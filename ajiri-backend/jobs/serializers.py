from rest_framework import serializers
from .models import Job, Application, Notification
from .matching import calculate_match_score, explain_skill_match
from profiles.serializers import SkillSerializer
from .utils import safe_http_url


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the browse/search results list."""
    match_score = serializers.SerializerMethodField()
    publication = serializers.SerializerMethodField()

    display_only = serializers.SerializerMethodField()
    display_notice = serializers.SerializerMethodField()
    can_apply = serializers.SerializerMethodField()
    original_source_url = serializers.URLField(source='source_url', read_only=True)

    def get_can_apply(self, job) -> bool:
        from .freshness import job_is_eligible
        cached = getattr(job, '_can_apply', None)
        return cached if cached is not None else job_is_eligible(job)

    def get_display_only(self, job) -> bool:
        return not self.get_can_apply(job)

    def get_display_notice(self, job) -> str:
        from .feed_display import NOTICE
        return NOTICE if self.get_display_only(job) else ''

    def get_publication(self, job) -> dict:
        from .models import JobPublication
        try:
            evidence = job.publication
        except JobPublication.DoesNotExist:
            return {'status': 'unverified', 'closes_at': None, 'confirmed_at': None, 'origin': 'unknown'}
        from datetime import timedelta
        from django.conf import settings
        until = evidence.closes_at or evidence.confirmed_until
        if evidence.origin == 'rss' and evidence.confirmed_at:
            freshness_end = evidence.confirmed_at + timedelta(seconds=settings.RSS_AVAILABILITY_MAX_AGE_SECONDS)
            until = min(until, freshness_end) if until else freshness_end
        # Original publisher identity comes from reviewed provenance, never a feed's label.
        # see docs/CONCEPTS.md#ajiri-original-vacancies
        return {'status': evidence.status, 'closes_at': evidence.closes_at, 'confirmed_until': evidence.confirmed_until,
                'publisher': 'Ajiri' if evidence.origin == 'employer' else None,
                'listing_url': safe_http_url(job.source_url) if evidence.origin == 'employer' else None,
                'confirmed_at': evidence.confirmed_at, 'origin': evidence.origin, 'available_until': until}

    class Meta:
        model = Job
        fields = (
            'id', 'title', 'company_name', 'location', 'job_type',
            'county', 'work_arrangement', 'min_experience_years',
            'salary_min', 'salary_max', 'is_salary_negotiable',
            'match_score', 'posted_at', 'publication', 'display_only', 'display_notice', 'can_apply', 'original_source_url', 'source_name',
        )

    def get_match_score(self, job):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            return calculate_match_score(request.user.profile, job)
        return None


class JobDetailSerializer(JobListSerializer):
    """Full serializer for a single job's detail page."""
    skills_required = SkillSerializer(many=True, read_only=True)
    source_url = serializers.URLField(source='application_target', read_only=True)
    match_score = serializers.SerializerMethodField()
    match_explanation = serializers.SerializerMethodField()

    def get_match_explanation(self, job) -> dict:
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            return explain_skill_match(request.user.profile, job)
        return None

    class Meta:
        model = Job
        fields = (
            'id', 'title', 'company_name', 'description', 'requirements',
            'location', 'job_type', 'salary_min', 'salary_max',
            'county', 'work_arrangement', 'min_experience_years',
            'is_salary_negotiable', 'skills_required', 'match_score', 'match_explanation',
            'source_url', 'source_name', 'posted_at', 'publication', 'display_only', 'display_notice', 'can_apply', 'original_source_url',
        )

    def get_match_score(self, job):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            return calculate_match_score(request.user.profile, job)
        return None


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Represents an Application draft for the frontend's review screen.
    email_subject/email_body are left editable (not read-only) since a
    future PATCH endpoint will let the user tweak them before sending —
    this endpoint only ever sets their initial auto-generated values.
    """
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company_name', read_only=True)
    employer_url = serializers.URLField(source='job.application_target', read_only=True)
    delivery_evidence = serializers.SerializerMethodField()

    def get_delivery_evidence(self, obj) -> dict:
        attempts = getattr(obj, '_pipeline_attempts', None)
        if attempts is None:
            attempts = list(obj.delivery_attempts.filter(channel='application', user_id=obj.user_id)
                            .order_by('-created_at', '-pk')[:1])
        if attempts:
            attempt = attempts[0]
            labels = {'accepted': 'Email provider accepted; inbox delivery unconfirmed',
                      'reserved': 'Email outcome uncertain; reconciliation required',
                      'unknown': 'Email outcome uncertain; reconciliation required',
                      'definite_failure': 'Latest email attempt failed'}
            return {'kind': attempt.state, 'label': labels[attempt.state],
                    'recorded_at': attempt.created_at.isoformat()}
        if obj.status == 'sent':
            label = ('External submission reported by you' if obj.application_method == 'external_link'
                     else 'Historical email record; provider evidence unavailable')
            return {'kind': 'user_report' if obj.application_method == 'external_link' else 'unverified_record',
                    'label': label, 'recorded_at': obj.sent_at.isoformat() if obj.sent_at else None}
        return {'kind': obj.status, 'label': obj.get_status_display(), 'recorded_at': None}

    class Meta:
        model = Application
        fields = (
            'id', 'job', 'job_title', 'company_name', 'status', 'employer_url',
            'application_method', 'application_email',
            'generated_cv', 'generated_cover_letter',
            'email_subject', 'email_body',
            'created_at', 'updated_at', 'sent_at',
            'progress_stage', 'progress_note', 'progress_revision', 'progress_reported_at', 'delivery_evidence',
            'follow_up_at',
        )
        read_only_fields = (
            'id', 'job', 'job_title', 'company_name', 'status',
            'application_method', 'application_email',
            'generated_cv', 'generated_cover_letter',
            'created_at', 'updated_at', 'sent_at',
            'progress_stage', 'progress_note', 'progress_revision', 'progress_reported_at', 'delivery_evidence',
            'follow_up_at',
        )


class NotificationSerializer(serializers.ModelSerializer):
    """
    Represents one job-match alert for the frontend's Notifications page.
    job_id is exposed separately from the nested job fields so the
    frontend can link straight to /jobs/<job_id>/ without a second lookup.
    """
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company_name', read_only=True)
    job_id = serializers.IntegerField(source='job.id', read_only=True)

    class Meta:
        model = Notification
        fields = (
            'id', 'job_id', 'job_title', 'company_name',
            'match_score', 'is_read', 'sent_email', 'created_at',
        )
        read_only_fields = (
            'id', 'job_id', 'job_title', 'company_name',
            'match_score', 'sent_email', 'created_at',
        )
