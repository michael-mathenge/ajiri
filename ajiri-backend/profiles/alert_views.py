from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.throttles import EndpointThrottle
from . import alert_consent


class ChoiceSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    decision_id = serializers.UUIDField()
    policy_version = serializers.ChoiceField(choices=[alert_consent.POLICY])


def preference_response(user):
    profile = user.profile
    profile.refresh_from_db()
    event = profile.alert_consent_events.order_by('-pk').first()
    confirmed = bool(event and event.enabled and event.policy_version == alert_consent.POLICY
                     and event.recipient_digest == alert_consent.recipient_digest(user.email))
    response = Response({'enabled': profile.notify_email,
        'confirmed': confirmed, 'eligible': alert_consent.eligible(profile),
        'policy_version': alert_consent.POLICY})
    response['Cache-Control'] = 'no-store, private'
    return response


class AlertPreferenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [EndpointThrottle]
    throttle_scope = 'alert_preference'

    def get(self, request):
        return preference_response(request.user)

    def post(self, request):
        serializer = ChoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            alert_consent.record_choice(request.user, serializer.validated_data['enabled'],
                                        serializer.validated_data['decision_id'])
        except ValueError:
            return Response({'detail': 'Decision key conflict. Reload before choosing again.'}, status=409)
        return preference_response(request.user)


class UnsubscribeView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [EndpointThrottle]
    throttle_scope = 'alert_unsubscribe'

    def post(self, request):
        token, confirm = request.data.get('token'), request.data.get('confirm', False)
        if not isinstance(token, str) or len(token) > 2048 or type(confirm) is not bool:
            return Response({'detail': 'Invalid unsubscribe request.'}, status=400)
        try:
            alert_consent.unsubscribe(token, confirm=confirm)
        except ValueError:
            return Response({'detail': 'Invalid or expired unsubscribe link.'}, status=400)
        response = Response({'can_unsubscribe': True, 'unsubscribed': confirm})
        response['Cache-Control'] = 'no-store, private'
        return response
