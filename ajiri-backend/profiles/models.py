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

    # Job Alerts preferences — let a user opt out of a channel without
    # touching code. Both default True so alerts work out of the box.
    # See docs/CONCEPTS.md#job-alerts
    notify_email = models.BooleanField(default=True)
    notify_in_app = models.BooleanField(default=True)

    # Proof belongs to the exact address, never inferred from login/preferences.
    # see docs/CONCEPTS.md#verification-proof-schema
    email_verified_at = models.DateTimeField(null=True, blank=True, default=None)
    verified_email = models.EmailField(max_length=254, blank=True, default='')
    password_reset_at = models.DateTimeField(null=True, blank=True, default=None)

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
