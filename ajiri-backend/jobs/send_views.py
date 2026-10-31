"""Owner-scoped exact authorization and default-off transport/queue gates."""
from django.db import IntegrityError
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response

from accounts.throttles import EndpointThrottle
from profiles.cv_validation import StrictSerializer, SchemaVersion, StrictBoolean
from profiles.cv_views import PrivateCVView
from .application_packages import PackageConflict
from .models import ApplicationSendAuthorization as Authorization
from .package_views import owner_application
from .send_authorization import (plan_response, authorize, authorization_data,
    owner_authorization, withdraw)


class RetryQuery(StrictSerializer):
    retry_of = serializers.UUIDField(required=False)


class AuthorizationInput(RetryQuery):
    request_key = serializers.UUIDField()
    package_id = serializers.UUIDField()
    expected_revision = SchemaVersion(min_value=1, max_value=2147483647)
    plan_sha256 = serializers.RegexField(r'\A[0-9a-f]{64}\Z')
    authorization = StrictBoolean()

    def validate_authorization(self, value):
        if value is not True:
            raise serializers.ValidationError('Explicit authorization of this exact application is required.')
        return value


class SendPlanView(PrivateCVView):
    def get(self, request, pk):
        app = owner_application(request, pk)
        query = RetryQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(plan_response(request.user, app, query.validated_data.get('retry_of')))


class SendAuthorizationListView(PrivateCVView):
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'apply'

    def get(self, request, pk):
        owner_application(request, pk)
        class Lookup(StrictSerializer):
            request_key = serializers.UUIDField(required=False)
        query = Lookup(data=request.query_params)
        query.is_valid(raise_exception=True)
        rows = Authorization.objects.filter(application_id=pk, owner=request.user).order_by('-authorized_at')
        if 'request_key' in query.validated_data:
            return Response(authorization_data(get_object_or_404(rows, **query.validated_data)))
        return Response({'results': [authorization_data(row) for row in rows[:20]]})

    def post(self, request, pk):
        owner_application(request, pk)
        serializer = AuthorizationInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            authorization, created = authorize(request.user, pk, serializer.validated_data)
        except IntegrityError:
            raise PackageConflict('A conflicting authorization exists. Reconcile before another action.') from None
        return Response(authorization_data(authorization), status=201 if created else 200)


class SendAuthorizationView(PrivateCVView):
    def get(self, request, pk, authorization_id):
        return Response(authorization_data(owner_authorization(request.user, pk, authorization_id)))


class WithdrawAuthorizationView(PrivateCVView):
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'apply'

    def post(self, request, pk, authorization_id):
        owner_authorization(request.user, pk, authorization_id)
        StrictSerializer(data=request.data).is_valid(raise_exception=True)
        return Response(authorization_data(withdraw(request.user, pk, authorization_id)))


class DispatchAuthorizationView(PrivateCVView):
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'apply'

    def post(self, request, pk, authorization_id):
        authorization = owner_authorization(request.user, pk, authorization_id)
        StrictSerializer(data=request.data).is_valid(raise_exception=True)
        data = authorization_data(authorization)
        if data['attempt'] is not None:
            return Response(data)  # Receipt remains readable even after file/mailbox edits.
        if not data['dispatch_enabled']:
            return Response({'detail': data['disabled_reason'], 'code': 'application_sending_disabled'}, status=409)
        if getattr(settings, 'DELIVERY_QUEUE_ENABLED', False):
            from .delivery_queue import enqueue
            from .queue_views import task_data
            task = enqueue('application', authorization.pk, owner=request.user)
            return Response({**data, 'queue': task_data(task)}, status=202)
        from .application_dispatch import dispatch
        from .delivery_service import DeliveryError
        try:
            dispatch(request.user, authorization)
        except DeliveryError:
            return Response({'detail': 'Sending could not be confirmed. Check the authorization receipt before any further action.',
                             'code': 'application_dispatch_unavailable'}, status=409)
        authorization.refresh_from_db()
        return Response(authorization_data(authorization))
