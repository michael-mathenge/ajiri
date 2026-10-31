"""Separate explicit choice and durable identity-free daily counts.

see docs/CONCEPTS.md#durable-aggregate-analytics
"""
import re
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from profiles.models import Profile
from .models import AnalyticsChoice, AnalyticsDailyCount

EVENTS = ('search_used', 'cv_review_opened', 'application_review_opened')


def available():
    version = getattr(settings, 'ANALYTICS_POLICY_VERSION', '')
    return (getattr(settings, 'ANALYTICS_ENABLED', False) is True
        and getattr(settings, 'ANALYTICS_PURPOSE_CONFIRMED', False) is True
        and isinstance(version, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}', version) is not None)


def current_choice(user):
    return AnalyticsChoice.objects.filter(owner=user).order_by('-pk').first()


def choose(user, *, decision_id, enabled, policy_version=''):
    if type(enabled) is not bool:
        raise ValueError('An explicit independent analytics choice is required.')
    with transaction.atomic():
        # Choice/revocation and collection share this first-write cutoff on SQLite/Postgres.
        if Profile.objects.filter(user=user).update(headline=F('headline')) != 1:
            raise ValueError('Account unavailable.')
        existing = AnalyticsChoice.objects.filter(decision_id=decision_id).first()
        if existing:
            if (existing.owner_id != user.pk or existing.enabled != enabled or existing.policy_version != policy_version):
                raise ValueError('Decision identity was already used.')
            return existing  # Never replay an old opt-in over a newer withdrawal.
        if enabled and (not available() or not user.is_active or policy_version != settings.ANALYTICS_POLICY_VERSION):
            raise ValueError('Current analytics purpose and policy acknowledgement are unavailable.')
        return AnalyticsChoice.objects.create(owner=user, decision_id=decision_id,
            enabled=enabled, policy_version=policy_version)


def record(user, event):
    if event not in EVENTS:
        raise ValueError('Use an allowlisted analytics event without attributes.')
    if not available():
        return False
    with transaction.atomic():
        if Profile.objects.filter(user=user).update(headline=F('headline')) != 1:
            return False
        choice = current_choice(user)
        now = timezone.now()
        if (not user.__class__.objects.filter(pk=user.pk, is_active=True).exists()
                or choice is None or not choice.enabled or choice.created_at > now
                or choice.policy_version != settings.ANALYTICS_POLICY_VERSION or not available()):
            return False
        day = now.astimezone(ZoneInfo('Africa/Nairobi')).date()
        counter, _ = AnalyticsDailyCount.objects.get_or_create(day=day, event=event)
        AnalyticsDailyCount.objects.filter(pk=counter.pk).update(count=F('count')+1)
        return True
