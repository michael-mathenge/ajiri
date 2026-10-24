"""Private saved queries and bounded Nairobi-day windows; no production email route."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, OperationalError
from django.db.models import F
from django.utils import timezone
from profiles.alert_consent import eligible
from .filters import JobFilter
from .freshness import eligible_jobs
from .models import SavedSearch, SavedSearchMatch

MAX_SEARCHES = 10
MAX_MATCHES = 50
NAIROBI = ZoneInfo('Africa/Nairobi')


def next_window(at, frequency):
    if frequency == 'off':
        return None
    days = 1 if frequency == 'daily' else 7
    return datetime.combine(at.astimezone(NAIROBI).date() + timedelta(days=days), time.min, tzinfo=NAIROBI)


def reset_windows(search, at):
    search.in_app_cursor = search.email_cursor = at
    search.next_in_app_at = next_window(at, search.in_app_frequency)
    search.next_email_at = next_window(at, search.email_frequency)


def collect_due(search_id, channel='in_app', *, at=None):
    # see docs/CONCEPTS.md#saved-search-windows
    if channel not in ('in_app', 'email'):
        raise ValueError('Invalid saved-search channel.')
    if not settings.SAVED_SEARCHES_ENABLED:
        return []
    at = at or timezone.now()
    with transaction.atomic():
        # Claim SQLite's writer slot before reading a due window, also used by edits.
        if not SavedSearch.objects.filter(pk=search_id).update(revision=F('revision')):
            return []
        search = SavedSearch.objects.select_related('owner__profile').get(pk=search_id)
        frequency = getattr(search, channel + '_frequency')
        due = getattr(search, 'next_' + channel + '_at')
        if frequency == 'off' or due is None or due > at:
            return []
        step = timedelta(days=1 if frequency == 'daily' else 7)
        end = due + step * ((at - due) // step)
        start = getattr(search, channel + '_cursor')
        try:
            profile = search.owner.profile
        except ObjectDoesNotExist:
            profile = None
        allowed = bool(profile is not None and search.owner.is_active
                       and (profile.notify_in_app if channel == 'in_app' else eligible(profile)))
        if channel == 'email' and allowed:
            # Saving a search or an old legacy preference never grants consent.
            start = max(start, profile.alert_consent_events.order_by('-pk').first().created_at)
        rows = []
        if allowed and start < end:
            jobs = eligible_jobs(at=at).filter(scraped_at__gt=start, scraped_at__lte=end)
            query = JobFilter({'q': search.q, 'location': search.location, 'job_type': search.job_type}, queryset=jobs)
            if not query.is_valid():
                raise ValueError('Stored saved search is invalid.')
            for job in query.qs.order_by('-scraped_at', '-pk')[:MAX_MATCHES]:
                row, created = SavedSearchMatch.objects.get_or_create(search=search, revision=search.revision,
                    job=job, channel=channel, defaults={'window_start': start, 'window_end': end})
                if created:
                    rows.append(row.pk)
        setattr(search, channel + '_cursor', end)
        setattr(search, 'next_' + channel + '_at', end + step)
        search.save(update_fields=[channel + '_cursor', 'next_' + channel + '_at'])
        return rows


def run_due_saved_searches():
    if not settings.SAVED_SEARCHES_ENABLED:
        return 0
    now = timezone.now()
    count = 0
    for pk in SavedSearch.objects.filter(next_in_app_at__lte=now).values_list('pk', flat=True).iterator():
        try:
            count += len(collect_due(pk, at=now))
        except OperationalError:
            continue  # Rolled-back window remains due; no external effect to repeat.
    return count
