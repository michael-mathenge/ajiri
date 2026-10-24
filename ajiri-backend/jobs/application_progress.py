"""Private user reports, independent of immutable documents and delivery evidence."""
from django.db import transaction, OperationalError
from django.db.models import F
from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from accounts.throttles import EndpointThrottle
from profiles.cv_validation import StrictSerializer
from .models import Application
from .serializers import ApplicationSerializer


class ProgressInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0, max_value=2147483646)
    stage = serializers.ChoiceField(choices=Application.Progress.choices)
    note = serializers.CharField(max_length=1000, allow_blank=True, required=False, default='')

    def validate(self, data):
        if data['stage'] == Application.Progress.NOT_REPORTED and data['note']:
            raise serializers.ValidationError({'note': ['Choose a reported stage or clear the note.']})
        return data


class ProgressConflict(APIException):
    status_code = 409
    default_detail = 'Your application update changed. Reload before saving again.'


class ProgressBusy(APIException):
    status_code = 503
    default_detail = 'Application updates are busy. Reload the current state before trying again.'


class ApplicationProgressView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'apply'
    serializer_class = ApplicationSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        return response

    def patch(self, request, pk):
        form = ProgressInput(data=request.data)
        form.is_valid(raise_exception=True)
        values = form.validated_data
        try:
            with transaction.atomic():
                changed = Application.objects.filter(pk=pk, user=request.user,
                    progress_revision=values['expected_revision']).update(
                        progress_revision=F('progress_revision')+1, progress_stage=values['stage'],
                        progress_note=values['note'], progress_reported_at=timezone.now())
                app = generics.get_object_or_404(Application.objects.select_related('job'), pk=pk, user=request.user)
                if not changed:
                    raise ProgressConflict()
        except OperationalError:
            raise ProgressBusy() from None
        response = Response(ApplicationSerializer(app, context={'request': request}).data)
        response['Cache-Control'] = 'private, no-store'
        return response
