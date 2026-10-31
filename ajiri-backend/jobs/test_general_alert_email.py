import uuid
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from profiles.alert_consent import record_choice
from .brevo_transport import BrevoTransport, Result
from .general_alert_email import deliver
from .models import DeliveryAttempt, DeliveryDailyBudget, Job, JobPublication, Notification


@override_settings(REAL_EMAIL_ENABLED=True, ACCOUNT_SECURITY_EMAIL_ENABLED=True,
    GENERAL_ALERT_EMAIL_ENABLED=True, ALERT_EMAIL_ENABLED=True, JOB_FRESHNESS_ENFORCED=True,
    EMAIL_DELIVERY_MODE='account_security', ACCOUNT_EMAIL_TEST_CAPTURE=False,
    EMAIL_PLATFORM_FROM='platform@example.invalid', BREVO_TIMEOUT_SECONDS=10,
    ACCOUNT_LINK_ORIGIN='https://example.invalid', BREVO_API_KEY='synthetic-test-only',
    EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class GeneralAlertTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='match@example.invalid', password='Synthetic-only!')
        profile = self.user.profile
        profile.email_verified_at = timezone.now()
        profile.verified_email = self.user.email
        profile.notify_in_app = False
        profile.save()
        record_choice(self.user, True, uuid.uuid4())
        self.job = Job.objects.create(title='Synthetic match', company_name='Synthetic test',
            description='Synthetic only', source_url='https://example.invalid/job', source_name='test')
        self.publication = JobPublication.objects.create(job=self.job, origin='rss', status='published',
            confirmed_at=timezone.now(), closes_at=timezone.now()+timedelta(days=1))
        self.notification = Notification.objects.create(user=self.user, job=self.job, match_score=70, in_app=False)
        sender = patch.object(BrevoTransport, 'send', return_value=Result('accepted', '<synthetic>'))
        self.send = sender.start()
        self.addCleanup(sender.stop)

    def test_exact_threshold_shared_budget_idempotency_and_in_app_independence(self):
        self.assertEqual(deliver(self.notification.pk), 'accepted')
        self.assertEqual(deliver(self.notification.pk), 'accepted')
        self.send.assert_called_once()
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').alert_reserved, 1)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.notify_in_app)
        payload = self.send.call_args.args[0]
        self.assertIn(b'/unsubscribe#token=', payload)
        self.assertNotIn(b'attachment', payload)

    def test_unknown_never_retries_and_batch_skips_existing_receipts(self):
        self.send.return_value = Result('unknown', failure_category='timeout')
        self.assertEqual(deliver(self.notification.pk), 'unknown')
        self.assertEqual(deliver(self.notification.pk), 'unknown')
        call_command('deliver_match_emails', stdout=StringIO())
        self.send.assert_called_once()

    def test_revoked_or_stale_or_low_score_never_reserves(self):
        self.publication.confirmed_at = timezone.now()-timedelta(days=2)
        self.publication.save()
        self.assertEqual(deliver(self.notification.pk), 'ineligible')
        self.publication.confirmed_at = timezone.now()
        self.publication.save()
        Notification.objects.filter(pk=self.notification.pk).update(match_score=69)
        self.assertEqual(deliver(self.notification.pk), 'ineligible')
        Notification.objects.filter(pk=self.notification.pk).update(match_score=100)
        record_choice(self.user, False, uuid.uuid4())
        self.assertEqual(deliver(self.notification.pk), 'ineligible')
        self.send.assert_not_called()
        self.assertFalse(DeliveryAttempt.objects.exists())

    def test_disabled_command_and_disabled_freshness_never_send(self):
        for values in ({'GENERAL_ALERT_EMAIL_ENABLED': False}, {'JOB_FRESHNESS_ENFORCED': False}):
            with self.subTest(values=values), override_settings(**values):
                self.assertEqual(deliver(self.notification.pk), 'disabled')
                call_command('deliver_match_emails', stdout=StringIO())
        self.send.assert_not_called()
        self.assertFalse(DeliveryAttempt.objects.exists())

    def test_consent_withdrawal_after_reservation_blocks_provider(self):
        from .general_alert_email import AlertTransport
        original = AlertTransport.prepare

        def revoke(sink, **kwargs):
            payload = original(sink, **kwargs)
            record_choice(self.user, False, uuid.uuid4())
            return payload

        with patch.object(AlertTransport, 'prepare', revoke):
            self.assertEqual(deliver(self.notification.pk), 'unavailable')
        self.send.assert_not_called()
        self.assertFalse(DeliveryAttempt.objects.exists())
