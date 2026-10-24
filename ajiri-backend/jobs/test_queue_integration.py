"""Queue tests reuse real authorization/quota/receipt code with captured provider IO."""
from datetime import timedelta
from contextlib import nullcontext
import uuid
from unittest.mock import patch

from django.test import TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from . import test_delivery_service as fixtures
from .brevo_transport import Result
from .delivery_service import DeliveryError
from .application_packages import PackageConflict
from .package_review import PackageUnavailable
from .models import ApplicationSendAuthorization, DeliveryAttempt, DeliveryDailyBudget
from .pilot_test_helpers import prepared_pilot, pilot_settings
from .queue_test_integration import ApplicationEnvelope, InlineTestQueue, execute_application
from .send_authorization import authorize, plan_response, withdraw


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
                   EMAIL_PLATFORM_FROM='platform@example.invalid')
class QueueIntegrationTests(TransactionTestCase):
    setUp = fixtures.DeliveryServiceTests.setUp

    def fixture(self):
        from profiles.models import CVApproval
        existing = CVApproval.objects.filter(profile__user=self.user).first()
        with patch('jobs.pilot_test_helpers.approved_cv', return_value=existing) if existing else nullcontext():
            app, package = prepared_pilot(self.user)
        preview = plan_response(self.user, app)
        auth = authorize(self.user, app.pk, {'request_key': uuid.uuid4(), 'package_id': package.pk,
            'expected_revision': 1, 'plan_sha256': preview['plan_sha256'], 'authorization': True})[0]
        envelope = ApplicationEnvelope(self.user.pk, auth.pk)
        queue = InlineTestQueue()
        queue.enqueue(envelope)
        return app, auth, queue, envelope

    def enabled(self):
        return override_settings(**pilot_settings(self.user), DELIVERY_QUEUE_TEST_CAPTURE=True)

    @patch('jobs.brevo_transport.BrevoTransport.send', return_value=Result('accepted', '<synthetic@invalid>'))
    def test_duplicate_messages_share_the_authorization_receipt_and_quota(self, provider):
        with self.enabled():
            app, auth, queue, envelope = self.fixture()
            queue.enqueue(envelope)
            first = queue.execute(envelope)
            second = queue.execute(envelope)
            self.assertEqual(first.pk, second.pk)
            self.assertEqual(DeliveryAttempt.objects.filter(application=app).count(), 1)
            self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').application_reserved, 1)
        provider.assert_called_once()

    @patch('jobs.brevo_transport.BrevoTransport.send')
    def test_default_closed_before_any_budget_or_provider_use(self, provider):
        with self.enabled():
            _, _, queue, envelope = self.fixture()
        with self.assertRaises(DeliveryError):
            queue.execute(envelope)
        self.assertFalse(DeliveryAttempt.objects.exists())
        self.assertFalse(DeliveryDailyBudget.objects.exists())
        provider.assert_not_called()

    @patch('jobs.brevo_transport.BrevoTransport.send')
    def test_delay_with_withdrawal_or_expiry_cannot_send(self, provider):
        with self.enabled():
            for revoked in ('withdraw', 'expire'):
                app, auth, queue, envelope = self.fixture()
                if revoked == 'withdraw':
                    withdraw(self.user, app.pk, auth.pk)
                else:
                    ApplicationSendAuthorization.objects.filter(pk=auth.pk).update(
                        authorized_at=timezone.now()-timedelta(days=2),
                        expires_at=timezone.now()-timedelta(seconds=1))
                with self.assertRaises((DeliveryError, PackageConflict)):
                    queue.execute(envelope)
        self.assertFalse(DeliveryAttempt.objects.exists())
        provider.assert_not_called()

    @patch('jobs.brevo_transport.BrevoTransport.send', return_value=Result('unknown', failure_category='transport'))
    def test_unknown_receipt_replay_never_repeats_handoff(self, provider):
        with self.enabled():
            _, _, queue, envelope = self.fixture()
            self.assertEqual(queue.execute(envelope).state, 'unknown')
            self.assertEqual(queue.execute(envelope).state, 'unknown')
        provider.assert_called_once()

    @patch('jobs.brevo_transport.BrevoTransport.send', return_value=Result('accepted', '<synthetic@invalid>'))
    def test_crash_after_handoff_before_ack_reconciles_same_receipt(self, provider):
        with self.enabled():
            _, _, queue, envelope = self.fixture()

            def crash_after(message):
                execute_application(message)
                raise RuntimeError('Synthetic worker exit before acknowledgement')

            with self.assertRaises(RuntimeError):
                queue.execute(envelope, crash_after)
            with self.assertRaises(DeliveryError):
                queue.execute(envelope)
            receipt = queue.execute(envelope, reconcile=True)
            self.assertEqual(receipt.state, 'accepted')
            self.assertEqual(DeliveryAttempt.objects.count(), 1)
        provider.assert_called_once()

    @patch('jobs.brevo_transport.BrevoTransport.send', return_value=Result('accepted', '<synthetic@invalid>'))
    def test_crash_before_handoff_retains_identity_and_requires_reconciliation(self, provider):
        with self.enabled():
            _, _, queue, envelope = self.fixture()
            with self.assertRaises(RuntimeError):
                queue.execute(envelope, lambda _: (_ for _ in ()).throw(RuntimeError('Synthetic crash')))
            provider.assert_not_called()
            self.assertFalse(DeliveryAttempt.objects.exists())
            self.assertEqual(queue.execute(envelope, reconcile=True).state, 'accepted')
        provider.assert_called_once()

    @patch('jobs.brevo_transport.BrevoTransport.send')
    def test_other_owner_and_missing_authorization_fail_without_provider_call(self, provider):
        with self.enabled():
            _, auth, _, _ = self.fixture()
            other = get_user_model().objects.create_user(email='other-queue@example.invalid')
            for envelope in (ApplicationEnvelope(other.pk, auth.pk), ApplicationEnvelope(self.user.pk, uuid.uuid4())):
                with self.assertRaises(DeliveryError):
                    execute_application(envelope)
        self.assertFalse(DeliveryAttempt.objects.exists())
        provider.assert_not_called()

    @patch('jobs.brevo_transport.BrevoTransport.send', return_value=Result('accepted', '<synthetic@invalid>'))
    def test_another_queued_authorization_cannot_bypass_pilot_quota(self, provider):
        with self.enabled():
            _, _, first_queue, first = self.fixture()
            _, _, second_queue, second = self.fixture()
            self.assertEqual(first_queue.execute(first).state, 'accepted')
            with self.assertRaises(DeliveryError):
                second_queue.execute(second)
            self.assertEqual(DeliveryAttempt.objects.count(), 1)
            self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').application_reserved, 1)
        provider.assert_called_once()

    @patch('jobs.brevo_transport.BrevoTransport.send')
    def test_changed_package_evidence_is_rechecked_after_queue_delay(self, provider):
        from .models import ApplicationPackage
        with self.enabled():
            _, auth, queue, envelope = self.fixture()
            ApplicationPackage.objects.filter(pk=auth.document_approval.package_id).update(content_sha256='0'*64)
            with self.assertRaises((DeliveryError, PackageConflict, PackageUnavailable)):
                queue.execute(envelope)
        self.assertFalse(DeliveryAttempt.objects.exists())
        provider.assert_not_called()
