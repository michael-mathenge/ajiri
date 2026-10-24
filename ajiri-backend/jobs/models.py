import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from profiles.models import Skill


class EmployerOrganisation(models.Model):
    """Staff review is evidence, never a guarantee of employer conduct."""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='employer_organisations')
    name = models.CharField(max_length=255)
    website = models.URLField()
    status = models.CharField(max_length=20, default='pending', choices=[('pending', 'Pending review'), ('approved', 'Reviewed'), ('rejected', 'Rejected')])
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Job(models.Model):
    """
    A listing ingested from a source or published after independent employer review.
    Publication evidence, not the presence of this historical row, controls visibility.
    """

    class JobType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        CONTRACT = 'contract', 'Contract'
        INTERNSHIP = 'internship', 'Internship'

    class ApplicationMethod(models.TextChoices):
        EMAIL = 'email', 'Email'
        EXTERNAL_LINK = 'external_link', 'External Link'

    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)

    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    # When True, frontend shows "To be discussed during interview process"
    # instead of salary_min/max, regardless of whether they're filled in.
    is_salary_negotiable = models.BooleanField(default=False)

    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.FULL_TIME,
    )

    # Reuses the SAME Skill model from the profiles app (not a separate one).
    # This is what makes match-scoring possible later: a profile's skills
    # and a job's required skills point at the exact same underlying rows.
    skills_required = models.ManyToManyField(Skill, blank=True, related_name='jobs')

    source_url = models.URLField(unique=True)
    # A nullable added column avoids rebuilding SQLite's job table and losing FTS triggers.
    external_application_url = models.URLField(blank=True, null=True, default=None)
    source_name = models.CharField(max_length=100)

    posted_at = models.DateTimeField(null=True, blank=True)
    scraped_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_flagged_scam = models.BooleanField(default=False)
    scam_flags = models.TextField(blank=True, default='')

    # New fields for Auto-Apply phase — see docs/CONCEPTS.md#application-method-detection
    application_method = models.CharField(
        max_length=20,
        choices=ApplicationMethod.choices,
        default=ApplicationMethod.EXTERNAL_LINK,
    )
    application_email = models.EmailField(blank=True, default='')

    def __str__(self):
        return f"{self.title} at {self.company_name}"

    @property
    def application_target(self):
        return self.external_application_url or self.source_url


class JobModerationReview(models.Model):
    # see docs/CONCEPTS.md#reasoned-job-moderation
    job = models.ForeignKey(Job, on_delete=models.PROTECT, related_name='moderation_reviews')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    reviewed_fingerprint = models.CharField(max_length=64)
    decision = models.CharField(max_length=10, choices=[('clear', 'Clear flag'), ('uphold', 'Keep flag')])
    reason = models.TextField()
    before = models.JSONField()
    after = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['job', 'reviewed_fingerprint'], name='unique_job_moderation_evidence')]


class JobPublication(models.Model):
    # see docs/CONCEPTS.md#job-freshness-evidence
    job = models.OneToOneField(Job, on_delete=models.PROTECT, related_name='publication')
    origin = models.CharField(max_length=20, choices=[('rss', 'RSS'), ('employer', 'Employer')])
    status = models.CharField(max_length=20, default='unverified', choices=[('unverified', 'Unverified'), ('published', 'Published'), ('archived', 'Archived')])
    closes_at = models.DateTimeField(null=True, blank=True)
    confirmed_until = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    evidence_url = models.URLField(blank=True)
    archive_reason = models.CharField(max_length=100, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    organisation = models.ForeignKey(EmployerOrganisation, null=True, blank=True, on_delete=models.PROTECT)


class EmployerJobDraft(models.Model):
    organisation = models.ForeignKey(EmployerOrganisation, on_delete=models.PROTECT, related_name='job_drafts')
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    location = models.CharField(max_length=255)
    job_type = models.CharField(max_length=20, choices=Job.JobType.choices, default=Job.JobType.FULL_TIME)
    application_url = models.URLField()
    closes_at = models.DateTimeField()
    status = models.CharField(max_length=20, default='pending', choices=[('pending', 'Pending review'), ('published', 'Published'), ('rejected', 'Rejected'), ('withdrawn', 'Withdrawn')])
    revision = models.PositiveIntegerField(default=1)
    job = models.OneToOneField(Job, null=True, blank=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class EmployerReview(models.Model):
    draft = models.ForeignKey(EmployerJobDraft, on_delete=models.PROTECT, related_name='reviews')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    decision = models.CharField(max_length=20)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class SavedSearch(models.Model):
    # see docs/CONCEPTS.md#saved-search-windows
    class Frequency(models.TextChoices):
        OFF = 'off', 'Off'
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Every seven days'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=80)
    q = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    job_type = models.CharField(max_length=20, blank=True, choices=Job.JobType.choices)
    in_app_frequency = models.CharField(max_length=8, choices=Frequency.choices, default=Frequency.OFF)
    email_frequency = models.CharField(max_length=8, choices=Frequency.choices, default=Frequency.OFF)
    revision = models.PositiveIntegerField(default=1)
    in_app_cursor = models.DateTimeField()
    email_cursor = models.DateTimeField()
    next_in_app_at = models.DateTimeField(null=True, blank=True)
    next_email_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SavedSearchMatch(models.Model):
    search = models.ForeignKey(SavedSearch, on_delete=models.CASCADE, related_name='matches')
    revision = models.PositiveIntegerField()
    job = models.ForeignKey(Job, on_delete=models.PROTECT)
    channel = models.CharField(max_length=8, choices=[('in_app', 'In app'), ('email', 'Email')])
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    notification = models.ForeignKey('Notification', on_delete=models.SET_NULL, null=True, blank=True)
    email_attempt = models.ForeignKey('DeliveryAttempt', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('search', 'revision', 'job', 'channel'), name='saved_search_unique_match')]


class Application(models.Model):
    """
    Tracks the lifecycle of one user applying to one job: DRAFT (auto-generated,
    nothing sent yet) -> READY_FOR_REVIEW (user notified) -> SENT (user reviewed,
    edited if needed, and hit send) or DISMISSED (user declined to apply).

    Unlike cv_generator.py/cover_letter_generator.py (which build a .docx fresh
    in memory on every request), the files here are generated ONCE when the
    draft is created and saved permanently. This matters because the user needs
    to review/edit the SAME document that eventually gets sent — regenerating
    it later could silently produce a different file than what they approved.
    See docs/CONCEPTS.md#application-lifecycle
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        READY_FOR_REVIEW = 'ready_for_review', 'Ready for Review'
        SENT = 'sent', 'Sent'
        DISMISSED = 'dismissed', 'Dismissed'

    class Progress(models.TextChoices):
        NOT_REPORTED = 'not_reported', 'No update reported'
        APPLIED = 'applied', 'Applied (your report)'
        INTERVIEW = 'interview', 'Interview (your report)'
        OFFER = 'offer', 'Offer (your report)'
        CLOSED = 'closed', 'Closed (your report)'

    # see docs/CONCEPTS.md#application-progress-evidence
    progress_stage = models.CharField(max_length=16, choices=Progress.choices, default=Progress.NOT_REPORTED)
    progress_note = models.CharField(max_length=1000, blank=True, default='')
    progress_revision = models.PositiveIntegerField(default=0)
    progress_reported_at = models.DateTimeField(null=True, blank=True, default=None)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # Snapshotted from job.application_method / job.application_email at
    # draft-creation time. Jobs can theoretically change or be deactivated
    # later — we don't want an in-progress Application silently changing
    # behavior underneath the user.
    application_method = models.CharField(
        max_length=20,
        choices=Job.ApplicationMethod.choices,
    )
    application_email = models.EmailField(blank=True, default='')

    generated_cv = models.FileField(upload_to='applications/cvs/')
    generated_cover_letter = models.FileField(upload_to='applications/cover_letters/')

    # Only meaningful for application_method='email' — the user can edit
    # these before sending. Left blank for external_link applications.
    email_subject = models.CharField(max_length=255, blank=True, default='')
    email_body = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # One application per user per job — the ingest-trigger and the
        # periodic sweep must never create duplicate drafts for the same pair.
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.email} -> {self.job.title} ({self.status})"


def application_package_document_path(instance, filename):
    # see docs/CONCEPTS.md#application-package-schema
    # Private UUID paths never disclose or trust the supplied filename.
    return f'application-packages/{uuid.uuid4().hex}.docx'


class ApplicationPackage(models.Model):
    """Dormant revision snapshot; owner/byte validation belongs to future APIs."""
    # see docs/CONCEPTS.md#application-package-schema
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='packages')
    revision = models.PositiveIntegerField()
    cv_approval = models.ForeignKey('profiles.CVApproval', on_delete=models.PROTECT, related_name='application_packages')
    job_snapshot = models.JSONField()
    letter_text = models.TextField()
    email_subject = models.CharField(max_length=255, blank=True, default='')
    email_body = models.TextField(blank=True, default='')
    cv_document = models.FileField(upload_to=application_package_document_path, max_length=100)
    letter_document = models.FileField(upload_to=application_package_document_path, max_length=100)
    cv_sha256 = models.CharField(max_length=64)
    letter_sha256 = models.CharField(max_length=64)
    content_sha256 = models.CharField(max_length=64)
    cv_size = models.PositiveIntegerField()
    letter_size = models.PositiveIntegerField()
    template_version = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('application', 'revision'), name='app_package_unique_revision'),
            models.CheckConstraint(condition=models.Q(revision__gte=1), name='app_package_revision_positive'),
            models.CheckConstraint(condition=models.Q(cv_size__gte=1), name='app_package_cv_size_positive'),
            models.CheckConstraint(condition=models.Q(letter_size__gte=1), name='app_package_letter_size_positive'),
        ]


class ApplicationPackageApproval(models.Model):
    """Document approval evidence only; never permission to send email."""
    # see docs/CONCEPTS.md#application-package-schema
    package = models.OneToOneField(ApplicationPackage, on_delete=models.CASCADE, related_name='approval')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                    related_name='application_package_approvals')
    approved_at = models.DateTimeField(auto_now_add=True)
    content_sha256 = models.CharField(max_length=64)
    policy_version = models.CharField(max_length=40)


class Notification(models.Model):
    """
    A record that a user was alerted about a job matching their profile at
    or above MATCH_ALERT_THRESHOLD (see jobs/matching.py). One row per
    (user, job) pair — unique_together stops the same match from alerting
    the user twice, since both the immediate ingest-time check and the
    periodic Celery Beat sweep can independently discover the same match.
    See docs/CONCEPTS.md#job-alerts
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='notifications',
    )

    # Snapshotted at notification-creation time — the score that triggered
    # this alert, even if skills/requirements change later.
    match_score = models.PositiveIntegerField()

    is_read = models.BooleanField(default=False)
    # Whether an email was actually sent for this notification — separate
    # from is_read, since email delivery and in-app "seen" are independent.
    sent_email = models.BooleanField(default=False)
    # Keep email-only delivery receipts out of the in-app inbox.
    # see docs/CONCEPTS.md#notification-delivery-channels
    in_app = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.email} matched with {self.job.title} ({self.match_score}%)"


# Schema only: existing senders do not read or write these tables yet.
# see docs/CONCEPTS.md#delivery-accounting-schema
class DeliveryAttempt(models.Model):
    class Channel(models.TextChoices):
        APPLICATION = 'application', 'Application'
        ALERT = 'alert', 'Alert'
        EMAIL_VERIFICATION = 'email_verification', 'Email verification'
        PASSWORD_RESET = 'password_reset', 'Password reset'

    class State(models.TextChoices):
        RESERVED = 'reserved', 'Reserved'
        ACCEPTED = 'accepted', 'Accepted by provider'
        DEFINITE_FAILURE = 'definite_failure', 'Definite failure'
        UNKNOWN = 'unknown', 'Unknown outcome'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='delivery_attempts')
    application = models.ForeignKey(Application, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='delivery_attempts')
    notification = models.ForeignKey(Notification, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='delivery_attempts')
    channel = models.CharField(max_length=24, choices=Channel.choices)
    state = models.CharField(max_length=24, choices=State.choices, default=State.RESERVED)
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    recipient_digest = models.CharField(max_length=64, validators=[
        RegexValidator(r'\A[0-9a-f]{64}\Z', 'A lowercase keyed SHA-256 digest is required.')])
    provider_message_id = models.CharField(max_length=255, blank=True, default='')
    failure_category = models.CharField(max_length=32, blank=True, default='', choices=[
        ('', 'None'), ('transport', 'Transport'), ('provider_rejected', 'Provider rejected'),
        ('timeout', 'Timeout'), ('configuration', 'Configuration')])
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True, default=None)

    def clean(self):
        super().clean()
        if not self._state.adding:
            return  # Retained receipts may have SET_NULL links after erasure.
        errors = {}
        if not self.user_id:
            errors['user'] = 'An owner is required when creating a delivery attempt.'
        if self.channel == self.Channel.APPLICATION:
            if not self.application_id:
                errors['application'] = 'Application delivery requires an application.'
            elif self.application.user_id != self.user_id:
                errors['application'] = 'Application owner does not match.'
        elif self.channel == self.Channel.ALERT:
            if not self.notification_id:
                errors['notification'] = 'Alert delivery requires a notification.'
            elif self.notification.user_id != self.user_id:
                errors['notification'] = 'Notification owner does not match.'
        if errors:
            raise ValidationError(errors)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(channel__in=[
                'application', 'alert', 'email_verification', 'password_reset']),
                name='delivery_channel_valid'),
            models.CheckConstraint(condition=models.Q(state__in=[
                'reserved', 'accepted', 'definite_failure', 'unknown']), name='delivery_state_valid'),
            # Permit erased links but never cross-link a channel to another purpose.
            models.CheckConstraint(condition=(
                models.Q(channel='application', notification__isnull=True)
                | models.Q(channel='alert', application__isnull=True)
                | models.Q(channel__in=['email_verification', 'password_reset'],
                           application__isnull=True, notification__isnull=True)),
                name='delivery_channel_links_valid'),
            models.CheckConstraint(condition=models.Q(failure_category__in=[
                '', 'transport', 'provider_rejected', 'timeout', 'configuration']),
                name='delivery_failure_category_valid'),
            models.UniqueConstraint(fields=['application'],
                condition=models.Q(state__in=['reserved', 'unknown']), name='delivery_app_unresolved'),
            models.UniqueConstraint(fields=['notification'],
                condition=models.Q(state__in=['reserved', 'unknown']), name='delivery_alert_unresolved'),
        ]


class DeliveryDailyBudget(models.Model):
    scope = models.CharField(max_length=64, validators=[
        RegexValidator(r'\A(?:global|user:[1-9][0-9]*)\Z', 'Use global or user:<positive id>.')])
    # Explicit Nairobi calendar day; no server-local date default.
    day = models.DateField()
    application_reserved = models.PositiveIntegerField(default=0)
    alert_reserved = models.PositiveIntegerField(default=0)
    account_reserved = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['scope', 'day'], name='delivery_budget_scope_day')]


# Dormant P4a evidence tables; no API, authorization service or sender reads them yet.
# see docs/CONCEPTS.md#application-send-authorization-schema
class ApplicationSendAuthorization(models.Model):
    class State(models.TextChoices):
        AUTHORIZED = 'authorized', 'Authorized'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        SUPERSEDED = 'superseded', 'Superseded'
        EXPIRED = 'expired', 'Expired'
        DISPATCH_STARTED = 'dispatch_started', 'Dispatch started'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_key = models.UUIDField(unique=True)
    application = models.ForeignKey(Application, on_delete=models.PROTECT, related_name='send_authorizations')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                              related_name='application_send_authorizations')
    document_approval = models.ForeignKey(ApplicationPackageApproval, on_delete=models.PROTECT,
                                          related_name='send_authorizations')
    plan = models.JSONField()
    plan_sha256 = models.CharField(max_length=64, validators=[
        RegexValidator(r'\A[0-9a-f]{64}\Z', 'A lowercase SHA-256 fingerprint is required.')])
    policy_version = models.CharField(max_length=40)
    authorized_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    state = models.CharField(max_length=16, choices=State.choices, default=State.AUTHORIZED)
    closed_at = models.DateTimeField(null=True, blank=True, default=None)
    retry_of = models.ForeignKey(DeliveryAttempt, on_delete=models.PROTECT, null=True, blank=True,
                                 default=None, related_name='retry_authorizations')

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(state__in=[
                'authorized', 'withdrawn', 'superseded', 'expired', 'dispatch_started']),
                name='app_send_state_valid'),
            models.CheckConstraint(condition=(
                models.Q(state='authorized', closed_at__isnull=True)
                | models.Q(state__in=['withdrawn', 'superseded', 'expired', 'dispatch_started'],
                           closed_at__isnull=False)), name='app_send_closed_time'),
            models.CheckConstraint(condition=models.Q(expires_at__gt=models.F('authorized_at')),
                                   name='app_send_expiry_valid'),
            models.UniqueConstraint(fields=['application'], condition=models.Q(state='authorized'),
                                    name='app_send_active_unique'),
        ]


class ApplicationSendAttemptLink(models.Model):
    authorization = models.OneToOneField(ApplicationSendAuthorization, on_delete=models.PROTECT,
                                         related_name='attempt_link')
    attempt = models.OneToOneField(DeliveryAttempt, on_delete=models.PROTECT,
                                   related_name='send_authorization_link')
    previous_attempt = models.ForeignKey(DeliveryAttempt, on_delete=models.PROTECT, null=True, blank=True,
                                         default=None, related_name='authorization_retry_links')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['previous_attempt'],
                condition=models.Q(previous_attempt__isnull=False), name='app_send_retry_unique'),
            models.CheckConstraint(condition=(models.Q(previous_attempt__isnull=True)
                | ~models.Q(previous_attempt=models.F('attempt'))), name='app_send_retry_not_self'),
        ]
