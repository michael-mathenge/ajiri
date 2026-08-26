from rest_framework import serializers
from .models import Job, Application
from .matching import calculate_match_score
from profiles.serializers import SkillSerializer


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the browse/search results list."""
    match_score = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id', 'title', 'company_name', 'location', 'job_type',
            'salary_min', 'salary_max', 'is_salary_negotiable',
            'match_score', 'posted_at',
        )

    def get_match_score(self, job):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            return calculate_match_score(request.user.profile, job)
        return None


class JobDetailSerializer(serializers.ModelSerializer):
    """Full serializer for a single job's detail page."""
    skills_required = SkillSerializer(many=True, read_only=True)
    match_score = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id', 'title', 'company_name', 'description', 'requirements',
            'location', 'job_type', 'salary_min', 'salary_max',
            'is_salary_negotiable', 'skills_required', 'match_score',
            'source_url', 'source_name', 'posted_at',
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

    class Meta:
        model = Application
        fields = (
            'id', 'job', 'job_title', 'company_name', 'status',
            'application_method', 'application_email',
            'generated_cv', 'generated_cover_letter',
            'email_subject', 'email_body',
            'created_at', 'updated_at', 'sent_at',
        )
        read_only_fields = (
            'id', 'job', 'job_title', 'company_name', 'status',
            'application_method', 'application_email',
            'generated_cv', 'generated_cover_letter',
            'created_at', 'updated_at', 'sent_at',
        )