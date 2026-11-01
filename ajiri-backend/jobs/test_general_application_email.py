from datetime import timedelta
from unittest.mock import patch

from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from profiles.models import Profile
from .application_dispatch import dispatch
from .brevo_transport import BrevoTransport, Result
from .delivery_service import DeliveryError
from .general_application_email import AuthorizedTransport
from .models import DeliveryAttempt, JobPublication
from .send_authorization import plan_response
from . import test_delivery_service as fixtures


@override_settings(REAL_EMAIL_ENABLED=True, ACCOUNT_SECURITY_EMAIL_ENABLED=True,
    GENERAL_APPLICATION_EMAIL_ENABLED=True, APPLICATION_EMAIL_ENABLED=True,
    JOB_FRESHNESS_ENFORCED=True, EMAIL_DELIVERY_MODE='account_security',
    ACCOUNT_EMAIL_TEST_CAPTURE=False, EMAIL_PLATFORM_FROM='platform@example.invalid',
    BREVO_TIMEOUT_SECONDS=10, ACCOUNT_LINK_ORIGIN='https://example.invalid',
    BREVO_API_KEY='synthetic-test-only', EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class GeneralApplicationTests(TransactionTestCase):
    application = fixtures.DeliveryServiceTests.application
    authorization = fixtures.DeliveryServiceTests.authorization

    def setUp(self):
        fixtures.DeliveryServiceTests.setUp(self)
        # Fixture creation only; the actual dispatcher always enforces publication.
        with override_settings(JOB_FRESHNESS_ENFORCED=False):
            self.app = self.application()
        self.user.refresh_from_db()
        self.auth = self.app.test_authorization
        self.publication = JobPublication.objects.create(job=self.app.job, origin='rss', status='published',
            confirmed_at=timezone.now(), closes_at=timezone.now()+timedelta(days=1))
        sender = patch.object(BrevoTransport, 'send', return_value=Result('accepted', '<synthetic>'))
        self.send = sender.start()
        self.addCleanup(sender.stop)

    def test_exact_authorization_accepts_once_and_reconciles_after_disable(self):
        self.assertTrue(plan_response(self.user, self.app)['dispatch_enabled'])
        self.assertEqual(dispatch(self.user, self.auth).state, 'accepted')
        with override_settings(GENERAL_APPLICATION_EMAIL_ENABLED=False, APPLICATION_EMAIL_ENABLED=False):
            self.assertEqual(dispatch(self.user, self.auth).state, 'accepted')
        self.send.assert_called_once()
        self.assertEqual(DeliveryAttempt.objects.count(), 1)

    def test_unknown_handoff_reconciles_without_provider_retry(self):
        self.send.return_value = Result('unknown', failure_category='timeout')
        self.assertEqual(dispatch(self.user, self.auth).state, 'unknown')
        self.assertEqual(dispatch(self.user, self.auth).state, 'unknown')
        self.send.assert_called_once()

    def test_expired_vacancy_or_changed_verified_mailbox_blocks_before_budget(self):
        self.publication.closes_at = timezone.now()-timedelta(seconds=1)
        self.publication.save()
        with self.assertRaises(DeliveryError):
            dispatch(self.user, self.auth)
        self.publication.closes_at = timezone.now()+timedelta(days=1)
        self.publication.save()
        Profile.objects.filter(user=self.user).update(verified_email='changed@example.invalid')
        self.user.refresh_from_db()
        with self.assertRaises(DeliveryError):
            dispatch(self.user, self.auth)
        self.send.assert_not_called()
        self.assertFalse(DeliveryAttempt.objects.exists())

    def test_deadline_change_at_final_boundary_records_failure_without_provider(self):
        original = AuthorizedTransport.send

        def expire(sink, payload):
            JobPublication.objects.filter(pk=self.publication.pk).update(closes_at=timezone.now()-timedelta(seconds=1))
            return original(sink, payload)

        with patch.object(AuthorizedTransport, 'send', expire):
            self.assertEqual(dispatch(self.user, self.auth).state, 'definite_failure')
        self.send.assert_not_called()
        self.assertEqual(DeliveryAttempt.objects.count(), 1)
