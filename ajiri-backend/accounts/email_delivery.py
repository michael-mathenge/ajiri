"""Account bridge to shared budgets: separately gated general mail, tests or pilot.

Real sending defaults off. Never fall back to console for security links.
see docs/CONCEPTS.md#account-email-accounting
"""
import hashlib
import hmac
import json
import uuid
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.utils import timezone
from django.utils.crypto import salted_hmac

from jobs.brevo_transport import Result
from jobs.delivery_service import DeliveryError, DeliveryService, QuotaExceeded
from jobs.models import DeliveryAttempt
from . import general_email, pilot


def test_available():
    return (getattr(settings, 'ACCOUNT_EMAIL_TEST_CAPTURE', False) is True
        and settings.EMAIL_BACKEND == 'django.core.mail.backends.locmem.EmailBackend')


def available():
    if getattr(settings, 'ACCOUNT_SECURITY_EMAIL_ENABLED', False):
        return general_email.configuration() is not None
    return pilot.configuration() is not None or test_available()


def eligible(user, purpose):
    if getattr(settings, 'ACCOUNT_SECURITY_EMAIL_ENABLED', False):
        return general_email.eligible(user, purpose)
    if getattr(settings, 'REAL_EMAIL_ENABLED', False):
        return pilot.eligible(user, purpose)
    return test_available()


class MemoryTransport:
    """Test sink only. It shares Brevo's payload contract, never opens a socket."""
    def prepare(self, *, recipient, subject, text, reply_to=None, attachments=(), max_attachment_bytes=0):
        if attachments or reply_to:
            raise DeliveryError('Account email cannot contain attachments or a reply override.')
        return json.dumps({'to': [{'email': recipient}], 'sender': {'email': settings.DEFAULT_FROM_EMAIL},
            'subject': subject, 'textContent': text}).encode()

    def send(self, payload):
        if getattr(settings, 'REAL_EMAIL_ENABLED', False) or not available():
            return Result('definite_failure', failure_category='configuration')
        message = json.loads(payload)
        sent = EmailMessage(subject=message['subject'], body=message['textContent'],
            from_email=message['sender']['email'], to=[message['to'][0]['email']],
            connection=get_connection('django.core.mail.backends.locmem.EmailBackend')).send(fail_silently=False)
        return Result('accepted', '<locmem-' + uuid.uuid4().hex + '>') if sent == 1 else Result('unknown', failure_category='transport')


def next_day_wait():
    now = timezone.now().astimezone(ZoneInfo('Africa/Nairobi'))
    midnight = datetime.combine(now.date()+timedelta(days=1), time.min, tzinfo=now.tzinfo)
    return max(1, int((midnight-now).total_seconds())+1)


def deliver_account_link(user, purpose, text, request_id):
    """One explicit request, no background/provider retries; return only safe status.

    A definite-failure retry is selected only for a NEW explicit HTTP request ID.
    Unknown/reserved outcomes are never reset by this bridge.
    """
    if not eligible(user, purpose):
        return 'disabled'
    if purpose not in ('password_reset', 'email_verification'):
        raise ValueError('Invalid account email purpose.')
    key = salted_hmac('ajiri.account-recipient-digest.v1', 'delivery-accounting', algorithm='sha256').digest()
    digest = hmac.new(key, user.email.casefold().encode(), hashlib.sha256).hexdigest()
    previous = DeliveryAttempt.objects.filter(user=user, channel=purpose,
        recipient_digest=digest, state='definite_failure').order_by('-created_at').first()
    try:
        general = general_email.configuration()
        policy = None if general else pilot.configuration()
        sink = (general_email.AccountTransport(general, user, purpose) if general else
            pilot.transport(policy) if policy else MemoryTransport())
        attempt = DeliveryService(sink, digest_key=key, enabled=True, pilot=policy).deliver(
            user_id=user.pk, channel=purpose, recipient=user.email.casefold(), subject='Ajiri account security',
            text=text, idempotency_key=request_id, retry_of=previous.pk if previous else None)
        return attempt.state
    except QuotaExceeded:
        return 'quota'
    except (DeliveryError, user.__class__.DoesNotExist):
        return 'unavailable'  # Includes existing uncertain/reserved receipts and DB contention.
