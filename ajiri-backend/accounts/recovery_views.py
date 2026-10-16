from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.cache import patch_cache_control
from django.utils.crypto import constant_time_compare
from django.utils.http import urlsafe_base64_decode
from rest_framework import permissions, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from profiles.models import Profile
from .csrf import CookieCSRFViewMixin
from .recovery import VERIFY_SALT, capture_enabled, capture_link, verification_state
from .throttles import EndpointThrottle, AccountTargetThrottle


class EmailInput(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class ResetInput(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=256)
    password = serializers.CharField(max_length=4096, trim_whitespace=False)
    password_confirm = serializers.CharField(max_length=4096, trim_whitespace=False)


class VerificationInput(serializers.Serializer):
    token = serializers.CharField(max_length=2048)


class AccountMutation(CookieCSRFViewMixin, APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'account_confirm'

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        patch_cache_control(response, private=True, no_store=True)
        return response


class PasswordResetRequest(AccountMutation):
    throttle_scope = 'account_email'
    throttle_classes = (EndpointThrottle, AccountTargetThrottle)

    def post(self, request):
        serializer = EmailInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Same status/body for unknown, inactive, unusable-password and known accounts.
        # No token generation or lookup is needed while delivery is disabled.
        if capture_enabled():
            user = get_user_model().objects.filter(email__iexact=serializer.validated_data['email'], is_active=True).first()
            if user and user.has_usable_password():
                capture_link(user, 'password_reset')
        return Response({'detail': 'If an eligible account exists, a reset link can be requested when email delivery is available.',
                         'delivery_available': capture_enabled()}, status=202)


class PasswordResetConfirm(AccountMutation):
    def post(self, request):
        serializer = ResetInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            uid = int(urlsafe_base64_decode(data['uid']).decode())
            if uid < 1 or uid > 2**63 - 1:
                raise ValueError
        except (ValueError, UnicodeError, OverflowError):
            raise ValidationError({'token': ['Invalid or expired reset link.']})
        with transaction.atomic():
            # First write serializes SQLite before the token check; select_for_update
            # alone does not lock rows on SQLite. No user data changes in this claim.
            get_user_model().objects.filter(pk=uid, is_active=True).update(password=F('password'))
            user = get_user_model().objects.filter(pk=uid, is_active=True).first()
            profile = Profile.objects.filter(user_id=uid).first()
            if not user or not profile or not user.has_usable_password() or not default_token_generator.check_token(user, data['token']):
                raise ValidationError({'token': ['Invalid or expired reset link.']})
            errors = {}
            if data['password'] != data['password_confirm']:
                errors['password_confirm'] = ['Passwords must match.']
            try:
                password_validation.validate_password(data['password'], user)
            except DjangoValidationError as error:
                errors['password'] = error.messages
            if errors:
                raise ValidationError(errors)
            user.set_password(data['password'])
            user.save(update_fields=['password'])
            Profile.objects.filter(pk=profile.pk).update(password_reset_at=timezone.now())
            BlacklistedToken.objects.bulk_create([BlacklistedToken(token_id=pk)
                for pk in OutstandingToken.objects.filter(user=user).values_list('pk', flat=True)], ignore_conflicts=True)
            password_validation.password_changed(data['password'], user)
        response = Response({'detail': 'Password changed. Log in with your new password.'})
        response.delete_cookie('refresh_token')
        return response


class VerificationRequest(AccountMutation):
    authentication_classes = APIView.authentication_classes
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'account_email'
    throttle_classes = (EndpointThrottle, AccountTargetThrottle)

    def post(self, request):
        profile = Profile.objects.filter(user=request.user).first()
        if profile and not (profile.email_verified_at and profile.verified_email.casefold() == request.user.email.casefold()):
            capture_link(request.user, 'email_verification')
        return Response({'detail': 'A verification link can be requested when email delivery is available.',
                         'delivery_available': capture_enabled()}, status=202)


class VerificationConfirm(AccountMutation):
    def post(self, request):
        serializer = VerificationInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = signing.loads(serializer.validated_data['token'], salt=VERIFY_SALT, max_age=86400)
            uid = data['uid']
            if type(uid) is not int or not 0 < uid <= 2**63 - 1:
                raise ValueError
        except (signing.BadSignature, ValueError, TypeError, KeyError):
            raise ValidationError({'token': ['Invalid or expired verification link.']})
        with transaction.atomic():
            Profile.objects.filter(user_id=uid).update(verified_email=F('verified_email'))
            user = get_user_model().objects.filter(pk=uid, is_active=True).first()
            profile = Profile.objects.filter(user_id=uid).first()
            if not user or not profile or data.get('email') != user.email.casefold():
                raise ValidationError({'token': ['Invalid or expired verification link.']})
            if not (profile.email_verified_at and profile.verified_email.casefold() == user.email.casefold()):
                state = data.get('state')
                if not isinstance(state, str) or not constant_time_compare(state, verification_state(user, profile)):
                    raise ValidationError({'token': ['Invalid or expired verification link.']})
                Profile.objects.filter(pk=profile.pk).update(email_verified_at=timezone.now(), verified_email=user.email.casefold())
        return Response({'detail': 'Email verified.'})


class VerificationStatus(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'verification_status'

    def get(self, request):
        profile = Profile.objects.filter(user=request.user).first()
        response = Response({'verified': bool(profile and profile.email_verified_at
            and profile.verified_email.casefold() == request.user.email.casefold()), 'delivery_available': capture_enabled()})
        patch_cache_control(response, private=True, no_store=True)
        return response
