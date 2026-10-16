"""Fail-closed owner pilot; no provider calls or credential reads while disabled.

see docs/CONCEPTS.md#owner-email-pilot
"""
import json
from dataclasses import dataclass
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import validate_email

from jobs.brevo_transport import BrevoTransport
from jobs.delivery_service import DeliveryError


@dataclass(frozen=True)
class Pilot:
    owner_id: int
    recipient: str
    sender: str
    limit: int
    timeout: int


def configuration():
    if not getattr(settings, 'REAL_EMAIL_ENABLED', False):
        return None
    try:
        owner = int(settings.EMAIL_PILOT_OWNER_ID)
        recipient = settings.EMAIL_PILOT_RECIPIENT
        sender = settings.EMAIL_PLATFORM_FROM
        limit = int(settings.EMAIL_PILOT_DAILY_LIMIT)
        timeout = int(settings.BREVO_TIMEOUT_SECONDS)
        for address in (recipient, sender):
            validate_email(address)
            if address != address.strip() or '\r' in address or '\n' in address or '*' in address:
                raise ValueError
        origin = urlsplit(settings.ACCOUNT_LINK_ORIGIN)
        if (settings.EMAIL_DELIVERY_MODE != 'owner_pilot' or owner <= 0
            or not 1 <= limit <= 5 or not 1 <= timeout <= 60
            or settings.ACCOUNT_EMAIL_TEST_CAPTURE
            or settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend'
            or origin.scheme != 'https' or not origin.hostname or origin.username
            or origin.password or origin.path not in ('', '/') or origin.query or origin.fragment):
            raise ValueError
        key = getattr(settings, 'BREVO_API_KEY', '')
        if not isinstance(key, str) or not key or key != key.strip() or '\n' in key or '\r' in key:
            raise ValueError
        return Pilot(owner, recipient.casefold(), sender, limit, timeout)
    except (AttributeError, TypeError, ValueError, ValidationError):
        raise ImproperlyConfigured('Owner email pilot configuration is invalid.') from None


def eligible(user, purpose):
    policy = configuration()
    return policy is not None and purpose in ('password_reset', 'email_verification') and (
        user.is_active and user.pk == policy.owner_id and user.email.casefold() == policy.recipient)


class PilotTransport:
    def __init__(self, policy, transport):
        self.policy = policy
        self.transport = transport

    def prepare(self, **kwargs):
        if (kwargs['recipient'].casefold() != self.policy.recipient
            or kwargs.get('attachments') or kwargs.get('reply_to')):
            raise DeliveryError('Pilot recipient or message is not allowed.')
        return self.transport.prepare(**kwargs)

    def send(self, payload):
        # Check again at the last boundary: never accept CC/BCC or arbitrary payloads.
        message = json.loads(payload)
        if (configuration() != self.policy or set(message) != {'sender', 'to', 'subject', 'textContent'}
            or message['to'] != [{'email': self.policy.recipient}]
            or message['sender'] != {'email': self.policy.sender, 'name': 'Ajiri'}):
            raise DeliveryError('Pilot message is not allowed.')
        return self.transport.send(payload)


def transport(policy):
    # Michael supplies the private runtime credential; never include it in errors.
    key = getattr(settings, 'BREVO_API_KEY', '')
    if not key or not isinstance(key, str) or key != key.strip() or '\n' in key or '\r' in key:
        raise ImproperlyConfigured('Owner email pilot credential is unavailable.')
    return PilotTransport(policy, BrevoTransport(api_key=key, sender=policy.sender, timeout=policy.timeout, sender_name='Ajiri'))
