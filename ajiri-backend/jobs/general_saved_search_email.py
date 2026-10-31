"""Default-off durable saved-search windows with real HTTPS mail transport.

see docs/CONCEPTS.md#general-saved-search-email
"""
import json
import uuid
from urllib.parse import urlencode

from django.conf import settings
from django.db.models import F
from django.utils.crypto import salted_hmac

from accounts.general_email import configuration
from profiles.alert_consent import eligible, unsubscribe_token
from .brevo_transport import BrevoTransport, Result
from .delivery_service import DeliveryError, DeliveryService
from .freshness import job_is_eligible
from .models import DeliveryAttempt, Notification, SavedSearchMatch
from .saved_searches import collect_due


def enabled():
    return (getattr(settings, 'SAVED_SEARCH_EMAIL_ENABLED', False)
            and settings.ALERT_EMAIL_ENABLED and settings.SAVED_SEARCHES_ENABLED
            and settings.JOB_FRESHNESS_ENFORCED and configuration() is not None)


def current(row):
    event = row.search.owner.profile.alert_consent_events.order_by('-pk').first()
    return (row.channel == 'email' and row.revision == row.search.revision
        and row.search.email_frequency in ('daily', 'weekly') and eligible(row.search.owner.profile)
        and event is not None and event.created_at <= row.window_start and job_is_eligible(row.job))


class SearchTransport:
    def __init__(self, row):
        self.identity = row.pk
        self.recipient = row.search.owner.email.casefold()
        self.policy = configuration()
        self.payload = None
        self.transport = BrevoTransport(settings.BREVO_API_KEY, self.policy.sender,
            timeout=self.policy.timeout, sender_name='Ajiri')

    def prepare(self, **kwargs):
        if (kwargs.get('attachments') or kwargs.get('reply_to')
                or kwargs['recipient'].casefold() != self.recipient):
            raise DeliveryError('Saved-search message is not allowed.')
        self.payload = self.transport.prepare(**kwargs)
        return self.payload

    def send(self, payload):
        row = SavedSearchMatch.objects.select_related('search__owner__profile', 'job').filter(pk=self.identity).first()
        if (not enabled() or configuration() != self.policy or row is None or not current(row)
                or row.search.owner.email.casefold() != self.recipient or payload != self.payload
                or json.loads(payload).get('to') != [{'email': self.recipient}]):
            return Result('definite_failure', failure_category='configuration')
        return self.transport.send(payload)


def deliver_due(search_id, *, at=None):
    if not enabled():
        return []
    collect_due(search_id, 'email', at=at)
    rows = SavedSearchMatch.objects.select_related('search__owner__profile', 'job').filter(
        search_id=search_id, channel='email', email_attempt__isnull=True, revision=F('search__revision'))
    outcomes = []
    for row in rows.order_by('pk')[:50]:
        if not current(row):
            continue
        user = row.search.owner
        notification, _ = Notification.objects.get_or_create(user=user, job=row.job,
            defaults={'match_score': 0, 'in_app': False})
        previous = DeliveryAttempt.objects.filter(notification=notification).order_by('-created_at').first()
        if previous:
            SavedSearchMatch.objects.filter(pk=row.pk).update(notification=notification, email_attempt=previous)
            outcomes.append(previous.state)
            continue
        origin = settings.ACCOUNT_LINK_ORIGIN.rstrip('/')
        link = origin + '/unsubscribe#' + urlencode({'token': unsubscribe_token(user.profile)})
        text = (f'Saved search: {row.search.name}\n{row.job.title} - {row.job.company_name}\n'
            f'Review the current vacancy: {origin}/jobs/{row.job_id}\n'
            'Availability can change. Applying is free.\nConfirm unsubscribe: ' + link)
        key = salted_hmac('ajiri.account-recipient-digest.v1', 'delivery-accounting', algorithm='sha256').digest()
        try:
            attempt = DeliveryService(SearchTransport(row), digest_key=key, enabled=True).deliver(
                user_id=user.pk, channel='alert', recipient=user.email.casefold(),
                subject='Ajiri saved search match', text=text, notification_id=notification.pk,
                alert_consent_confirmed=True,
                idempotency_key=uuid.uuid5(uuid.NAMESPACE_URL, f'ajiri-saved-search:{row.pk}'))
        except DeliveryError:
            continue
        SavedSearchMatch.objects.filter(pk=row.pk).update(notification=notification, email_attempt=attempt)
        if attempt.state == 'accepted':
            Notification.objects.filter(pk=notification.pk).update(sent_email=True)
        outcomes.append(attempt.state)
    return outcomes
