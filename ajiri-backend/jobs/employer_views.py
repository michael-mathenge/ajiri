"""Owner drafts and staff review; no self-verification or paid application gate."""

from django.db import transaction, OperationalError
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, APIException
from profiles.cv_validation import StrictSerializer
from .models import (
    EmployerOrganisation,
    EmployerJobDraft,
    EmployerReview,
    Job,
    JobPublication,
)
from .scam_filter import analyze_job_for_scam
from .utils import safe_http_url
from accounts.throttles import EndpointThrottle
from urllib.parse import urlsplit
import uuid


class OrganisationSerializer(serializers.ModelSerializer):
    def validate_website(self, value):
        if not safe_http_url(value):
            raise serializers.ValidationError('Use an HTTP or HTTPS official website without embedded credentials.')
        return value
    class Meta:
        model = EmployerOrganisation
        fields = ("id", "name", "website", "status", "reviewed_at")
        read_only_fields = ("id", "status", "reviewed_at")


class DraftSerializer(serializers.ModelSerializer):
    def validate_application_url(self, value):
        if not safe_http_url(value):
            raise serializers.ValidationError('Use an HTTP or HTTPS application URL without embedded credentials.')
        return value
    class Meta:
        model = EmployerJobDraft
        fields = (
            "id",
            "organisation",
            "title",
            "description",
            "requirements",
            "location",
            "job_type",
            "application_url",
            "closes_at",
            "status",
            "revision",
            "job",
            "created_at",
        )
        read_only_fields = ("id", "status", "revision", "job", "created_at")

    def validate_organisation(self, value):
        if value.owner_id != self.context["request"].user.pk:
            raise serializers.ValidationError("Choose your own organisation.")
        return value

    def validate_closes_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Choose a future closing date and time.")
        return value

    def validate_description(self, value):
        if len(value) > 12000:
            raise serializers.ValidationError("Use at most 12,000 characters.")
        return value

    def validate_requirements(self, value):
        if len(value) > 6000:
            raise serializers.ValidationError("Use at most 6,000 characters.")
        return value


class PublicationRulesEnabled(permissions.BasePermission):
    message = 'New employer submissions and reviews are temporarily unavailable.'

    def has_permission(self, request, view):
        return settings.JOB_FRESHNESS_ENFORCED and (
            request.method in permissions.SAFE_METHODS
            or getattr(view, 'allow_when_posting_disabled', False)
            or settings.EMPLOYER_POSTING_ENABLED)


class VerifiedEmployer(permissions.BasePermission):
    message = "Verify your current account email before posting a job."

    def has_permission(self, request, view):
        if not request.user.is_authenticated or not request.user.is_active:
            return False
        profile = request.user.profile
        return bool(
            profile.email_verified_at
            and profile.verified_email.casefold() == request.user.email.casefold()
        )


class EmployerUnavailable(APIException):
    status_code = 503
    default_detail = 'Employer records are temporarily unavailable. Reload review status before retrying.'


class PrivateEmployerMixin:
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'employer_mutation'

    def get_throttles(self):
        return [] if self.request.method in permissions.SAFE_METHODS else super().get_throttles()

    def handle_exception(self, exception):
        if isinstance(exception, OperationalError):
            exception = EmployerUnavailable()
        return super().handle_exception(exception)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        return response


class OrganisationList(PrivateEmployerMixin, generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated, PublicationRulesEnabled, VerifiedEmployer)
    serializer_class = OrganisationSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return EmployerOrganisation.objects.none()
        return EmployerOrganisation.objects.filter(owner=self.request.user).order_by(
            "-pk"
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DraftList(PrivateEmployerMixin, generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated, PublicationRulesEnabled, VerifiedEmployer)
    serializer_class = DraftSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return EmployerJobDraft.objects.none()
        return EmployerJobDraft.objects.filter(
            organisation__owner=self.request.user
        ).order_by("-pk")


class ReviewQueue(PrivateEmployerMixin, APIView):
    permission_classes = (permissions.IsAdminUser, PublicationRulesEnabled)

    def get(self, request):
        # Bounded queue; the operator must review each item, never bulk-publish.
        return Response(
            {
                "organisations": OrganisationSerializer(
                    EmployerOrganisation.objects.filter(status="pending").order_by(
                        "pk"
                    )[:50],
                    many=True,
                ).data,
                "drafts": DraftSerializer(
                    EmployerJobDraft.objects.filter(status="pending").order_by("pk")[
                        :50
                    ],
                    many=True,
                ).data,
            }
        )


class DraftWithdraw(PrivateEmployerMixin, APIView):
    permission_classes = (permissions.IsAuthenticated, PublicationRulesEnabled)
    allow_when_posting_disabled = True

    def post(self, request, pk):
        with transaction.atomic():
            draft = generics.get_object_or_404(
                EmployerJobDraft, pk=pk, organisation__owner=request.user
            )
            if draft.status == "withdrawn":
                return Response({"status": "withdrawn"})
            EmployerJobDraft.objects.filter(pk=pk).update(status="withdrawn")
            if draft.job_id:
                JobPublication.objects.filter(job_id=draft.job_id).update(
                    status="archived",
                    archive_reason="employer_withdrew",
                    archived_at=timezone.now(),
                )
                Job.objects.filter(pk=draft.job_id).update(is_active=False)
        return Response({"status": "withdrawn"})


class ReviewInput(StrictSerializer):
    approve = serializers.BooleanField()
    reason = serializers.CharField(max_length=2000, allow_blank=False)
    revision = serializers.IntegerField(min_value=1, required=False)


class OrganisationReview(PrivateEmployerMixin, APIView):
    permission_classes = (permissions.IsAdminUser, PublicationRulesEnabled)

    def post(self, request, pk):
        form = ReviewInput(data=request.data)
        form.is_valid(raise_exception=True)
        organisation = generics.get_object_or_404(EmployerOrganisation, pk=pk)
        if organisation.owner_id == request.user.pk:
            raise ValidationError("An employer cannot review its own organisation.")
        with transaction.atomic():
            changed = EmployerOrganisation.objects.filter(
                pk=pk, status="pending"
            ).update(
                status="approved" if form.validated_data["approve"] else "rejected",
                reviewed_by=request.user,
                reviewed_at=timezone.now(),
                review_reason=form.validated_data["reason"],
            )
            if not changed:
                return Response(
                    {"detail": "This organisation has already been reviewed."},
                    status=409,
                )
        return Response({"status": "reviewed"})


class DraftReview(PrivateEmployerMixin, APIView):
    permission_classes = (permissions.IsAdminUser, PublicationRulesEnabled)

    def post(self, request, pk):
        form = ReviewInput(data=request.data)
        form.is_valid(raise_exception=True)
        with transaction.atomic():
            draft = generics.get_object_or_404(
                EmployerJobDraft.objects.select_related("organisation"), pk=pk
            )
            organisation = draft.organisation
            if organisation.owner_id == request.user.pk:
                raise ValidationError("An employer cannot review its own listing.")
            approve = form.validated_data["approve"]
            if (
                form.validated_data.get("revision") != draft.revision
                or approve
                and (
                    organisation.status != "approved"
                    or not organisation.owner.is_active
                    or not organisation.owner.profile.email_verified_at
                    or organisation.owner.profile.verified_email.casefold()
                    != organisation.owner.email.casefold()
                    or draft.closes_at <= timezone.now()
                )
            ):
                raise ValidationError(
                    "Check organisation review, closing date and current revision."
                )
            changed = EmployerJobDraft.objects.filter(
                pk=pk, status="pending", revision=draft.revision
            ).update(status="published" if approve else "rejected")
            if not changed:
                return Response(
                    {"detail": "The listing changed or has already been reviewed."},
                    status=409,
                )
            if approve:
                base = settings.PUBLIC_JOB_ORIGIN.rstrip('/')
                parsed = urlsplit(base)
                if (not safe_http_url(base) or parsed.scheme != 'https' or parsed.path
                    or parsed.query or parsed.fragment or len(base) > 150):
                    raise ValidationError('Configure the fixed HTTPS job origin before publishing.')
                job = Job(
                    title=draft.title,
                    company_name=organisation.name,
                    description=draft.description,
                    requirements=draft.requirements,
                    location=draft.location,
                    job_type=draft.job_type,
                    source_name="Employer submission",
                    source_url=f"{base}/jobs/pending-{uuid.uuid4().hex}",
                    external_application_url=draft.application_url,
                    application_method="external_link",
                    posted_at=timezone.now(),
                )
                flagged, reasons = analyze_job_for_scam(job)
                if flagged:
                    raise ValidationError(
                        {
                            "detail": "The listing needs further scam review.",
                            "reasons": reasons,
                        }
                    )
                job.save()
                # Several real vacancies can share one employer application portal.
                # Give each reviewed listing its own stable Ajiri identity.
                job.source_url = f'{base}/jobs/{job.pk}'
                job.save(update_fields=['source_url'])
                JobPublication.objects.create(
                    job=job,
                    origin="employer",
                    status="published",
                    closes_at=draft.closes_at,
                    organisation=organisation,
                    confirmed_at=timezone.now(),
                    evidence_url=organisation.website,
                )
                EmployerJobDraft.objects.filter(pk=pk).update(job=job)
            EmployerReview.objects.create(
                draft=draft,
                actor=request.user,
                revision=draft.revision,
                decision="approved" if approve else "rejected",
                reason=form.validated_data["reason"],
            )
        return Response({"status": "published" if approve else "rejected"})
