import base64
from datetime import timedelta
import json
import threading
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import close_old_connections, transaction
from django.test import TransactionTestCase, SimpleTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from profiles.cv_builder import content_hash
from profiles.models import Profile
from .application_packages import save_package, context, PackageConflict
from .application_pilot import ApplicationPilot, ApplicationPilotTransport
from .brevo_transport import Result
from .delivery_service import DeliveryError, DeliveryService, QuotaExceeded
from .models import (ApplicationSendAuthorization as Authorization, ApplicationSendAttemptLink as Link,
                     DeliveryAttempt, DeliveryDailyBudget as Budget)
from .send_authorization import (authorize, withdraw, plan_response, dispatch_inputs, authorization_data)
from . import test_delivery_service as fixtures


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
                   EMAIL_PLATFORM_FROM='platform@example.invalid')
class SendAuthorizationTests(TransactionTestCase):
    setUp = fixtures.DeliveryServiceTests.setUp
    application = fixtures.DeliveryServiceTests.application
    authorization = fixtures.DeliveryServiceTests.authorization
    deliver = fixtures.DeliveryServiceTests.deliver

    def client_for(self, user=None):
        client = APIClient()
        client.force_authenticate(user or self.user)
        return client

    def input(self, app, **changes):
        preview = plan_response(self.user, app, changes.get('retry_of'))
        data = {'request_key': str(uuid.uuid4()), 'package_id': preview['plan']['package_id'],
            'expected_revision': 1, 'plan_sha256': preview['plan_sha256'], 'authorization': True}
        data.update(changes)
        return data

    def base(self, app):
        return f'/api/jobs/applications/{app.pk}/'

    def dispatch(self, app, auth=None, **changes):
        auth = auth or Authorization.objects.get(pk=app.test_authorization.pk)
        args = dict(user_id=self.user.pk, channel='application', application_id=app.pk,
            authorization_id=auth.pk, idempotency_key=auth.pk, retry_of=auth.retry_of_id)
        args.update(dispatch_inputs(self.user, auth))
        args.update(changes)
        return self.service.deliver(**args)

    def test_plan_exact_saved_bytes_names_and_read_only_no_mail_or_budgets(self):
        app = self.application()
        self.user.full_name = '  José / Long Name\x01  '
        self.user.save()
        with patch('jobs.brevo_transport.BrevoTransport.send') as send:
            response = self.client_for().get(self.base(app)+'send-plan/')
            self.assertEqual(response.status_code, 200)
            plan = response.data['plan']
            self.assertEqual(plan['attachments'][0]['filename'], 'Jose_Long_Name_CV_Example.docx')
            self.assertEqual(plan['recipient'], app.application_email)
            self.assertEqual(plan['reply_to'], self.user.email)
            self.assertFalse(plan['copy_to_self'])
            self.assertFalse(response.data['dispatch_enabled'])
            self.assertEqual(content_hash(plan), response.data['plan_sha256'])
            self.assertEqual(len(plan['attachments']), 2)
            self.assertNotIn('application-packages/', str(plan))
            send.assert_not_called()
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertFalse(Budget.objects.exists())
        self.assertFalse(DeliveryAttempt.objects.exists())
        self.assertEqual(Authorization.objects.count(), 1)

    def test_explicit_creation_and_replay_closed_record_before_changed_eligibility(self):
        app = self.application()
        withdraw(self.user, app.pk, app.test_authorization.pk)
        client, url = self.client_for(), self.base(app)+'send-authorizations/'
        data = self.input(app)
        first = client.post(url, data, format='json')
        self.assertEqual(first.status_code, 201)
        self.assertEqual(client.post(url, data, format='json').status_code, 200)
        auth = Authorization.objects.get(pk=first.data['id'])
        self.assertEqual(auth.expires_at - auth.authorized_at, timedelta(hours=24))
        withdraw(self.user, app.pk, auth.pk)
        Profile.objects.filter(user=self.user).update(email_verified_at=None)
        replay = client.post(url, data, format='json')
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.data['state'], 'withdrawn')
        self.assertEqual(client.get(url, {'request_key': data['request_key']}).data['id'], str(auth.pk))
        changed = {**data, 'plan_sha256': '0'*64}
        self.assertEqual(client.post(url, changed, format='json').status_code, 409)
        self.assertFalse(Budget.objects.exists())

    def test_types_unknown_fields_and_duplicate_active_authorization(self):
        app = self.application()
        client, url = self.client_for(), self.base(app)+'send-authorizations/'
        data = self.input(app)
        self.assertEqual(client.post(url, data, format='json').status_code, 409)
        for change in ({'authorization': False}, {'authorization': 'true'}, {'authorization': 1},
                       {'expected_revision': True}, {'recipient': 'other@example.invalid'}, {'copy_to_self': True}):
            self.assertEqual(client.post(url, {**data, **change}, format='json').status_code, 400)
        self.assertEqual(Authorization.objects.count(), 1)
        self.assertFalse(Budget.objects.exists())

    def test_get_expiry_has_no_write_and_replacement_closes_old_evidence(self):
        app = self.application()
        auth = app.test_authorization
        later = auth.expires_at + timedelta(seconds=1)
        with patch('jobs.send_authorization.timezone.now', return_value=later):
            self.assertEqual(authorization_data(auth)['state'], 'expired')
            auth.refresh_from_db()
            self.assertEqual(auth.state, 'authorized')
            replacement = self.authorization(app)
            self.assertNotEqual(replacement.pk, auth.pk)
        auth.refresh_from_db()
        self.assertEqual(auth.state, 'expired')
        self.assertEqual(auth.closed_at, later)

    def test_withdrawal_idempotent_and_never_dispatches(self):
        app = self.application()
        auth = app.test_authorization
        url = self.base(app)+f'send-authorizations/{auth.pk}/withdraw/'
        client = self.client_for()
        self.assertEqual(client.post(url, {}, format='json').data['state'], 'withdrawn')
        closed = Authorization.objects.get(pk=auth.pk).closed_at
        self.assertEqual(client.post(url, {}, format='json').status_code, 200)
        self.assertEqual(Authorization.objects.get(pk=auth.pk).closed_at, closed)
        with self.assertRaises(PackageConflict):
            self.dispatch(app)
        self.assertEqual(self.transport.calls, [])
        self.assertFalse(Budget.objects.exists())

    def test_dispatch_requires_auth_exact_key_and_complete_payload_before_reservation(self):
        app = self.application()
        for change in ({'authorization_id': None}, {'idempotency_key': uuid.uuid4()},
                       {'subject': 'Changed'}, {'text': 'Changed'},
                       {'attachments': [('CV.docx', b'changed')]}, {'recipient': self.user.email}):
            with self.assertRaises((DeliveryError, PackageConflict, ValueError)):
                self.dispatch(app, **change)
        self.assertEqual(self.transport.calls, [])
        self.assertFalse(Budget.objects.exists())

    def test_exact_dispatch_receipt_replay_and_cutoff_survive_file_and_mailbox_edits(self):
        app = self.application()
        auth = app.test_authorization
        inputs = dispatch_inputs(self.user, auth)
        attempt = self.dispatch(app)
        self.assertEqual(attempt.state, 'accepted')
        self.assertEqual(authorization_data(auth)['state'], 'dispatch_started')
        frozen = json.loads(self.transport.calls[0])
        for item, (_, expected) in zip(frozen['attachment'], inputs['attachments']):
            self.assertEqual(base64.b64decode(item['content']), expected)
        auth.refresh_from_db()
        self.assertEqual(auth.state, 'dispatch_started')
        self.assertEqual(Link.objects.get().attempt, attempt)
        with self.assertRaises(PackageConflict):
            withdraw(self.user, app.pk, auth.pk)
        package = app.packages.get()
        package.cv_document.storage.delete(package.cv_document.name)
        Profile.objects.filter(user=self.user).update(email_verified_at=None)
        self.service.enabled = False
        replay = self.service.deliver(user_id=self.user.pk, channel='application', application_id=app.pk,
            authorization_id=auth.pk, idempotency_key=auth.pk, recipient='', subject='', text='')
        self.assertEqual(replay.pk, attempt.pk)
        response = self.client_for().post(self.base(app)+f'send-authorizations/{auth.pk}/dispatch/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['attempt']['state'], 'accepted')
        self.assertEqual(len(self.transport.calls), 1)
        app.refresh_from_db()
        self.assertEqual(app.status, 'ready_for_review')

    def test_disabled_endpoint_even_when_global_real_email_setting_is_true(self):
        app = self.application()
        with override_settings(REAL_EMAIL_ENABLED=True, APPLICATION_EMAIL_ENABLED=True), \
                patch('jobs.brevo_transport.BrevoTransport.send') as send:
            response = self.client_for().post(self.base(app)+f'send-authorizations/{app.test_authorization.pk}/dispatch/', {}, format='json')
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.data['code'], 'application_sending_disabled')
            send.assert_not_called()
        self.assertFalse(Budget.objects.exists())
        self.assertEqual(Authorization.objects.get().state, 'authorized')

    def test_new_package_atomically_supersedes_active_authorization(self):
        app = self.application()
        package = app.packages.get()
        save_package(self.user, app.pk, {'cv_version': package.cv_approval_id, 'expected_revision': 1,
            'context_sha256': content_hash(context(app)), 'letter_text': 'Changed exact letter',
            'email_subject': 'Synthetic', 'email_body': 'Changed body'})
        self.assertEqual(Authorization.objects.get().state, 'superseded')
        with self.assertRaises(PackageConflict):
            self.dispatch(app)
        self.assertEqual(self.transport.calls, [])

    def test_job_mailbox_name_sender_and_file_changes_invalidate_permission(self):
        app = self.application()
        for field, value in [('title', 'New title'), ('application_email', 'changed@example.invalid'),
                             ('application_method', 'external_link'), ('is_active', False), ('is_flagged_scam', True)]:
            original = getattr(app.job, field)
            setattr(app.job, field, value); app.job.save()
            with self.assertRaises(PackageConflict):
                self.dispatch(app)
            setattr(app.job, field, original); app.job.save()
        self.user.full_name = 'Changed name'; self.user.save()
        with self.assertRaises(PackageConflict):
            self.dispatch(app)
        self.user.full_name = ''; self.user.save()
        with override_settings(EMAIL_PLATFORM_FROM='changed@example.invalid'):
            with self.assertRaises(PackageConflict):
                self.dispatch(app)
        Profile.objects.filter(user=self.user).update(verified_email='old@example.invalid')
        with self.assertRaises(PackageConflict):
            self.dispatch(app)
        self.assertFalse(Budget.objects.exists())

    def test_corrupt_immutable_plan_and_in_transaction_payload_change_are_blocked(self):
        app = self.application()
        auth = app.test_authorization
        Authorization.objects.filter(pk=auth.pk).update(plan_sha256='0'*64)
        with self.assertRaises(PackageConflict):
            self.dispatch(app)
        Authorization.objects.filter(pk=auth.pk).update(plan_sha256=auth.plan_sha256)
        original = self.service._reserve
        def changed(*args):
            Profile.objects.filter(user=self.user).update(email_verified_at=None)
            return original(*args)
        with patch.object(self.service, '_reserve', side_effect=changed):
            with self.assertRaises(DeliveryError):
                self.dispatch(app)
        self.assertFalse(Budget.objects.exists())
        self.assertEqual(Authorization.objects.get().state, 'authorized')

    def test_one_explicit_retry_no_chains_or_forks_and_failures_consume_quota(self):
        app = self.application()
        object.__setattr__(self.transport, 'result', Result('definite_failure', failure_category='provider_rejected'))
        first = self.dispatch(app)
        retry = self.authorization(app, first.pk)
        second = self.dispatch(app, retry)
        self.assertEqual(Link.objects.get(attempt=second).previous_attempt_id, first.pk)
        for previous in (None, first.pk, second.pk):
            with self.assertRaises(PackageConflict):
                self.authorization(app, previous)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 2)

    def test_owner_404_no_store_and_no_unknown_mutation_fields(self):
        app = self.application()
        other = get_user_model().objects.create_user(email='other@example.invalid', password='synthetic')
        routes = ['send-plan/', 'send-authorizations/', f'send-authorizations/{app.test_authorization.pk}/']
        client = self.client_for(other)
        for route in routes:
            response = client.get(self.base(app)+route)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response['Cache-Control'], 'private, no-store')
        for action in ('withdraw', 'dispatch'):
            self.assertEqual(client.post(self.base(app)+f'send-authorizations/{app.test_authorization.pk}/{action}/', {}, format='json').status_code, 404)
        owner = self.client_for()
        url = self.base(app)+f'send-authorizations/{app.test_authorization.pk}/withdraw/'
        self.assertEqual(owner.post(url, {'send': True}, format='json').status_code, 400)
        response = owner.head(self.base(app)+'send-plan/')
        self.assertEqual(response.content, b'')
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_real_sqlite_withdrawal_writer_wins_before_reservation(self):
        app = self.application()
        auth = app.test_authorization
        args = dispatch_inputs(self.user, auth)
        locked, release = threading.Event(), threading.Event()
        failures = []
        def writer():
            close_old_connections()
            try:
                with transaction.atomic():
                    withdraw(self.user, app.pk, auth.pk)
                    locked.set()
                    if not release.wait(10):
                        raise RuntimeError('Release timed out')
            except Exception as error:
                failures.append(type(error).__name__)
            finally:
                close_old_connections()
        thread = threading.Thread(target=writer)
        original = self.service._reserve
        def reserve(*values):
            thread.start()
            self.assertTrue(locked.wait(10))
            release.set(); thread.join(10)
            return original(*values)
        try:
            with patch.object(self.service, '_reserve', side_effect=reserve):
                with self.assertRaises(DeliveryError):
                    self.service.deliver(user_id=self.user.pk, channel='application', application_id=app.pk,
                        authorization_id=auth.pk, idempotency_key=auth.pk, **args)
        finally:
            release.set()
            if thread.ident:
                thread.join(10)
        self.assertEqual(failures, [])
        self.assertFalse(Budget.objects.exists())
        self.assertEqual(self.transport.calls, [])

    def test_application_pilot_capacity_one_per_day_shared_with_accounts(self):
        self.service.pilot = ApplicationPilot(self.user.pk, 'employer@example.invalid', self.user.email,
            'platform@example.invalid', 6000000, 'Synthetic test review only')
        first, second = self.application(), self.application()
        self.dispatch(first)
        with self.assertRaises(QuotaExceeded):
            self.dispatch(second)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 1)
        self.assertEqual(Authorization.objects.get(pk=second.test_authorization.pk).state, 'authorized')
        self.assertEqual(len(self.transport.calls), 1)

    def test_save_wins_after_preflight_and_blocks_dispatch_without_quota(self):
        app = self.application()
        package = app.packages.get()
        original = self.service._reserve
        def save_first(*args):
            save_package(self.user, app.pk, {'cv_version': package.cv_approval_id, 'expected_revision': 1,
                'context_sha256': content_hash(context(app)), 'letter_text': 'New reviewed text needed',
                'email_subject': 'Synthetic', 'email_body': 'New draft'})
            return original(*args)
        with patch.object(self.service, '_reserve', side_effect=save_first):
            with self.assertRaises(DeliveryError):
                self.dispatch(app)
        self.assertEqual(Authorization.objects.get().state, 'superseded')
        self.assertFalse(Budget.objects.exists())
        self.assertEqual(self.transport.calls, [])

    def test_dispatch_wins_and_prevents_withdrawal_or_new_package_during_provider_call(self):
        app = self.application()
        package = app.packages.get()
        def send(payload):
            self.assertFalse(transaction.get_connection().in_atomic_block)
            self.assertEqual(Authorization.objects.get().state, 'dispatch_started')
            with self.assertRaises(PackageConflict):
                withdraw(self.user, app.pk, app.test_authorization.pk)
            with self.assertRaises(PackageConflict):
                save_package(self.user, app.pk, {'cv_version': package.cv_approval_id, 'expected_revision': 1,
                    'context_sha256': content_hash(context(app)), 'letter_text': 'Too late',
                    'email_subject': 'Synthetic', 'email_body': 'New draft'})
            return Result('accepted', '<synthetic@brevo.invalid>')
        with patch.object(fixtures.FakeTransport, 'send', side_effect=send) as provider:
            self.assertEqual(self.dispatch(app).state, 'accepted')
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(app.packages.count(), 1)

    def test_name_changed_between_preflight_and_reservation_is_not_authorized(self):
        app = self.application()
        original = self.service._reserve
        def change_name(*args):
            get_user_model().objects.filter(pk=self.user.pk).update(full_name='Changed after preview')
            return original(*args)
        with patch.object(self.service, '_reserve', side_effect=change_name):
            with self.assertRaises(DeliveryError):
                self.dispatch(app)
        self.assertFalse(Budget.objects.exists())
        self.assertEqual(self.transport.calls, [])

    def test_identical_handoff_during_preflight_reconciles_existing_receipt(self):
        app = self.application()
        auth = app.test_authorization
        args = dispatch_inputs(self.user, auth)
        args.update(user_id=self.user.pk, channel='application', application_id=app.pk,
                    authorization_id=auth.pk, idempotency_key=auth.pk)
        other = DeliveryService(self.transport, digest_key=b'x'*32, enabled=True)
        original = self.service._validate_authorization
        receipts = []
        def handoff_first(*values):
            receipts.append(other.deliver(**args))
            return original(*values)
        with patch.object(self.service, '_validate_authorization', side_effect=handoff_first):
            result = self.service.deliver(**args)
        self.assertEqual(result.pk, receipts[0].pk)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 1)

    def test_corrupt_receipt_link_is_not_exposed_as_owned_delivery(self):
        app = self.application()
        auth = app.test_authorization
        attempt = self.dispatch(app)
        DeliveryAttempt.objects.filter(pk=attempt.pk).update(idempotency_key=uuid.uuid4())
        response = self.client_for().get(self.base(app)+f'send-authorizations/{auth.pk}/')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('attempt', response.data)
        with self.assertRaises(DeliveryError):
            self.service.deliver(user_id=self.user.pk, channel='application', application_id=app.pk,
                authorization_id=auth.pk, idempotency_key=auth.pk, recipient='', subject='', text='')
        self.assertEqual(len(self.transport.calls), 1)

    def test_corrupt_private_file_blocks_plan_and_dispatch_before_quota(self):
        app = self.application()
        package = app.packages.get()
        with package.letter_document.open('wb') as stream:
            stream.write(b'private malicious exception-like text')
        response = self.client_for().get(self.base(app)+'send-plan/')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('malicious', str(response.data))
        self.assertFalse(Budget.objects.exists())
        self.assertEqual(self.transport.calls, [])

    def test_shared_five_message_pilot_cap_counts_prior_account_failures(self):
        app = self.application()
        self.service.pilot = ApplicationPilot(self.user.pk, 'employer@example.invalid', self.user.email,
            'platform@example.invalid', 6000000, 'Synthetic test review only')
        day = timezone.now().astimezone(__import__('zoneinfo').ZoneInfo('Africa/Nairobi')).date()
        Budget.objects.create(scope='global', day=day, account_reserved=5)
        with self.assertRaises(QuotaExceeded):
            self.dispatch(app)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 0)
        self.assertEqual(Authorization.objects.get().state, 'authorized')
        self.assertEqual(self.transport.calls, [])


class ApplicationPilotBoundaryTests(SimpleTestCase):
    def setUp(self):
        self.inner = fixtures.FakeTransport()
        self.policy = ApplicationPilot(1, 'owner@example.invalid', 'applicant@example.invalid',
            'platform@example.invalid', 6000000, 'Synthetic test review only')
        self.transport = ApplicationPilotTransport(self.policy, self.inner, still_approved=lambda policy: True)
        self.args = dict(recipient=self.policy.recipient, reply_to=self.policy.reply_to,
            subject='[AJIRI PILOT] Synthetic application', text='Synthetic only',
            attachments=[('Applicant_CV_Company.docx', b'fake docx'), ('Applicant_Cover_Letter_Company.docx', b'fake docx')],
            max_attachment_bytes=4*1024*1024)

    def test_exact_boundary_accepts_only_primary_synthetic_two_attachment_message(self):
        payload = self.transport.prepare(**self.args)
        self.assertEqual(len(json.loads(payload)['attachment']), 2)
        self.assertEqual(self.inner.calls, [])
        for change in ({'to': [{'email': 'employer@example.invalid'}]}, {'cc': [{'email': self.policy.recipient}]},
                       {'bcc': []}, {'subject': 'Real application'}, {'attachment': []},
                       {'replyTo': {'email': 'changed@example.invalid'}}):
            altered = json.loads(payload); altered.update(change)
            with self.assertRaises(DeliveryError):
                self.transport.send(json.dumps(altered).encode())
        self.transport.still_approved = lambda policy: False
        with self.assertRaises(DeliveryError):
            self.transport.send(payload)
        self.assertEqual(self.inner.calls, [])

    def test_missing_review_or_serialized_size_ceiling_fails_closed(self):
        for limit, review in [(0, 'review'), (1000, '')]:
            with self.assertRaises(ValueError):
                ApplicationPilot(1, self.policy.recipient, self.policy.reply_to, self.policy.sender, limit, review)
        policy = ApplicationPilot(1, self.policy.recipient, self.policy.reply_to, self.policy.sender, 10, 'Synthetic review')
        transport = ApplicationPilotTransport(policy, self.inner, still_approved=lambda policy: True)
        with self.assertRaises(DeliveryError):
            transport.prepare(**self.args)
