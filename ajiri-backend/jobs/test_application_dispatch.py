"""HTTP pilot integration uses synthetic accounts and a captured fake provider only."""
import json
import uuid
from unittest.mock import patch
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import User
from profiles.models import Profile
from .models import Job, ApplicationSendAuthorization as Authorization, DeliveryAttempt, DeliveryDailyBudget
from .send_authorization import plan_response, authorize, withdraw
from .pilot_test_helpers import prepared_pilot, pilot_settings
from .brevo_transport import Result
from . import test_delivery_service as fixtures


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    EMAIL_PLATFORM_FROM='platform@example.invalid')
class ApplicationDispatchTests(TransactionTestCase):
    setUp = fixtures.DeliveryServiceTests.setUp

    def fixture(self):
        with self.pilot():
            return self.enabled_fixture()

    def enabled_fixture(self):
        app, package = prepared_pilot(self.user)
        preview = plan_response(self.user, app)
        auth = authorize(self.user, app.pk, {'request_key': uuid.uuid4(), 'package_id': package.pk,
            'expected_revision': 1, 'plan_sha256': preview['plan_sha256'], 'authorization': True})[0]
        return app, auth

    def pilot(self, **changes):
        values = pilot_settings(self.user)
        values.update(changes)
        return override_settings(**values)

    def client_for(self, user=None):
        client = APIClient(); client.force_authenticate(user or self.user); return client

    def url(self, app, auth):
        return f'/api/jobs/applications/{app.pk}/send-authorizations/{auth.pk}/dispatch/'

    def test_default_off_does_not_read_account_provider_configuration_or_claim_budget(self):
        app, auth = self.fixture()
        with patch('jobs.application_dispatch.account_pilot.configuration') as account:
            response = self.client_for().post(self.url(app, auth), {}, format='json')
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.data['code'], 'application_sending_disabled')
            account.assert_not_called()
        self.assertFalse(DeliveryAttempt.objects.exists())
        self.assertFalse(DeliveryDailyBudget.objects.exists())

    def test_accepted_dispatch_reconciles_without_repeat_even_after_disabled(self):
        app, auth = self.fixture()
        client = self.client_for()
        with self.pilot(), patch('jobs.brevo_transport.BrevoTransport.send', return_value=Result('accepted', '<synthetic@invalid>')) as send:
            self.assertTrue(client.get(f'/api/jobs/applications/{app.pk}/send-plan/').data['dispatch_enabled'])
            response = client.post(self.url(app, auth), {}, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['attempt']['state'], 'accepted')
            payload = json.loads(send.call_args.args[0])
            self.assertEqual(payload['to'], [{'email': self.user.email}])
            self.assertEqual(payload['replyTo'], {'email': self.user.email})
            self.assertEqual(len(payload['attachment']), 2)
            self.assertNotIn('cc', payload); self.assertNotIn('bcc', payload)
            self.assertEqual(client.post(self.url(app, auth), {}, format='json').data['attempt']['state'], 'accepted')
            send.assert_called_once()
        with patch('jobs.brevo_transport.BrevoTransport.send') as send:
            self.assertEqual(client.post(self.url(app, auth), {}, format='json').data['attempt']['state'], 'accepted')
            send.assert_not_called()
        self.assertEqual(DeliveryAttempt.objects.count(), 1)
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').application_reserved, 1)

    def test_real_jobs_wrong_owner_changed_mailbox_and_withdrawal_have_zero_provider_calls(self):
        app, auth = self.fixture()
        with self.pilot(), patch('jobs.brevo_transport.BrevoTransport.send') as send:
            for change in ({'is_active': True}, {'source_name': 'real feed'}, {'application_email': 'employer@example.invalid'}):
                original = {key: getattr(app.job, key) for key in change}
                Job.objects.filter(pk=app.job_id).update(**change)
                self.assertEqual(self.client_for().post(self.url(app, auth), {}, format='json').status_code, 409)
                Job.objects.filter(pk=app.job_id).update(**original)
            other = User.objects.create_user(email='other@example.invalid')
            self.assertEqual(self.client_for(other).post(self.url(app, auth), {}, format='json').status_code, 404)
            Profile.objects.filter(user=self.user).update(email_verified_at=None)
            self.assertEqual(self.client_for().post(self.url(app, auth), {}, format='json').status_code, 409)
            Profile.objects.filter(user=self.user).update(email_verified_at=timezone.now())
            withdraw(self.user, app.pk, auth.pk)
            self.assertEqual(self.client_for().post(self.url(app, auth), {}, format='json').status_code, 409)
            send.assert_not_called()
        self.assertFalse(DeliveryAttempt.objects.exists())

    def test_unknown_outcome_never_repeats_and_invalid_review_flag_blocks(self):
        app, auth = self.fixture()
        with self.pilot(APPLICATION_PILOT_LIMIT_REVIEW=''), patch('jobs.brevo_transport.BrevoTransport.send') as send:
            self.assertEqual(self.client_for().post(self.url(app, auth), {}, format='json').status_code, 409)
            send.assert_not_called()
        with self.pilot(), patch('jobs.brevo_transport.BrevoTransport.send', return_value=Result('unknown', failure_category='transport')) as send:
            for _ in range(2):
                response = self.client_for().post(self.url(app, auth), {}, format='json')
                self.assertEqual(response.data['attempt']['state'], 'unknown')
            send.assert_called_once()
            self.assertEqual(Authorization.objects.get(pk=auth.pk).state, 'dispatch_started')

    def test_synthetic_job_stays_out_of_public_jobs_and_matching(self):
        from .matching import notify_matching_profiles
        app, auth = self.fixture()
        with self.pilot(), patch('jobs.brevo_transport.BrevoTransport.send') as send:
            self.assertEqual(self.client_for().get(f'/api/jobs/{app.job_id}/').status_code, 404)
            listed = self.client_for().get('/api/jobs/').data['results']
            self.assertNotIn(app.job_id, [row['id'] for row in listed])
            self.assertEqual(notify_matching_profiles(app.job), 0)
            self.assertTrue(self.client_for().get(f'/api/jobs/applications/{app.pk}/send-plan/').data['dispatch_enabled'])
            send.assert_not_called()
        self.assertFalse(DeliveryAttempt.objects.exists())

    def test_inflight_http_replay_reads_reserved_receipt_without_second_handoff(self):
        import threading
        from concurrent.futures import ThreadPoolExecutor
        from django.db import close_old_connections
        entered, release = threading.Event(), threading.Event()
        app, auth = self.fixture()

        def provider(payload):
            entered.set()
            if not release.wait(10):
                raise TimeoutError('Synthetic handoff timed out')
            return Result('accepted', '<synthetic@invalid>')

        def first_request():
            close_old_connections()
            try:
                return self.client_for().post(self.url(app, auth), {}, format='json')
            finally:
                close_old_connections()

        with self.pilot(), patch('jobs.brevo_transport.BrevoTransport.send', side_effect=provider) as send:
            with ThreadPoolExecutor(max_workers=1) as worker:
                future = worker.submit(first_request)
                try:
                    self.assertTrue(entered.wait(5))
                    replay = self.client_for().post(self.url(app, auth), {}, format='json')
                    self.assertEqual(replay.status_code, 200)
                    self.assertEqual(replay.data['attempt']['state'], 'reserved')
                    send.assert_called_once()
                finally:
                    release.set()
                completed = future.result(timeout=10)
                self.assertEqual(completed.status_code, 200)
                self.assertEqual(completed.data['attempt']['state'], 'accepted')
                self.assertEqual(completed.data['attempt']['id'], replay.data['attempt']['id'])
        self.assertEqual(DeliveryAttempt.objects.count(), 1)
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').application_reserved, 1)

    def test_owner_revoked_after_reservation_stops_before_provider(self):
        from .delivery_service import DeliveryService
        app, auth = self.fixture()
        original = DeliveryService._reserve

        def revoke(service, *args, **kwargs):
            result = original(service, *args, **kwargs)
            User.objects.filter(pk=self.user.pk).update(is_active=False)
            return result

        with self.pilot(), patch.object(DeliveryService, '_reserve', revoke), patch('jobs.brevo_transport.BrevoTransport.send') as send:
            response = self.client_for().post(self.url(app, auth), {}, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['attempt']['state'], 'definite_failure')
            send.assert_not_called()
        self.assertEqual(DeliveryAttempt.objects.get().failure_category, 'configuration')

    def test_account_messages_share_the_pilot_budget_before_application(self):
        from zoneinfo import ZoneInfo
        app, auth = self.fixture()
        DeliveryDailyBudget.objects.create(scope='global', day=timezone.now().astimezone(ZoneInfo('Africa/Nairobi')).date(),
            account_reserved=5)
        with self.pilot(), patch('jobs.brevo_transport.BrevoTransport.send') as send:
            response = self.client_for().post(self.url(app, auth), {}, format='json')
            self.assertEqual(response.status_code, 409)
            send.assert_not_called()
        self.assertFalse(DeliveryAttempt.objects.exists())
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').application_reserved, 0)

    def test_operator_preparation_is_dry_run_by_default_and_never_approves_or_sends(self):
        import io
        from django.core.management import call_command
        from django.core.management.base import CommandError
        from profiles.models import CVApproval
        from .models import Application, ApplicationPackage
        with self.assertRaises(CommandError):
            call_command('prepare_owner_application_pilot', stdout=io.StringIO())
        self.assertFalse(Job.objects.exists())
        with self.pilot(), patch('jobs.brevo_transport.BrevoTransport.send') as send:
            call_command('prepare_owner_application_pilot', stdout=io.StringIO())
            self.assertFalse(Job.objects.exists())
            for _ in range(2):
                call_command('prepare_owner_application_pilot', create=True, stdout=io.StringIO())
            self.assertEqual(Job.objects.count(), 1)
            self.assertFalse(Job.objects.get().is_active)
            self.assertEqual(Application.objects.count(), 1)
            self.assertFalse(ApplicationPackage.objects.exists())
            self.assertFalse(CVApproval.objects.exists())
            self.assertFalse(Authorization.objects.exists())
            self.assertFalse(DeliveryAttempt.objects.exists())
            send.assert_not_called()
