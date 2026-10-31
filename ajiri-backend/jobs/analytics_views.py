from django.http import Http404
from django.conf import settings
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.response import Response
from profiles.cv_validation import StrictBoolean, StrictSerializer
from profiles.cv_views import PrivateCVView
from accounts.throttles import EndpointThrottle
from .analytics import EVENTS, available, choose, current_choice, record


class AnalyticsChoiceInput(StrictSerializer):
    decision_id = serializers.UUIDField()
    enabled = StrictBoolean()
    policy_version = serializers.RegexField(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$', required=False, allow_blank=True, default='')


class AnalyticsEventInput(StrictSerializer):
    event = serializers.ChoiceField(choices=EVENTS)


class AnalyticsChoiceView(PrivateCVView):
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'analytics_choice'

    def get(self, request):
        choice = current_choice(request.user)
        return Response({'available': available(), 'policy_version': settings.ANALYTICS_POLICY_VERSION,
            'enabled': bool(available() and choice and choice.enabled
                and choice.policy_version == settings.ANALYTICS_POLICY_VERSION)})

    def post(self, request):
        serializer = AnalyticsChoiceInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            choose(request.user, **serializer.validated_data)
        except (ValueError, IntegrityError):
            raise serializers.ValidationError('The analytics choice is unavailable or changed. Reload its current policy.') from None
        return self.get(request)


class AnalyticsEventView(PrivateCVView):
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'analytics'

    def post(self, request):
        if not available():
            raise Http404
        serializer = AnalyticsEventInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        record(request.user, serializer.validated_data['event'])
        return Response(status=204)  # Never echo account data or private request attributes.
