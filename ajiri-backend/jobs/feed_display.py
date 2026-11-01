"""Browse-only feed visibility; never use this for eligibility or sending.

see docs/CONCEPTS.md#unverified-feed-display
"""
from django.conf import settings
from django.db.models import Q, Exists, OuterRef
from django.utils import timezone

from .freshness import eligible_jobs
from .models import Job

NOTICE = "Not verified: check the employer's page before applying"


def supplemental_jobs(queryset=None, at=None):
    at = at or timezone.now()
    queryset = Job.objects.all() if queryset is None else queryset
    # Historical ingestion predates publication records. Only the established
    # feed name identifies those rows; missing evidence is never employer proof.
    feed = Q(publication__origin='rss', publication__organisation__isnull=True) | Q(
        publication__isnull=True, source_name='MyJobMag Kenya')
    # These two archive reasons describe absent/stale evidence. Actual closure
    # and unexplained archives remain hidden, even when their deadline is absent.
    allowed_status = (
        Q(publication__isnull=True)
        | Q(publication__status__in=['unverified', 'published'], publication__archive_reason='')
        | Q(publication__status='archived', publication__archive_reason__in=[
            'availability_not_verified', 'deadline_or_confirmation_expired'])
    )
    return (queryset.filter(is_active=True, is_flagged_scam=False)
            .filter(Q(posted_at__isnull=True) | Q(posted_at__lte=at))
            .filter(feed)
            .filter(Q(publication__closes_at__isnull=True) | Q(publication__closes_at__gt=at))
            .filter(allowed_status))


def browse_jobs(queryset=None, at=None, enabled=None):
    at = at or timezone.now()
    queryset = Job.objects.all() if queryset is None else queryset
    enabled = settings.JOB_FEED_DISPLAY_ENABLED if enabled is None else enabled
    eligible = eligible_jobs(at=at).filter(pk=OuterRef('pk'))
    result = queryset.annotate(_can_apply=Exists(eligible))
    if enabled:
        supplemental = supplemental_jobs(at=at).filter(pk=OuterRef('pk'))
        result = result.annotate(_feed_candidate=Exists(supplemental))
        return result.filter(Q(_can_apply=True) | Q(_feed_candidate=True))
    return result.filter(_can_apply=True)
