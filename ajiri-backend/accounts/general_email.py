"""Inactive general account-security delivery using the shared receipt ledger.

see docs/CONCEPTS.md#general-account-security-email
"""
import json
from dataclasses import dataclass
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import validate_email

from jobs.brevo_transport import BrevoTransport
from jobs.delivery_service import DeliveryError


@dataclass(frozen=True)
class Configuration:
    sender: str
    timeout: int


def configuration():
    if not getattr(settings, 'ACCOUNT_SECURITY_EMAIL_ENABLED', False):
        return None
    try:
        sender = settings.EMAIL_PLATFORM_FROM
        validate_email(sender)
        timeout = int(settings.BREVO_TIMEOUT_SECONDS)
        origin = urlsplit(settings.ACCOUNT_LINK_ORIGIN)
        key = getattr(settings, 'BREVO_API_KEY', '')
        if (not settings.REAL_EMAIL_ENABLED or settings.EMAIL_DELIVERY_MODE != 'account_security'
                or settings.ACCOUNT_EMAIL_TEST_CAPTURE
                or settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend'
                or sender != sender.strip() or any(c in sender for c in '\r\n*')
                or not 1 <= timeout <= 60 or origin.scheme != 'https' or not origin.hostname
                or origin.username or origin.password or origin.path not in ('', '/')
                or origin.query or origin.fragment or not isinstance(key, str)
                or not key or key != key.strip() or any(c in key for c in '\r\n')):
            raise ValueError
        return Configuration(sender, timeout)
    except (AttributeError, TypeError, ValueError, ValidationError):
        raise ImproperlyConfigured('Account security email configuration is invalid.') from None


def eligible(user, purpose):
    return (configuration() is not None and user.is_active
            and purpose in ('password_reset', 'email_verification'))


class AccountTransport:
    def __init__(self, policy, user, purpose):
        self.policy = policy
        self.user_id = user.pk
        self.recipient = user.email.casefold()
        self.purpose = purpose
        self.transport = BrevoTransport(api_key=settings.BREVO_API_KEY,
            sender=policy.sender, timeout=policy.timeout, sender_name='Ajiri')

    def prepare(self, **kwargs):
        if (kwargs['recipient'].casefold() != self.recipient
                or kwargs.get('attachments') or kwargs.get('reply_to')):
            raise DeliveryError('Account security message is not allowed.')
        return self.transport.prepare(**kwargs)

    def send(self, payload):
        # Re-read the mailbox and switches immediately before the one provider call.
        user = get_user_model().objects.filter(pk=self.user_id, is_active=True).first()
        message = json.loads(payload)
        if (configuration() != self.policy or user is None
                or not eligible(user, self.purpose) or user.email.casefold() != self.recipient
                or set(message) != {'sender', 'to', 'subject', 'textContent'}
                or message['to'] != [{'email': self.recipient}]
                or message['sender'] != {'email': self.policy.sender, 'name': 'Ajiri'}):
            raise DeliveryError('Account security eligibility changed before handoff.')
        return self.transport.send(payload)
