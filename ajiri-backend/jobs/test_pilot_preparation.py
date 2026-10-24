"""Personal review can complete while the provider transport stays disabled."""
from io import StringIO
import uuid
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient

from profiles.models import CVApproval, Profile
from . import test_delivery_service as fixtures
from .application_dispatch import configuration, preparation_configuration, editable_pilot
from .application_packages import require_editable, PackageConflict
from .models import Application, Job, DeliveryAttempt, DeliveryDailyBudget, ApplicationPackageApproval, ApplicationSendAuthorization
from .pilot_test_helpers import pilot_settings, prepared_pilot
from .send_authorization import authorize, plan_response


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
                   EMAIL_PLATFORM_FROM='platform@example.invalid')
class PilotPreparationTests(TransactionTestCase):
    setUp = fixtures.DeliveryServiceTests.setUp

    def preparation(self, **changes):
        values = pilot_settings(self.user)
        values.update(APPLICATION_EMAIL_ENABLED=False, APPLICATION_PILOT_PREPARATION_ENABLED=True)
        values.update(changes)
        return override_settings(**values)

    def test_default_off_does_not_read_provider_configuration(self):
        with override_settings(APPLICATION_EMAIL_ENABLED=False, APPLICATION_PILOT_PREPARATION_ENABLED=False), \
                patch('jobs.application_dispatch.account_pilot.configuration') as provider:
            self.assertIsNone(configuration())
            self.assertIsNone(preparation_configuration())
            provider.assert_not_called()

    @patch('jobs.brevo_transport.BrevoTransport.send')
    def test_documents_and_exact_authorization_can_be_reviewed_while_dispatch_is_closed(self, provider):
        with self.preparation():
            app, package = prepared_pilot(self.user)
            self.assertTrue(editable_pilot(app))
            self.assertIsNone(configuration())
            preview = plan_response(self.user, app)
            auth = authorize(self.user, app.pk, {'request_key': uuid.uuid4(), 'package_id': package.pk,
                'expected_revision': 1, 'plan_sha256': preview['plan_sha256'], 'authorization': True})[0]
            client = APIClient(); client.force_authenticate(self.user)
            plan = client.get(f'/api/jobs/applications/{app.pk}/send-plan/')
            self.assertEqual(plan.status_code, 200)
            self.assertFalse(plan.data['dispatch_enabled'])
            response = client.post(f'/api/jobs/applications/{app.pk}/send-authorizations/{auth.pk}/dispatch/', {}, format='json')
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.data['code'], 'application_sending_disabled')
            self.assertFalse(DeliveryAttempt.objects.exists())
            self.assertFalse(DeliveryDailyBudget.objects.exists())
            provider.assert_not_called()

    @patch('jobs.brevo_transport.BrevoTransport.send')
    def test_preparation_command_is_idempotent_without_approval_or_email(self, provider):
        with self.preparation():
            for _ in range(2):
                call_command('prepare_owner_application_pilot', create=True, stdout=StringIO())
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(Application.objects.count(), 1)
        self.assertFalse(Job.objects.get().is_active)
        for model in (CVApproval, ApplicationPackageApproval, ApplicationSendAuthorization, DeliveryAttempt, DeliveryDailyBudget):
            self.assertEqual(model.objects.count(), 0)
        provider.assert_not_called()

    def test_changed_unverified_mailbox_blocks_preparation_before_writes(self):
        Profile.objects.filter(user=self.user).update(email_verified_at=None)
        with self.preparation(), self.assertRaises(CommandError):
            call_command('prepare_owner_application_pilot', create=True, stdout=StringIO())
        self.assertFalse(Job.objects.exists())
        self.assertFalse(Application.objects.exists())

    def test_real_vacancy_cannot_use_the_synthetic_preparation_exception(self):
        with self.preparation():
            app, _ = prepared_pilot(self.user)
            app.job.source_name = 'real-source'
            app.job.save(update_fields=['source_name'])
            self.assertFalse(editable_pilot(app))
            with self.assertRaises(PackageConflict):
                require_editable(app)

    def test_disabling_preparation_preserves_existing_documents_and_reviews(self):
        with self.preparation():
            app, package = prepared_pilot(self.user)
        with override_settings(APPLICATION_EMAIL_ENABLED=False, APPLICATION_PILOT_PREPARATION_ENABLED=False):
            self.assertFalse(editable_pilot(app))
            with self.assertRaises(PackageConflict):
                require_editable(app)
        self.assertEqual(Application.objects.get(pk=app.pk).status, 'ready_for_review')
        self.assertEqual(ApplicationPackageApproval.objects.filter(package=package).count(), 1)
        self.assertFalse(DeliveryAttempt.objects.exists())
