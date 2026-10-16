import json
import threading
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import close_old_connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from jobs.brevo_transport import BrevoTransport, Result
from jobs.delivery_service import DeliveryError
from jobs.models import DeliveryAttempt, DeliveryDailyBudget
from .checks import check_email_pilot
from .pilot import configuration, transport
from .recovery import capture_link


# Synthetic data only. Every provider send is intercepted; no SMTP/API traffic.
@override_settings(REAL_EMAIL_ENABLED=True, EMAIL_DELIVERY_MODE='owner_pilot',
    EMAIL_PILOT_OWNER_ID=1, EMAIL_PILOT_RECIPIENT='owner@example.invalid',
    EMAIL_PLATFORM_FROM='platform@example.invalid', EMAIL_PILOT_DAILY_LIMIT=5,
    BREVO_TIMEOUT_SECONDS=10, BREVO_API_KEY='synthetic-test-only',
    ACCOUNT_EMAIL_TEST_CAPTURE=False, ACCOUNT_LINK_ORIGIN='https://example.invalid',
    EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PilotTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(pk=1, email='owner@example.invalid', password='Synthetic-test-2026!')
        self.other = get_user_model().objects.create_user(pk=2, email='other@example.invalid', password='Synthetic-test-2026!')
        self.sender = patch.object(BrevoTransport, 'send', return_value=Result('accepted', '<synthetic>'))
        self.send = self.sender.start()
        self.addCleanup(self.sender.stop)

    def deliver(self, purpose='email_verification', key=None, user=None):
        return capture_link(user or self.owner, purpose, key or uuid.uuid4())

    def test_disabled_does_not_construct_transport_generate_token_or_write(self):
        with override_settings(REAL_EMAIL_ENABLED=False), patch('accounts.recovery.verification_token') as token:
            self.assertEqual(self.deliver(), 'disabled')
        token.assert_not_called()
        self.send.assert_not_called()
        self.assertFalse(DeliveryAttempt.objects.exists())
        self.assertFalse(DeliveryDailyBudget.objects.exists())

    def test_invalid_configuration_fails_without_sensitive_output(self):
        for values in ({'EMAIL_PILOT_OWNER_ID': ''}, {'EMAIL_DELIVERY_MODE': 'all'},
            {'EMAIL_PILOT_RECIPIENT': '*@example.invalid'}, {'EMAIL_PILOT_DAILY_LIMIT': 6},
            {'EMAIL_PILOT_DAILY_LIMIT': 0}, {'BREVO_API_KEY': ''},
            {'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend'},
            {'ACCOUNT_EMAIL_TEST_CAPTURE': True}, {'ACCOUNT_LINK_ORIGIN': 'http://example.invalid'},
            {'EMAIL_PLATFORM_FROM': 'bad\r\naddress'}, {'BREVO_TIMEOUT_SECONDS': 61}):
            with self.subTest(values=list(values)), override_settings(**values):
                with self.assertRaises(ImproperlyConfigured):
                    self.deliver()
                errors = check_email_pilot(None)
                self.assertEqual(errors[0].id, 'accounts.E001')
                self.assertNotIn('synthetic-test-only', str(errors))
        self.send.assert_not_called()
        self.assertFalse(DeliveryDailyBudget.objects.exists())

    def test_non_owner_or_changed_address_rejected_before_link_creation(self):
        with patch('accounts.recovery.verification_token') as token:
            self.assertEqual(self.deliver(user=self.other), 'disabled')
            self.owner.email = 'changed@example.invalid'
            self.assertEqual(self.deliver(), 'disabled')
            self.owner.email = 'owner@example.invalid'
            self.assertEqual(self.deliver(purpose='application'), 'disabled')
        token.assert_not_called()
        self.send.assert_not_called()
        self.assertFalse(DeliveryDailyBudget.objects.exists())

    def test_owner_delivery_and_duplicate_identity(self):
        key = uuid.uuid4()
        self.owner.email = 'OWNER@example.invalid'
        get_user_model().objects.filter(pk=1).update(email=self.owner.email)
        self.assertEqual(self.deliver(key=key), 'accepted')
        self.assertEqual(self.deliver(key=key), 'accepted')
        self.assertEqual(self.send.call_count, 1)
        payload = json.loads(self.send.call_args.args[0])
        self.assertEqual(payload['to'], [{'email': 'owner@example.invalid'}])
        self.assertEqual(payload['sender'], {'email': 'platform@example.invalid', 'name': 'Ajiri'})
        self.assertNotIn('bcc', payload)
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').account_reserved, 1)

    def test_shared_five_attempt_cap_and_prior_nonpilot_usage(self):
        for index in range(5):
            self.assertEqual(self.deliver(purpose='password_reset' if index % 2 else 'email_verification'), 'accepted')
        self.assertEqual(self.deliver(), 'quota')
        self.assertEqual(self.send.call_count, 5)
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').account_reserved, 5)

    def test_failure_consumes_capacity_and_unknown_never_retries(self):
        self.send.return_value = Result('definite_failure', failure_category='provider_rejected')
        self.assertEqual(self.deliver(), 'definite_failure')
        self.assertEqual(self.deliver(), 'definite_failure')
        self.send.return_value = Result('unknown', failure_category='timeout')
        self.assertEqual(self.deliver(), 'unknown')
        self.assertEqual(self.deliver(), 'unavailable')
        self.assertEqual(self.send.call_count, 3)
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').account_reserved, 3)

    def test_prior_usage_counts_and_new_day_resets_capacity(self):
        from zoneinfo import ZoneInfo
        now = timezone.now()
        today = now.astimezone(ZoneInfo('Africa/Nairobi')).date()
        DeliveryDailyBudget.objects.create(scope='global', day=today, application_reserved=5)
        self.assertEqual(self.deliver(), 'quota')
        self.send.assert_not_called()
        with patch('jobs.delivery_service.timezone.now', return_value=now + timedelta(days=1)):
            self.assertEqual(self.deliver(), 'accepted')
        self.assertEqual(self.send.call_count, 1)

    def test_no_account_link_is_printed_and_nonowner_verification_is_truthful(self):
        with patch('builtins.print') as output:
            self.assertEqual(self.deliver(purpose='password_reset'), 'accepted')
        output.assert_not_called()
        client = APIClient()
        client.force_authenticate(self.other)
        with patch('accounts.throttles.EndpointThrottle.get_rate', return_value='1000/day'):
            response = client.post('/api/accounts/verification/request/', {})
        self.assertEqual(response.status_code, 202)
        self.assertFalse(response.data['delivery_available'])
        self.assertIn('No email was sent', response.data['detail'])
        self.assertEqual(self.send.call_count, 1)

    def test_boundary_rejects_modified_recipient_cc_and_shutdown(self):
        sink = transport(configuration())
        payload = sink.prepare(recipient='owner@example.invalid', subject='Test', text='Synthetic')
        message = json.loads(payload)
        for change in ({'to': [{'email': 'other@example.invalid'}]}, {'cc': [{'email': 'owner@example.invalid'}]}):
            with self.assertRaises(DeliveryError):
                sink.send(json.dumps({**message, **change}).encode())
        with override_settings(REAL_EMAIL_ENABLED=False), self.assertRaises(DeliveryError):
            sink.send(payload)
        self.send.assert_not_called()

    def test_public_reset_non_owner_has_same_response(self):
        with patch('accounts.throttles.EndpointThrottle.get_rate', return_value='1000/day'):
            client = APIClient()
            results = [client.post('/api/accounts/password-reset/request/', {'email': email})
                for email in ('owner@example.invalid', 'other@example.invalid', 'absent@example.invalid')]
        self.assertTrue(all((r.status_code, r.data) == (results[0].status_code, results[0].data) for r in results))
        self.assertEqual(self.send.call_count, 1)

    def test_concurrent_last_slot_is_atomic(self):
        for _ in range(4):
            self.assertEqual(self.deliver(), 'accepted')
        gate = threading.Barrier(2)
        outcomes = []
        def worker():
            close_old_connections()
            try:
                user = get_user_model().objects.get(pk=1)
                gate.wait(timeout=10)
                outcomes.append(self.deliver(user=user))
            finally:
                close_old_connections()
        workers = [threading.Thread(target=worker) for _ in range(2)]
        for worker_thread in workers:
            worker_thread.start()
        for worker_thread in workers:
            worker_thread.join(timeout=15)
        self.assertFalse(any(worker_thread.is_alive() for worker_thread in workers))
        self.assertCountEqual(outcomes, ['accepted', 'quota'])
        self.assertEqual(self.send.call_count, 5)
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').account_reserved, 5)
