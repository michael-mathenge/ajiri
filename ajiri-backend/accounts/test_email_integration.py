from datetime import datetime, timezone as dt_timezone
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import caches
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from jobs.brevo_transport import Result
from jobs.models import DeliveryAttempt as Attempt, DeliveryDailyBudget as Budget
from profiles.models import Profile
from .email_delivery import MemoryTransport, deliver_account_link, next_day_wait
from .recovery import capture_link


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', ACCOUNT_EMAIL_TEST_CAPTURE=True)
class AccountEmailIntegrationTests(TransactionTestCase):
    def setUp(self):
        for cache in caches.all():
            cache.clear()
        self.user = get_user_model().objects.create_user(email='integration@example.invalid', password='Synthetic-river-2027!')
        self.client = APIClient()
        mail.get_connection()
        rate = patch('accounts.throttles.EndpointThrottle.get_rate', return_value='1000/day')
        rate.start()
        self.addCleanup(rate.stop)

    def reset(self, key=None, email=None):
        return self.client.post('/api/accounts/password-reset/request/',
            {'email': email or self.user.email, 'request_id': str(key or uuid.uuid4())})

    def verify(self, key=None):
        self.client.force_authenticate(self.user)
        return self.client.post('/api/accounts/verification/request/', {'request_id': str(key or uuid.uuid4())})

    def test_reset_and_verification_write_account_receipts_and_shared_budget(self):
        self.assertEqual(self.reset().status_code, 202)
        self.assertEqual(self.verify().status_code, 202)
        self.assertCountEqual(Attempt.objects.values_list('channel', flat=True), ['password_reset', 'email_verification'])
        self.assertEqual(Budget.objects.get(scope='global').account_reserved, 2)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 0)
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue(all(row.state == 'accepted' for row in Attempt.objects.all()))
        for attempt in Attempt.objects.all():
            stored = str(attempt.__dict__)
            self.assertNotIn('integration@example.invalid', stored)
            self.assertNotIn('Use this account link', stored)
            self.assertNotIn('#token=', stored)
        Profile.objects.filter(user=self.user).update(email_verified_at=timezone.now(), verified_email=self.user.email)
        self.assertEqual(self.verify().status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(Budget.objects.get(scope='global').account_reserved, 2)

    def test_duplicate_identity_produces_one_capture_and_one_budget_charge(self):
        key = uuid.uuid4()
        self.assertEqual(self.reset(key).status_code, 202)
        self.assertEqual(self.reset(key).status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Attempt.objects.count(), 1)
        self.assertEqual(Budget.objects.get(scope='global').account_reserved, 1)

    def test_public_reset_masks_failure_unknown_quota_and_nonexistent_account(self):
        with patch('accounts.email_delivery.MemoryTransport.send', return_value=Result('unknown', failure_category='timeout')) as send:
            uncertain = self.reset()
            repeated = self.reset()
            absent = self.reset(email='absent@example.invalid')
        self.assertEqual((uncertain.status_code, uncertain.data), (absent.status_code, absent.data))
        self.assertEqual(repeated.data, absent.data)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(Budget.objects.get(scope='global').account_reserved, 1)
        self.assertEqual(Attempt.objects.get().state, 'unknown')
        self.assertIn('Check your inbox', uncertain.data['detail'])
        self.assertNotIn('request_id', uncertain.data)

    def test_private_verification_exposes_uncertainty_without_retry(self):
        with patch('accounts.email_delivery.MemoryTransport.send', return_value=Result('unknown', failure_category='timeout')) as send:
            first = self.verify()
            second = self.verify()
        self.assertEqual(first.status_code, 409)
        self.assertEqual(second.status_code, 409)
        self.assertIn('Reconciliation', first.data['detail'])
        self.assertEqual(send.call_count, 1)

    def test_definite_failure_counts_and_only_new_explicit_request_retries(self):
        key = uuid.uuid4()
        with patch('accounts.email_delivery.MemoryTransport.send', return_value=Result('definite_failure', failure_category='provider_rejected')) as send:
            self.assertEqual(self.verify(key).status_code, 502)
            self.assertEqual(self.verify(key).status_code, 502)
            self.assertEqual(send.call_count, 1)
            self.assertEqual(self.verify().status_code, 502)
            self.assertEqual(send.call_count, 2)
        self.assertEqual(Budget.objects.get(scope='global').account_reserved, 2)

    def test_thirty_account_messages_shared_purposes_and_no_allocation_borrowing(self):
        for number in range(30):
            purpose = 'password_reset' if number % 2 else 'email_verification'
            self.assertEqual(capture_link(self.user, purpose, uuid.uuid4()), 'accepted')
        response = self.verify()
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(Budget.objects.get(scope='global').account_reserved, 30)
        self.assertEqual(Attempt.objects.count(), 30)
        self.assertEqual(len(mail.outbox), 30)
        public = self.reset()
        absent = self.reset(email='absent@example.invalid')
        self.assertEqual(public.data, absent.data)
        self.assertEqual(public.status_code, 202)
        self.assertEqual(len(mail.outbox), 30)

    @override_settings(ACCOUNT_EMAIL_TEST_CAPTURE=False)
    def test_disabled_creates_no_token_mail_transport_or_accounting(self):
        with patch('accounts.recovery.default_token_generator.make_token') as token, patch('accounts.email_delivery.MemoryTransport') as transport:
            self.assertFalse(self.reset().data['delivery_available'])
            self.assertFalse(self.verify().data['delivery_available'])
        token.assert_not_called()
        transport.assert_not_called()
        self.assertFalse(Attempt.objects.exists())
        self.assertFalse(Budget.objects.exists())
        self.assertEqual(mail.outbox, [])

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
    def test_test_flag_cannot_activate_smtp_or_brevo(self):
        with patch('django.core.mail.EmailMessage.send') as mail_send, patch('jobs.brevo_transport.build_opener') as network:
            self.assertFalse(self.reset().data['delivery_available'])
            self.assertFalse(self.verify().data['delivery_available'])
        mail_send.assert_not_called()
        network.assert_not_called()
        self.assertFalse(Attempt.objects.exists())

    def test_unknown_account_and_malformed_request_id_never_spend(self):
        self.assertEqual(self.reset(email='absent@example.invalid').status_code, 202)
        self.assertEqual(self.client.post('/api/accounts/password-reset/request/',
            {'email': self.user.email, 'request_id': 'invalid'}).status_code, 400)
        self.assertFalse(Budget.objects.exists())

    def test_nairobi_midnight_wait_not_server_timezone(self):
        with patch('accounts.email_delivery.timezone.now', return_value=datetime(2026, 10, 16, 20, 59, 30, tzinfo=dt_timezone.utc)):
            self.assertEqual(next_day_wait(), 31)

    @override_settings(ACCOUNT_LINK_ORIGIN='https://user:password@example.invalid')
    def test_invalid_origin_does_not_generate_account_receipts_or_send(self):
        with patch('django.core.mail.EmailMessage.send') as send:
            self.assertEqual(self.verify().status_code, 409)
        send.assert_not_called()
        self.assertFalse(Budget.objects.exists())

    def test_bridge_rejects_non_account_channel(self):
        with self.assertRaises(ValueError):
            deliver_account_link(self.user, 'application', 'synthetic', uuid.uuid4())
        self.assertFalse(Budget.objects.exists())

    def test_memory_sink_pins_connection_even_if_settings_change_after_gate(self):
        payload = MemoryTransport().prepare(recipient=self.user.email, subject='Synthetic', text='Synthetic body')
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'):
            with patch('accounts.email_delivery.available', return_value=True), patch('django.core.mail.backends.smtp.EmailBackend.open') as network:
                result = MemoryTransport().send(payload)
        network.assert_not_called()
        self.assertEqual(result.state, 'accepted')
        self.assertEqual(len(mail.outbox), 1)
