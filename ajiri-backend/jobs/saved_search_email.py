"""Closed memory-only email integration. Not called by any production route/sweep."""
import uuid
import json
from urllib.parse import urlencode

from django.conf import settings
from django.db.models import F
from django.utils.crypto import salted_hmac
from profiles.alert_consent import eligible, unsubscribe_token
from accounts.email_delivery import MemoryTransport
from .brevo_transport import Result
from .delivery_service import DeliveryService, DeliveryError
from .freshness import job_is_eligible
from .models import SavedSearchMatch, Notification, DeliveryAttempt
from .saved_searches import collect_due


def test_boundary():
    return (settings.SAVED_SEARCH_EMAIL_TEST_CAPTURE is True
            and settings.ACCOUNT_EMAIL_TEST_CAPTURE is True
            and settings.EMAIL_BACKEND == 'django.core.mail.backends.locmem.EmailBackend'
            and settings.REAL_EMAIL_ENABLED is False)


class RecheckedMemoryTransport(MemoryTransport):
    def __init__(self, match_id):
        self.match_id = match_id

    def send(self, payload):
        row = SavedSearchMatch.objects.select_related('search__owner__profile', 'job').filter(pk=self.match_id).first()
        if (not test_boundary() or row is None or row.search.revision != row.revision
                or row.search.email_frequency == 'off' or not settings.SAVED_SEARCHES_ENABLED
                or not eligible(row.search.owner.profile) or not job_is_eligible(row.job)):
            return Result('definite_failure', failure_category='configuration')
        event = row.search.owner.profile.alert_consent_events.order_by('-pk').first()
        if (event.created_at > row.window_start
                or json.loads(payload).get('to') != [{'email': row.search.owner.email}]):
            return Result('definite_failure', failure_category='configuration')
        return super().send(payload)


def capture_due_email(search_id, *, at=None):
    # see docs/CONCEPTS.md#saved-search-windows
    if not test_boundary():
        return []  # No collection, receipt or quota mutation outside closed tests.
    collect_due(search_id, 'email', at=at)
    # A scalar F comparison keeps old query revisions out of a changed search.
    rows = SavedSearchMatch.objects.select_related('search__owner__profile', 'job').filter(
        search_id=search_id, channel='email', email_attempt__isnull=True, revision=F('search__revision'))
    outcomes = []
    for row in rows.order_by('pk')[:50]:
        user = row.search.owner
        if (row.search.email_frequency == 'off' or not eligible(user.profile)
                or not job_is_eligible(row.job)
                or user.profile.alert_consent_events.order_by('-pk').first().created_at > row.window_start):
            continue
        notification, _ = Notification.objects.get_or_create(user=user, job=row.job,
            defaults={'match_score': 0, 'in_app': False})
        # Reuse the shared notification receipt across overlapping saved searches.
        previous = DeliveryAttempt.objects.filter(notification=notification).order_by('-created_at').first()
        if previous:
            SavedSearchMatch.objects.filter(pk=row.pk).update(notification=notification, email_attempt=previous)
            outcomes.append(previous.state)
            continue
        origin = settings.ACCOUNT_LINK_ORIGIN.rstrip('/')
        link = origin + '/unsubscribe#' + urlencode({'token': unsubscribe_token(user.profile)})
        text = ('Synthetic saved-search test: ' + row.search.name + '\n' + row.job.title
                + '\nOnly current availability evidence is considered.\nConfirm unsubscribe: ' + link)
        key = salted_hmac('ajiri.account-recipient-digest.v1', 'delivery-accounting', algorithm='sha256').digest()
        try:
            attempt = DeliveryService(RecheckedMemoryTransport(row.pk), digest_key=key, enabled=True).deliver(
                user_id=user.pk, channel='alert', recipient=user.email,
                subject='[AJIRI TEST] Saved search match', text=text, notification_id=notification.pk,
                alert_consent_confirmed=True, idempotency_key=uuid.uuid5(uuid.NAMESPACE_URL, f'ajiri-saved-search:{row.pk}'))
        except DeliveryError:
            continue  # No automatic provider retry or cursor rewind.
        SavedSearchMatch.objects.filter(pk=row.pk).update(notification=notification, email_attempt=attempt)
        if attempt.state == 'accepted':
            Notification.objects.filter(pk=notification.pk).update(sent_email=True)
        outcomes.append(attempt.state)
    return outcomes
