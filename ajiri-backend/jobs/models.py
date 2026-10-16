import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from profiles.models import Skill


class Job(models.Model):
    """
    A single job listing pulled in from an external job board.
    We don't create jobs ourselves — every Job row represents something
    scraped/ingested from a source like BrighterMonday or MyJobMag.
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
