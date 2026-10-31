"""Synthetic identities and intercepted provider calls only."""
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TransactionTestCase, override_settings

from jobs.brevo_transport import BrevoTransport, Result
from jobs.delivery_service import DeliveryError
from jobs.models import DeliveryAttempt, DeliveryDailyBudget
from .checks import check_email_pilot
from .general_email import AccountTransport, configuration
from .recovery import capture_link


@override_settings(REAL_EMAIL_ENABLED=True, ACCOUNT_SECURITY_EMAIL_ENABLED=True,
    EMAIL_DELIVERY_MODE='account_security', ACCOUNT_EMAIL_TEST_CAPTURE=False,
    EMAIL_PLATFORM_FROM='platform@example.invalid', BREVO_TIMEOUT_SECONDS=10,
    ACCOUNT_LINK_ORIGIN='https://example.invalid', BREVO_API_KEY='synthetic-test-only',
    EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class GeneralAccountEmailTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='member@example.invalid', password='Synthetic-only-2026!')
        self.sender = patch.object(BrevoTransport, 'send', return_value=Result('accepted', '<synthetic>'))
        self.send = self.sender.start()
        self.addCleanup(self.sender.stop)

    def deliver(self, key=None):
        return capture_link(self.user, 'email_verification', key or uuid.uuid4())

    def test_non_pilot_owner_uses_shared_budget_once_per_request(self):
        key = uuid.uuid4()
        self.assertEqual(self.deliver(key), 'accepted')
        self.assertEqual(self.deliver(key), 'accepted')
        self.send.assert_called_once()
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').account_reserved, 1)
        self.assertEqual(DeliveryAttempt.objects.count(), 1)
        self.assertEqual(check_email_pilot(None), [])

    def test_unknown_handoff_blocks_new_request_without_retry(self):
        self.send.return_value = Result('unknown', failure_category='timeout')
        self.assertEqual(self.deliver(), 'unknown')
        self.assertEqual(self.deliver(), 'unavailable')
        self.send.assert_called_once()

    def test_disabled_does_not_generate_link_or_reserve(self):
        with override_settings(ACCOUNT_SECURITY_EMAIL_ENABLED=False, REAL_EMAIL_ENABLED=False):
            self.assertEqual(self.deliver(), 'disabled')
        self.send.assert_not_called()
        self.assertFalse(DeliveryAttempt.objects.exists())

    def test_invalid_configuration_fails_closed_with_safe_error(self):
        for values in ({'REAL_EMAIL_ENABLED': False}, {'EMAIL_DELIVERY_MODE': 'owner_pilot'},
                       {'ACCOUNT_LINK_ORIGIN': 'http://example.invalid'},
                       {'ACCOUNT_EMAIL_TEST_CAPTURE': True}, {'BREVO_TIMEOUT_SECONDS': 61},
                       {'EMAIL_PLATFORM_FROM': 'bad\n@example.invalid'}):
            with self.subTest(values=values), override_settings(**values):
                with self.assertRaises(ImproperlyConfigured):
                    configuration()
                self.assertEqual(len(check_email_pilot(None)), 1)
        self.send.assert_not_called()

    def test_handoff_rechecks_active_owner_mailbox_switch_and_payload(self):
        sink = AccountTransport(configuration(), self.user, 'password_reset')
        payload = sink.prepare(recipient=self.user.email, subject='Security', text='Synthetic')
        for values in ({'is_active': False}, {'email': 'changed@example.invalid'}):
            with self.subTest(values=values):
                get_user_model().objects.filter(pk=self.user.pk).update(**values)
                with self.assertRaises(DeliveryError):
                    sink.send(payload)
                get_user_model().objects.filter(pk=self.user.pk).update(is_active=True, email=self.user.email)
        with override_settings(ACCOUNT_SECURITY_EMAIL_ENABLED=False):
            with self.assertRaises(DeliveryError):
                sink.send(payload)
        with self.assertRaises(DeliveryError):
            sink.send(payload[:-1] + b', "bcc": []}')
        self.send.assert_not_called()

    def test_security_mail_cannot_attach_documents_or_override_recipient(self):
        sink = AccountTransport(configuration(), self.user, 'email_verification')
        for extra in ({'recipient': 'other@example.invalid'}, {'attachments': [('cv.pdf', b'bytes')]},
                      {'reply_to': 'other@example.invalid'}):
            with self.subTest(extra=extra), self.assertRaises(DeliveryError):
                sink.prepare(**({'recipient': self.user.email, 'subject': 'Security', 'text': 'Synthetic'} | extra))
        self.send.assert_not_called()
