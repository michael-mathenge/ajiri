from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    headline = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    skills = models.ManyToManyField(Skill, blank=True, related_name='profiles')
    cv_file = models.FileField(upload_to='cvs/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    # New users must explicitly choose email; in-app remains independent.
    # See docs/CONCEPTS.md#job-alerts
    notify_email = models.BooleanField(default=False)
    notify_in_app = models.BooleanField(default=True)

    # Proof belongs to the exact address, never inferred from login/preferences.
    # see docs/CONCEPTS.md#verification-proof-schema
    email_verified_at = models.DateTimeField(null=True, blank=True, default=None)
    verified_email = models.EmailField(max_length=254, blank=True, default='')
    password_reset_at = models.DateTimeField(null=True, blank=True, default=None)
    # No historical acknowledgement is inferred for existing accounts.
    # see docs/CONCEPTS.md#privacy-notice-acknowledgement
    privacy_consented_at = models.DateTimeField(null=True, blank=True, default=None)
    privacy_policy_version = models.CharField(max_length=40, blank=True, default='')

    def __str__(self):
        return f"{self.user.email}'s profile"


# New workspaces are explicit; existing profiles acquire no inferred approval.
# see docs/CONCEPTS.md#cv-builder-schema
class CVWorkspace(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='cv_workspace')
    content = models.JSONField(default=dict, blank=True)
    revision = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(revision__gte=1), name='cv_workspace_revision_positive')]


class AlertConsentEvent(models.Model):
    # see docs/CONCEPTS.md#explicit-alert-consent
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='alert_consent_events')
    decision_id = models.UUIDField(unique=True)
    enabled = models.BooleanField()
    channel = models.CharField(max_length=8, default='email')
    policy_version = models.CharField(max_length=40)
    recipient_digest = models.CharField(max_length=64)
    source = models.CharField(max_length=16, choices=[('in_app', 'In app'), ('unsubscribe', 'Unsubscribe')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(channel='email'), name='alert_consent_email_channel'),
            models.CheckConstraint(condition=models.Q(source__in=['in_app', 'unsubscribe']), name='alert_consent_source_valid'),
        ]


def approved_cv_path(instance, filename):
    # Ignore user filenames; files remain under the existing private storage.
    return f'approved-cvs/{uuid.uuid4().hex}.docx'


class CVApproval(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='cv_approvals')
    revision = models.PositiveIntegerField()
    content = models.JSONField()
    content_sha256 = models.CharField(max_length=64)
    template_version = models.CharField(max_length=32)
    document = models.FileField(upload_to=approved_cv_path, max_length=100)
    document_sha256 = models.CharField(max_length=64)
    approved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(revision__gte=1), name='cv_approval_revision_positive'),
            models.UniqueConstraint(fields=('profile', 'revision'), name='cv_approval_unique_revision'),
        ]


def certificate_path(instance, filename):
    return f'quarantine/certificates/{uuid.uuid4().hex}.pdf'


class CertificateEvidence(models.Model):
    # Private, unverified supporting evidence, never included in approval snapshots.
    # see docs/CONCEPTS.md#private-certificate-evidence
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='certificate_evidence')
    certification_id = models.UUIDField()
    document = models.FileField(upload_to=certificate_path, max_length=100)
    sha256 = models.CharField(max_length=64)
    size_bytes = models.PositiveIntegerField()
    scan_state = models.CharField(max_length=16, default='pending')
    scan_version = models.CharField(max_length=128, blank=True, default='')
    scanned_at = models.DateTimeField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('profile', 'certification_id'), name='certificate_unique_entry'),
            models.CheckConstraint(condition=models.Q(size_bytes__gte=1, size_bytes__lte=5*1024*1024),
                name='certificate_bounded_size'),
            models.CheckConstraint(condition=models.Q(scan_state__in=['pending', 'scanning', 'clean', 'infected', 'unavailable']),
                name='certificate_scan_state_valid'),
        ]
