"""One eligibility rule for browsing, alerts and new application actions.

see docs/CONCEPTS.md#job-freshness-evidence
"""

from django.conf import settings
from django.db.models import Q, F
from django.utils import timezone
from datetime import timedelta
from .models import Job, JobPublication


def eligible_jobs(queryset=None, at=None):
    queryset = Job.objects.all() if queryset is None else queryset
    queryset = queryset.filter(is_active=True, is_flagged_scam=False)
    if not getattr(settings, "JOB_FRESHNESS_ENFORCED", False):
        return queryset
    at = at or timezone.now()
    return (
        queryset.exclude(posted_at__gt=at)
        .filter(publication__status="published")
        .filter(
            Q(publication__closes_at__gt=at)
            | Q(
                publication__closes_at__isnull=True, publication__confirmed_until__gt=at
            )
        )
        .filter(
            Q(publication__origin="rss", publication__confirmed_at__gt=at-timedelta(seconds=settings.RSS_AVAILABILITY_MAX_AGE_SECONDS))
            | Q(
                publication__origin="employer",
                publication__organisation__status="approved",
                publication__organisation__owner__is_active=True,
                publication__organisation__owner__profile__email_verified_at__isnull=False,
                publication__organisation__owner__profile__verified_email=F(
                    "publication__organisation__owner__email"
                ),
            )
        )
    )


def job_is_eligible(job):
    return eligible_jobs().filter(pk=job.pk).exists()


def archive_expired(at=None):
    """Preserve rows/documents; the read gate already hides expired entries."""
    at = at or timezone.now()
    if getattr(settings, 'JOB_FRESHNESS_ENFORCED', False):
        # Historical active rows have no inferred proof. Archive them as
        # unverified, not as "expired", while preserving every related application.
        unknown = Job.objects.filter(is_active=True, publication__isnull=True)
        batch = []
        for job in unknown.iterator(chunk_size=500):
            batch.append(JobPublication(job=job, origin='rss', status='archived',
                archive_reason='availability_not_verified', archived_at=at))
            if len(batch) == 500:
                JobPublication.objects.bulk_create(batch, ignore_conflicts=True)
                batch = []
        if batch:
            JobPublication.objects.bulk_create(batch, ignore_conflicts=True)
    expired = JobPublication.objects.filter(status="published").filter(
        Q(closes_at__lte=at)
        | Q(closes_at__isnull=True, confirmed_until__lte=at)
        | Q(closes_at__isnull=True, confirmed_until__isnull=True)
        | Q(origin='rss', confirmed_at__lte=at-timedelta(seconds=settings.RSS_AVAILABILITY_MAX_AGE_SECONDS))
        | Q(origin='rss', confirmed_at__isnull=True)
    )
    return expired.update(
        status="archived",
        archive_reason="deadline_or_confirmation_expired",
        archived_at=at,
    )
