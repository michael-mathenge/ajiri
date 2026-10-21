"""Owner-only synthetic alert pilot; normal public alert sending remains disabled."""
from dataclasses import dataclass
from html import escape
import json
from urllib.parse import urlencode
import uuid

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils.crypto import salted_hmac
from accounts import pilot as account_pilot
from profiles.alert_consent import eligible, unsubscribe_token
from .brevo_transport import BrevoTransport, Result
from .delivery_service import DeliveryService, DeliveryError
from .models import Notification

SYNTHETIC_SOURCE = 'ajiri-owner-alert-pilot'


@dataclass(frozen=True)
class AlertPilot:
    owner_id: int
    recipient: str
    sender: str
    timeout: int
    limit: int
    alert_only: bool = True


def configuration():
    if not getattr(settings, 'ALERT_EMAIL_ENABLED', False):
        return None
    account = account_pilot.configuration()
    if account is None:
        return None
    return AlertPilot(account.owner_id, account.recipient, account.sender, account.timeout, account.limit)


def synthetic(notification, policy):
    job = notification.job
    prefix = f'https://example.invalid/ajiri-owner-alert-pilot/{policy.owner_id}/'
    return (job.source_name == SYNTHETIC_SOURCE and job.source_url.startswith(prefix)
            and job.title == 'Ajiri synthetic alert pilot' and job.company_name == 'Synthetic example'
            and not job.is_active and not job.is_flagged_scam)


def availability(user):
    try:
        policy = configuration()
    except ImproperlyConfigured:
        return 'unavailable'
    if policy is None:
        return 'disabled'
    return 'owner_pilot' if user.pk == policy.owner_id and user.email.casefold() == policy.recipient else 'pilot_only'


class AlertPilotTransport:
    def __init__(self, policy, notification_id, transport, *, subject, text):
        self.policy, self.notification_id, self.transport = policy, notification_id, transport
        self.subject, self.text = subject, text

    def prepare(self, **kwargs):
        if kwargs.get('attachments') or kwargs.get('reply_to'):
            raise DeliveryError('Alert attachments and reply overrides are disabled.')
        payload = json.loads(self.transport.prepare(**kwargs))
        payload['htmlContent'] = '<pre>' + escape(payload['textContent']) + '</pre>'
        value = json.dumps(payload, ensure_ascii=True).encode('utf-8')
        self.validate(value)
        return value

    def validate(self, payload):
        try:
            data = json.loads(payload)
            if (len(payload) > 65536 or set(data) != {'sender', 'to', 'subject', 'textContent', 'htmlContent'}
                    or data['to'] != [{'email': self.policy.recipient}]
                    or data['sender'] != {'email': self.policy.sender, 'name': 'Ajiri'}
                    or data['subject'] != self.subject or data['textContent'] != self.text
                    or data['htmlContent'] != '<pre>' + escape(self.text) + '</pre>'):
                raise ValueError
        except (ValueError, KeyError, TypeError):
            raise DeliveryError('Alert pilot payload is not allowed.') from None

    def send(self, payload):
        self.validate(payload)
        try:
            notification = Notification.objects.select_related('user__profile', 'job').get(pk=self.notification_id)
            allowed = (configuration() == self.policy and notification.user_id == self.policy.owner_id
                and notification.user.email.casefold() == self.policy.recipient
                and eligible(notification.user.profile) and synthetic(notification, self.policy))
        except (ImproperlyConfigured, ObjectDoesNotExist):
            allowed = False
        if not allowed:
            return Result('definite_failure', failure_category='configuration')
        return self.transport.send(payload)


def deliver_match(notification, *, explicit_owner_pilot=False):
    # see docs/CONCEPTS.md#owner-alert-pilot
    # Ingestion cannot open a new sending route; only an explicit synthetic owner pilot can hand off.
    if not explicit_owner_pilot:
        return False
    try:
        policy = configuration()
        if (policy is None or notification.sent_email or notification.user_id != policy.owner_id
                or notification.user.email.casefold() != policy.recipient
                or not eligible(notification.user.profile) or not synthetic(notification, policy)):
            return False
        origin = settings.ACCOUNT_LINK_ORIGIN.rstrip('/')
        link = origin + '/unsubscribe#' + urlencode({'token': unsubscribe_token(notification.user.profile)})
        subject = '[AJIRI ALERT PILOT] Synthetic job match'
        text = ('This is an owner-only synthetic Ajiri job-alert test, not a real vacancy.\n\n'
                'No employer was contacted and no application was sent.\n\n'
                'Turn off email job alerts (confirmation required): ' + link)
        transport = AlertPilotTransport(policy, notification.pk,
            BrevoTransport(api_key=settings.BREVO_API_KEY, sender=policy.sender, timeout=policy.timeout, sender_name='Ajiri'),
            subject=subject, text=text)
        key = salted_hmac('ajiri.account-recipient-digest.v1', 'delivery-accounting', algorithm='sha256').digest()
        attempt = DeliveryService(transport, digest_key=key, enabled=True, pilot=policy).deliver(
            user_id=notification.user_id, channel='alert', recipient=policy.recipient,
            subject=subject, text=text, notification_id=notification.pk, alert_consent_confirmed=True,
            idempotency_key=uuid.uuid5(uuid.NAMESPACE_URL, 'ajiri-alert:' + str(notification.pk)))
        if attempt.state == 'accepted':
            Notification.objects.filter(pk=notification.pk).update(sent_email=True)
            return True  # Provider acceptance only; inbox delivery still needs owner feedback.
        return False
    except (ImproperlyConfigured, DeliveryError, ObjectDoesNotExist):
        return False  # No console fallback, retry loop or raw provider message.
