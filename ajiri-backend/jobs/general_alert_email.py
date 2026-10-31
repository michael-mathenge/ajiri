"""Default-off current-job alert delivery; no provider retries.

see docs/CONCEPTS.md#general-alert-email
"""
import json
import uuid
from urllib.parse import urlencode

from django.conf import settings
from django.utils.crypto import salted_hmac

from accounts.general_email import configuration
from profiles.alert_consent import eligible, unsubscribe_token
from .brevo_transport import BrevoTransport, Result
from .delivery_service import DeliveryError, DeliveryService
from .freshness import job_is_eligible
from .models import DeliveryAttempt, Notification


def enabled():
    return (getattr(settings, 'GENERAL_ALERT_EMAIL_ENABLED', False)
            and settings.ALERT_EMAIL_ENABLED and settings.JOB_FRESHNESS_ENFORCED
            and configuration() is not None)


def current(notification):
    profile = notification.user.profile
    event = profile.alert_consent_events.order_by('-pk').first()
    return (notification.user.is_active and not notification.sent_email
            and notification.match_score >= 70 and eligible(profile)
            and event is not None and event.created_at <= notification.created_at
            and job_is_eligible(notification.job))


class AlertTransport:
    def __init__(self, notification, policy):
        self.notification_id = notification.pk
        self.recipient = notification.user.email.casefold()
        self.policy = policy
        self.payload = None
        self.transport = BrevoTransport(settings.BREVO_API_KEY, policy.sender,
            timeout=policy.timeout, sender_name='Ajiri')

    def prepare(self, **kwargs):
        if (kwargs.get('attachments') or kwargs.get('reply_to')
                or kwargs['recipient'].casefold() != self.recipient):
            raise DeliveryError('Alert message is not allowed.')
        self.payload = self.transport.prepare(**kwargs)
        return self.payload

    def send(self, payload):
        notification = Notification.objects.select_related('user__profile', 'job').filter(pk=self.notification_id).first()
        if (not enabled() or configuration() != self.policy or notification is None
                or not current(notification) or notification.user.email.casefold() != self.recipient
                or payload != self.payload
                or json.loads(payload).get('to') != [{'email': self.recipient}]):
            return Result('definite_failure', failure_category='configuration')
        return self.transport.send(payload)


def deliver(notification_id):
    if not enabled():
        return 'disabled'
    notification = Notification.objects.select_related('user__profile', 'job').get(pk=notification_id)
    previous = DeliveryAttempt.objects.filter(notification=notification).order_by('-created_at').first()
    if previous:
        return previous.state  # Even definite failures require a separately scoped explicit retry.
    if not current(notification):
        return 'ineligible'
    user, job = notification.user, notification.job
    origin = settings.ACCOUNT_LINK_ORIGIN.rstrip('/')
    link = origin + '/unsubscribe#' + urlencode({'token': unsubscribe_token(user.profile)})
    text = (f'{job.title} - {job.company_name}\n'
            f'Review the current vacancy: {origin}/jobs/{job.pk}\n'
            'Availability can change. Applying is free.\nConfirm unsubscribe: ' + link)
    key = salted_hmac('ajiri.account-recipient-digest.v1', 'delivery-accounting', algorithm='sha256').digest()
    try:
        attempt = DeliveryService(AlertTransport(notification, configuration()), digest_key=key, enabled=True).deliver(
            user_id=user.pk, channel='alert', recipient=user.email.casefold(), subject='Ajiri job match',
            text=text, notification_id=notification.pk, alert_consent_confirmed=True,
            idempotency_key=uuid.uuid5(uuid.NAMESPACE_URL, f'ajiri-match-alert:{notification.pk}'))
    except DeliveryError:
        return 'unavailable'
    if attempt.state == 'accepted':
        Notification.objects.filter(pk=notification.pk).update(sent_email=True)
    return attempt.state
