from io import StringIO
import json
import uuid
from urllib.parse import urlsplit, parse_qs
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from profiles.alert_consent import record_choice, unsubscribe
from .alert_delivery import deliver_match, SYNTHETIC_SOURCE
from .brevo_transport import Result
from .models import Job, Notification, DeliveryAttempt, DeliveryDailyBudget


class AlertDeliveryTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='owner-alert@example.invalid', password='Synthetic-only-123')
        self.other = get_user_model().objects.create_user(email='other-alert@example.invalid', password='Synthetic-only-456')
        p = self.user.profile
        p.email_verified_at = timezone.now(); p.verified_email = self.user.email; p.save()
        record_choice(self.user, True, uuid.uuid4()); p.refresh_from_db()
        self.settings_override = override_settings(REAL_EMAIL_ENABLED=True, ALERT_EMAIL_ENABLED=True,
            EMAIL_DELIVERY_MODE='owner_pilot', EMAIL_PILOT_OWNER_ID=str(self.user.pk), EMAIL_PILOT_RECIPIENT=self.user.email,
            EMAIL_PLATFORM_FROM='platform@example.invalid', EMAIL_PILOT_DAILY_LIMIT=5, BREVO_TIMEOUT_SECONDS=10,
            ACCOUNT_LINK_ORIGIN='https://app.example.invalid', ACCOUNT_EMAIL_TEST_CAPTURE=False,
            EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend', BREVO_API_KEY='synthetic-placeholder')
        self.settings_override.enable(); self.addCleanup(self.settings_override.disable)
        self.job = Job.objects.create(title='Ajiri synthetic alert pilot', company_name='Synthetic example',
            description='Synthetic', source_name=SYNTHETIC_SOURCE, is_active=False,
            source_url=f'https://example.invalid/ajiri-owner-alert-pilot/{self.user.pk}/{uuid.uuid4()}')
        self.notification = Notification.objects.create(user=self.user, job=self.job, match_score=100,in_app=False)

    def test_disabled_does_not_read_credentials_and_ingestion_cannot_send(self):
        with override_settings(ALERT_EMAIL_ENABLED=False), patch('accounts.pilot.configuration') as config:
            self.assertFalse(deliver_match(self.notification,explicit_owner_pilot=True)); config.assert_not_called()
        with patch('jobs.brevo_transport.BrevoTransport.send') as send:
            self.assertFalse(deliver_match(self.notification));send.assert_not_called()
        self.assertEqual(DeliveryAttempt.objects.count(),0)

    def test_shared_ledger_one_provider_call_and_confirmed_unsubscribe(self):
        captured=[]
        def send(payload):
            captured.append(json.loads(payload));return Result('accepted','<synthetic-alert>')
        with patch('jobs.brevo_transport.BrevoTransport.send',side_effect=send):
            self.assertTrue(deliver_match(self.notification,explicit_owner_pilot=True))
            self.notification.refresh_from_db()
            self.assertFalse(deliver_match(self.notification,explicit_owner_pilot=True))
        self.assertEqual(len(captured),1)
        self.assertEqual(DeliveryAttempt.objects.get().state,'accepted')
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').alert_reserved,1)
        self.assertEqual(captured[0]['to'],[{'email':self.user.email}])
        self.assertEqual(set(captured[0]),{'sender','to','subject','textContent','htmlContent'})
        link=captured[0]['textContent'].split()[-1]
        self.assertEqual(urlsplit(link).query,'')
        token=parse_qs(urlsplit(link).fragment)['token'][0]
        unsubscribe(token,confirm=False);self.user.profile.refresh_from_db();self.assertTrue(self.user.profile.notify_email)
        unsubscribe(token,confirm=True);self.user.profile.refresh_from_db();self.assertFalse(self.user.profile.notify_email)
        self.assertTrue(self.user.profile.notify_in_app)

    def test_real_job_other_owner_missing_consent_and_unverified_address_never_send(self):
        with patch('jobs.brevo_transport.BrevoTransport.send') as send:
            self.job.is_active=True;self.job.save()
            self.assertFalse(deliver_match(self.notification,explicit_owner_pilot=True))
            self.job.is_active=False;self.job.save()
            record_choice(self.user,False,uuid.uuid4())
            self.assertFalse(deliver_match(self.notification,explicit_owner_pilot=True))
            record_choice(self.user,True,uuid.uuid4())
            profile=self.user.profile;profile.refresh_from_db();profile.verified_email='different@example.invalid';profile.save()
            self.assertFalse(deliver_match(self.notification,explicit_owner_pilot=True))
            self.notification.user=self.other
            self.assertFalse(deliver_match(self.notification,explicit_owner_pilot=True));send.assert_not_called()
        self.assertEqual(DeliveryAttempt.objects.count(),0)

    def test_unknown_and_definite_failure_never_automatically_retry_or_claim_sent(self):
        for state in ('unknown','definite_failure'):
            with self.subTest(state=state):
                DeliveryAttempt.objects.all().delete();DeliveryDailyBudget.objects.all().delete()
                with patch('jobs.brevo_transport.BrevoTransport.send',return_value=Result(state,failure_category='transport')) as send:
                    self.assertFalse(deliver_match(self.notification,explicit_owner_pilot=True))
                    self.assertFalse(deliver_match(self.notification,explicit_owner_pilot=True))
                    self.assertEqual(send.call_count,1)
                self.notification.refresh_from_db();self.assertFalse(self.notification.sent_email)

    def test_quota_shared_with_security_mail_and_no_preference_fallback(self):
        from zoneinfo import ZoneInfo
        day=timezone.now().astimezone(ZoneInfo('Africa/Nairobi')).date()
        DeliveryDailyBudget.objects.create(scope='global',day=day,account_reserved=5)
        with patch('jobs.brevo_transport.BrevoTransport.send') as send:
            self.assertFalse(deliver_match(self.notification,explicit_owner_pilot=True));send.assert_not_called()
        self.assertEqual(DeliveryAttempt.objects.count(),0)

    def test_command_prepares_hidden_test_and_requires_explicit_handoff(self):
        out=StringIO()
        with patch('jobs.brevo_transport.BrevoTransport.send') as send:
            call_command('owner_alert_pilot',prepare=True,stdout=out);send.assert_not_called()
            hidden=Notification.objects.exclude(pk=self.notification.pk).get()
            self.assertFalse(hidden.job.is_active);self.assertFalse(hidden.in_app)
            with self.assertRaises(CommandError):call_command('owner_alert_pilot',notification_id=hidden.pk)

    def test_revocation_after_reservation_prevents_provider_handoff(self):
        from .delivery_service import DeliveryService
        original=DeliveryService._reserve
        def reserve(service,*args,**kwargs):
            result=original(service,*args,**kwargs)
            record_choice(self.user,False,uuid.uuid4())
            return result
        with patch.object(DeliveryService,'_reserve',reserve),patch('jobs.brevo_transport.BrevoTransport.send') as send:
            self.assertFalse(deliver_match(self.notification,explicit_owner_pilot=True));send.assert_not_called()
        self.assertEqual(DeliveryAttempt.objects.get().state,'definite_failure')
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').alert_reserved,1)
