"""Single-job, reasoned staff reviews; never invent publication evidence.

see docs/CONCEPTS.md#reasoned-job-moderation
"""
import hashlib
import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F

from .models import Job, JobModerationReview, JobPublication


class StaleReview(Exception):
    pass


def snapshot(job):
    fields = ('title', 'company_name', 'description', 'requirements', 'location',
              'job_type', 'source_url', 'source_name', 'is_active', 'is_flagged_scam',
              'scam_flags', 'application_method', 'application_email',
              'external_application_url', 'posted_at', 'salary_min', 'salary_max',
              'is_salary_negotiable')
    data = {field: getattr(job, field) for field in fields}
    data['publication'] = JobPublication.objects.filter(job=job).values(
        'origin', 'status', 'closes_at', 'confirmed_until', 'confirmed_at',
        'evidence_url', 'archive_reason', 'archived_at', 'organisation_id').first()
    data['skills'] = list(job.skills_required.order_by('pk').values_list('pk', flat=True))
    data['last_review'] = JobModerationReview.objects.filter(job=job).order_by('-pk').values_list('pk', flat=True).first()
    return json.loads(json.dumps(data, sort_keys=True, default=str))


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def review(actor, job_id, expected, decision, reason):
    if not actor.is_active or not actor.is_staff or not actor.has_perm('jobs.change_job'):
        raise PermissionDenied
    reason = reason.strip() if isinstance(reason, str) else ''
    if decision not in ('clear', 'uphold') or not reason or len(reason) > 1000:
        raise ValidationError('Choose a decision and give a reason of at most 1,000 characters.')
    with transaction.atomic():
        # SQLite has no row locks: claim the writer before reading review evidence.
        # A busy claim fails safely; it must not replay an uncertain decision.
        Job.objects.filter(pk=job_id).update(is_flagged_scam=F('is_flagged_scam'))
        job = Job.objects.select_for_update().get(pk=job_id)
        before = snapshot(job)
        if not job.is_flagged_scam or fingerprint(before) != expected:
            raise StaleReview('This job changed. Reload and review its current evidence before deciding.')
        # Update only the flag. Clearing it cannot revive an inactive/expired job.
        Job.objects.filter(pk=job.pk).update(is_flagged_scam=decision == 'uphold')
        job.refresh_from_db()
        after = snapshot(job)
        return JobModerationReview.objects.create(job=job, actor=actor,
            reviewed_fingerprint=expected, decision=decision, reason=reason,
            before=before, after=after)
