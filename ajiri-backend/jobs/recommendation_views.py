"""Private reversible suggestion choices; browsing, applications and alerts stay independent."""
from django.db import transaction, OperationalError
from django.conf import settings
from django.db.models import Count, Q, F, Value, FloatField, IntegerField, Case, When, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from accounts.throttles import EndpointThrottle
from profiles.cv_validation import StrictSerializer, StrictBoolean
from .freshness import eligible_jobs
from .filters import JobFilter
from .models import Job, RecommendationChoice
from .serializers import JobListSerializer


def current_suggestions():
    return eligible_jobs() if settings.JOB_FRESHNESS_ENFORCED else Job.objects.none()


class SuggestionSerializer(JobListSerializer):
    choice_revision = serializers.IntegerField(read_only=True)

    class Meta(JobListSerializer.Meta):
        fields = JobListSerializer.Meta.fields + ('choice_revision',)

    def get_match_score(self, job):
        # Same skill arithmetic as calculate_match_score; SQL counts avoid per-row skill queries.
        return round(job._matched_count / job._required_count * 100) if job._required_count else 0


class ChoiceSerializer(serializers.ModelSerializer):
    job = JobListSerializer(read_only=True)
    dismissed = serializers.BooleanField(read_only=True)

    class Meta:
        model = RecommendationChoice
        fields = ('job', 'revision', 'dismissed')


class ChoiceInput(StrictSerializer):
    dismissed = StrictBoolean()
    expected_revision = serializers.IntegerField(min_value=0, max_value=2147483646)


class ChoiceConflict(APIException):
    status_code = 409
    default_detail = 'Your suggestion choice changed. Refresh suggestions before trying again.'


class ChoiceBusy(APIException):
    status_code = 503
    default_detail = 'Suggestion choices are busy. Refresh suggestions before trying again.'


class PrivateChoiceMixin:
    permission_classes = (permissions.IsAuthenticated,)

    def get_throttles(self):
        # Share the existing owner-preference mutation budget; reads remain unthrottled.
        self.throttle_scope = 'saved_search_mutation'
        return [] if self.request.method in permissions.SAFE_METHODS else [EndpointThrottle()]

    def handle_exception(self, exc):
        return super().handle_exception(ChoiceBusy() if isinstance(exc, OperationalError) else exc)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        return response


class SuggestionList(PrivateChoiceMixin, generics.ListAPIView):
    # see docs/CONCEPTS.md#owner-recommendation-choices
    serializer_class = SuggestionSerializer
    filterset_class = JobFilter

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Job.objects.none()
        owner = self.request.user
        choices = RecommendationChoice.objects.filter(owner=owner)
        skill_ids = owner.profile.skills.values('pk')
        return current_suggestions().exclude(pk__in=choices.filter(dismissed_at__isnull=False).values('job_id')).annotate(
            _required_count=Count('skills_required', distinct=True),
            _matched_count=Count('skills_required', filter=Q(skills_required__in=skill_ids), distinct=True),
            choice_revision=Coalesce(Subquery(choices.filter(job_id=OuterRef('pk')).values('revision')[:1]), Value(0), output_field=IntegerField()),
        ).annotate(_suggestion_score=Case(When(_required_count=0, then=Value(0.0)),
            default=100.0 * F('_matched_count') / F('_required_count'), output_field=FloatField()),
        ).select_related('publication').order_by('-_suggestion_score', '-posted_at', '-pk')


class DismissedSuggestionList(PrivateChoiceMixin, generics.ListAPIView):
    serializer_class = ChoiceSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return RecommendationChoice.objects.none()
        return RecommendationChoice.objects.filter(owner=self.request.user,
            dismissed_at__isnull=False).select_related('job__publication').order_by('-dismissed_at', '-pk')


class RecommendationChoiceDetail(PrivateChoiceMixin, generics.GenericAPIView):
    serializer_class = ChoiceSerializer

    def choice(self, pk):
        current = RecommendationChoice.objects.select_related('job__publication').filter(owner=self.request.user, job_id=pk).first()
        if current is not None:
            return current
        job = generics.get_object_or_404(current_suggestions().select_related('publication'), pk=pk)
        return RecommendationChoice(owner=self.request.user, job=job)

    def get(self, request, pk):
        return Response(self.get_serializer(self.choice(pk)).data)

    def patch(self, request, pk):
        form = ChoiceInput(data=request.data)
        form.is_valid(raise_exception=True)
        with transaction.atomic():
            # Claim SQLite's writer slot before deciding whether a first choice exists.
            RecommendationChoice.objects.filter(owner=request.user, job_id=pk).update(revision=F('revision'))
            choice = self.choice(pk)
            revision = form.validated_data['expected_revision']
            if choice.revision != revision:
                raise ChoiceConflict()
            if choice.pk is None:
                choice.save()
            updated = RecommendationChoice.objects.filter(pk=choice.pk, owner=request.user, revision=revision).update(
                dismissed_at=timezone.now() if form.validated_data['dismissed'] else None,
                revision=F('revision') + 1)
            if not updated:
                raise ChoiceConflict()
            choice.refresh_from_db()
        return Response(self.get_serializer(choice).data)
