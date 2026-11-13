"""Private references never widen vacancy eligibility or create applications."""
from django.db import transaction, OperationalError
from django.db.models import F
from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from accounts.throttles import EndpointThrottle
from profiles.cv_validation import StrictSerializer
from .feed_display import browse_jobs
from .models import Job, SavedJob
from .serializers import JobListSerializer
from .utils import safe_http_url


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobListSerializer(read_only=True)
    reference_url = serializers.SerializerMethodField()

    def get_reference_url(self, obj) -> str | None:
        return safe_http_url(obj.job.source_url)

    class Meta:
        model = SavedJob
        fields = ('job', 'saved_at', 'reference_url')


class SavedStateSerializer(serializers.Serializer):
    job_id = serializers.IntegerField(read_only=True)
    saved = serializers.BooleanField(read_only=True)
    saved_at = serializers.DateTimeField(read_only=True, allow_null=True)


class SavedJobBusy(APIException):
    status_code = 503
    default_detail = 'Saved jobs are busy. Refresh your saved status before trying again.'


class PrivateSavedJobMixin:
    permission_classes = (permissions.IsAuthenticated,)

    def get_throttles(self):
        self.throttle_scope = 'saved_search_mutation'
        return [] if self.request.method in permissions.SAFE_METHODS else [EndpointThrottle()]

    def handle_exception(self, exc):
        return super().handle_exception(SavedJobBusy() if isinstance(exc, OperationalError) else exc)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        return response


class SavedJobList(PrivateSavedJobMixin, generics.ListAPIView):
    serializer_class = SavedJobSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SavedJob.objects.none()
        return SavedJob.objects.filter(owner=self.request.user).select_related('job__publication').order_by('-saved_at', '-pk')


class SavedJobState(PrivateSavedJobMixin, generics.GenericAPIView):
    # see docs/CONCEPTS.md#private-shortlist-and-follow-up
    serializer_class = SavedStateSerializer

    def visible_job(self, pk):
        return generics.get_object_or_404(browse_jobs(Job.objects.filter(is_active=True, is_flagged_scam=False)), pk=pk)

    def output(self, pk, row):
        return Response(self.get_serializer({'job_id': pk, 'saved': row is not None,
            'saved_at': row.saved_at if row else None}).data)

    def get(self, request, pk):
        row = SavedJob.objects.filter(owner=request.user, job_id=pk).first()
        if row is None:
            self.visible_job(pk)
        return self.output(pk, row)

    def put(self, request, pk):
        StrictSerializer(data=request.data).is_valid(raise_exception=True)
        with transaction.atomic():
            # Claim the writer slot; a repeated PUT retains one row and its original date.
            SavedJob.objects.filter(owner=request.user, job_id=pk).update(saved_at=F('saved_at'))
            row = SavedJob.objects.filter(owner=request.user, job_id=pk).first()
            if row is None:
                job = self.visible_job(pk)
                row, _ = SavedJob.objects.get_or_create(owner=request.user, job=job)
        return self.output(pk, row)

    def delete(self, request, pk):
        SavedJob.objects.filter(owner=request.user, job_id=pk).delete()
        return Response(status=204)
