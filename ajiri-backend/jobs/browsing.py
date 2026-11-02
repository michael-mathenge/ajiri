"""Fail-closed, bounded-cache control for authenticated supplemental browsing.

see docs/CONCEPTS.md#admin-job-browsing
"""
from django.conf import settings
from django.core.cache import cache

CACHE_KEY = 'job-browsing-enabled-v1'
CACHE_SECONDS = 60


def supplemental_browsing_enabled():
    # Evaluate rollback before the cache: a cached True cannot defeat it.
    if settings.JOB_FEED_DISPLAY_FORCE_OFF:
        return False
    try:
        value = cache.get(CACHE_KEY)
        if type(value) is bool:
            return value
        from .models import JobBrowsingSettings
        value = JobBrowsingSettings.objects.filter(pk=1).values_list(
            'supplemental_browsing_enabled', flat=True).first() is True
        cache.set(CACHE_KEY, value, CACHE_SECONDS)
        return value
    except Exception:
        # Cache adapters have different exception types. All read failures close
        # this optional surface; never include exception/configuration contents.
        return False


def invalidate_browsing_cache():
    try:
        cache.delete(CACHE_KEY)
    except Exception:
        # Other workers also expire their cached reads within sixty seconds.
        pass
