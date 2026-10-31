import json
from django.conf import settings
from django.utils import timezone
from django.http import Http404
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.throttles import EndpointThrottle
from profiles.cv_validation import StrictSerializer
from profiles.cv_views import PrivateCVView
from .daraja import PaymentBlocked, valid_reference
from .models import PaymentCheckout
from .payments import start_checkout


class CheckoutInput(StrictSerializer):
    decision_id = serializers.UUIDField()
    offer_id = serializers.UUIDField()
    terms_version = serializers.RegexField(r'\A[A-Za-z0-9._-]{1,64}\Z')
    phone = serializers.RegexField(r'\A254[17][0-9]{8}\Z', write_only=True)


def checkout_data(row):
    return {'id': str(row.id), 'offer_id': str(row.offer_id), 'amount_kes': row.amount_kes,
        'currency': 'KES', 'state': row.state, 'terms_version': row.terms_version,
        'settlement_verified': row.state == 'settled'}


class CheckoutCreateView(PrivateCVView):
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'payment'

    def post(self, request):
        if not settings.PAYMENTS_ENABLED:
            raise Http404
        serializer = CheckoutInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            row = start_checkout(request.user, **serializer.validated_data)
        except (PaymentBlocked, IntegrityError):
            return Response({'detail': 'Checkout unavailable. Review the offer or reconcile the original checkout.'}, status=409)
        return Response(checkout_data(row), status=202)


class CheckoutDetailView(PrivateCVView):
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'payment'

    def get(self, request, checkout_id):
        # Existing financial status remains readable while initiation is disabled.
        row = PaymentCheckout.objects.filter(pk=checkout_id, owner=request.user).first()
        if not row:
            raise Http404
        return Response(checkout_data(row))


class DarajaCallbackView(APIView):
    authentication_classes = ()
    permission_classes = ()
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'payment_callback'

    def post(self, request):
        if not settings.DARAJA_SANDBOX_ENABLED:
            raise Http404
        try:
            raw = request.stream.read(8193)
            if len(raw) > 8192:
                raise ValueError
            callback = json.loads(raw)['Body']['stkCallback']
            reference, merchant = callback['CheckoutRequestID'], callback['MerchantRequestID']
            if not valid_reference(reference) or not valid_reference(merchant):
                raise ValueError
        except (ValueError, KeyError, TypeError, AttributeError, RecursionError):
            return Response({'detail': 'Invalid bounded callback.'}, status=400)
        # Unauthenticated hint only: no raw payload, status authority, work enqueue,
        # query, settlement or capability. A forged/replayed hint cannot charge/grant.
        PaymentCheckout.objects.filter(provider_reference=reference, merchant_reference=merchant,
            callback_seen_at__isnull=True).update(callback_seen_at=timezone.now())
        return Response({'ResultCode': 0, 'ResultDesc': 'Received'})
