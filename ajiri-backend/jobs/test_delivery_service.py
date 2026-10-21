import io
import json
import threading
import uuid
import tempfile
from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, OperationalError, transaction
from django.db.models.query import QuerySet
from django.test import SimpleTestCase, TransactionTestCase, override_settings
from django.utils import timezone

from profiles.models import Profile
from profiles.cv_test_helpers import approved_cv
from profiles.cv_builder import content_hash
from .application_packages import save_package, context, PackageConflict
from .package_review import approve_package
from .send_authorization import plan_response, authorize, dispatch_inputs
from .models import ApplicationSendAuthorization
from .brevo_transport import BrevoTransport, NoRedirect, Result
from .delivery_service import DeliveryError, DeliveryService, Policy, QuotaExceeded
from .models import Application, DeliveryAttempt as Attempt, DeliveryDailyBudget as Budget, Job, Notification


class BrevoTransportTests(SimpleTestCase):
    def setUp(self):
        self.transport = BrevoTransport('test-placeholder', 'platform@example.invalid')

    def test_payload_reply_to_and_bytes_attachments(self):
        payload = json.loads(self.transport.prepare(recipient='employer@example.invalid', subject='Application',
            text='Synthetic body', reply_to='applicant@example.invalid',
            attachments=[('cv.docx', b'synthetic')], max_attachment_bytes=20))
        self.assertEqual(payload['sender']['email'], 'platform@example.invalid')
        self.assertEqual(payload['replyTo']['email'], 'applicant@example.invalid')
        self.assertEqual(payload['attachment'][0]['content'], 'c3ludGhldGlj')
        self.assertEqual(len(payload['to']), 1)
        self.assertNotIn('test-placeholder', repr(self.transport))

    def test_invalid_message_and_unapproved_attachment_size_rejected_before_io(self):
        for extra in ({'subject': 'header\r\ninjected'}, {'recipient': 'bad-address'},
                      {'attachments': [('cv.docx', b'x')]},
                      {'attachments': [('../cv.docx', b'x')], 'max_attachment_bytes': 10}):
            args = dict(recipient='owner@example.invalid', subject='Subject', text='Body')
            args.update(extra)
            with self.assertRaises(Exception):
                self.transport.prepare(**args)

    def response(self, body=b'{"messageId":"<synthetic@brevo.invalid>"}', status=201):
        from unittest.mock import MagicMock
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = status
        response.read.return_value = body
        return response

    @patch('jobs.brevo_transport.build_opener')
    def test_https_post_receipt_no_redirect_and_one_call(self, opener):
        opener.return_value.open.return_value = self.response()
        result = self.transport.send(b'{}')
        self.assertEqual(result.state, 'accepted')
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.brevo.com/v3/smtp/email')
        self.assertEqual(request.method, 'POST')
        self.assertEqual(opener.return_value.open.call_count, 1)
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.invalid'))

    @patch('jobs.brevo_transport.build_opener')
    def test_status_classification_and_no_raw_provider_body(self, opener):
        for status, expected in [(400, 'definite_failure'), (401, 'definite_failure'),
                                 (429, 'definite_failure'), (408, 'unknown'),
                                 (500, 'unknown'), (302, 'unknown')]:
            with self.subTest(status=status):
                body = io.BytesIO(b'credential-or-CV-must-not-be-read')
                opener.return_value.open.side_effect = HTTPError('https://api.brevo.com', status, 'private', {}, body)
                result = self.transport.send(b'{}')
                self.assertEqual(result.state, expected)
                self.assertNotIn('credential', repr(result))
                self.assertTrue(body.closed)

    @patch('jobs.brevo_transport.build_opener')
    def test_timeouts_network_and_malformed_acceptance_are_unknown(self, opener):
        for error in (TimeoutError('private'), URLError('private')):
            opener.return_value.open.side_effect = error
            self.assertEqual(self.transport.send(b'{}').state, 'unknown')
        opener.return_value.open.side_effect = None
        for body in (b'not-json', b'{}', b'{"messageId":"private\nbody"}', b'x' * 16385):
            opener.return_value.open.return_value = self.response(body)
            self.assertEqual(self.transport.send(b'{}').state, 'unknown')


class FakeTransport(BrevoTransport):
    def __init__(self, result=None):
        super().__init__('test-placeholder', 'platform@example.invalid', sender_name='Ajiri')
        object.__setattr__(self, 'calls', [])
        object.__setattr__(self, 'result', result or Result('accepted', '<synthetic@brevo.invalid>'))

    def send(self, payload):
        assert not connection.in_atomic_block, 'Network I/O inside a database transaction'
        self.calls.append(payload)
        return self.result


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
                   EMAIL_PLATFORM_FROM='platform@example.invalid')
class DeliveryServiceTests(TransactionTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        media = override_settings(MEDIA_ROOT=temporary.name)
        media.enable()
        self.addCleanup(media.disable)
        self.keys = {}
        self.user = get_user_model().objects.create_user(email='owner@example.invalid', password='synthetic-password')
        Profile.objects.filter(user=self.user).update(email_verified_at=timezone.now(), verified_email=self.user.email)
        self.transport = FakeTransport()
        self.service = DeliveryService(self.transport, digest_key=b'x' * 32, enabled=True)

    def application(self, user=None):
        job = Job.objects.create(title='Test', company_name='Example', description='Synthetic',
            source_name='test', source_url='https://example.invalid/' + uuid.uuid4().hex,
            application_method='email', application_email='employer@example.invalid')
        app = Application.objects.create(user=user or self.user, job=job, status='ready_for_review',
            application_method='email', application_email='employer@example.invalid')
        from profiles.models import CVApproval
        cv = CVApproval.objects.filter(profile__user=app.user).first() or approved_cv(app.user)
        package = save_package(app.user, app.pk, {'cv_version': cv.pk, 'expected_revision': 0,
            'context_sha256': content_hash(context(app)), 'letter_text': 'Synthetic letter',
            'email_subject': 'Synthetic', 'email_body': 'Private test body'})
        approve_package(app.user, app.pk, package.pk, 1, package.content_sha256)
        app.test_authorization = self.authorization(app)
        return app

    def authorization(self, app, retry_of=None):
        plan = plan_response(app.user, app, retry_of)
        return authorize(app.user, app.pk, {'request_key': uuid.uuid4(),
            'package_id': uuid.UUID(plan['plan']['package_id']), 'expected_revision': 1,
            'plan_sha256': plan['plan_sha256'], 'retry_of': retry_of, 'authorization': True})[0]

    def deliver(self, application=None, **changes):
        app = application or self.application()
        args = dict(user_id=self.user.pk, channel='application', recipient='employer@example.invalid',
            subject='Synthetic', text='Private test body', application_id=app.pk,
            idempotency_key=uuid.uuid4())
        args.update(changes)
        if args['channel'] == 'application':
            key = uuid.UUID(str(args['idempotency_key']))
            auth = self.keys.get(key)
            if auth is None:
                auth = ApplicationSendAuthorization.objects.get(pk=app.test_authorization.pk)
                if changes.get('retry_of'):
                    try:
                        auth = self.authorization(app, changes['retry_of'])
                    except PackageConflict as error:
                        raise DeliveryError(str(error)) from None
                elif auth.state != 'authorized':
                    raise DeliveryError('A new authorization is required for another explicit action.')
                self.keys[key] = auth
            auth.refresh_from_db()
            args['authorization_id'] = auth.pk
            args['idempotency_key'] = auth.pk
            # Frozen inputs prepared by the approved service, never arbitrary test attachments.
            if auth.state == 'authorized':
                try:
                    args.update(dispatch_inputs(app.user, auth))
                except PackageConflict as error:
                    raise DeliveryError(str(error)) from None
                args.update({key: value for key, value in changes.items() if key != 'idempotency_key'})
        return self.service.deliver(**args)

    def test_disabled_by_default_and_unverified_block_before_reservation(self):
        app = self.application()
        self.service.enabled = False
        with self.assertRaises(DeliveryError):
            self.deliver(app)
        self.service.enabled = True
        Profile.objects.filter(user=self.user).update(email_verified_at=None)
        with self.assertRaises(DeliveryError):
            self.deliver(app)
        self.assertEqual(Budget.objects.count(), 0)
        self.assertEqual(self.transport.calls, [])

    def test_accepted_idempotency_and_no_payload_in_ledger(self):
        app, key = self.application(), uuid.uuid4()
        first = self.deliver(app, idempotency_key=key)
        second = self.deliver(app, idempotency_key=key)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.state, 'accepted')
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 1)
        self.assertEqual(Budget.objects.get(scope=f'user:{self.user.pk}').application_reserved, 1)
        self.assertNotIn('Private test body', str(first.__dict__))
        self.assertNotIn('employer@example.invalid', str(first.__dict__))
        app.refresh_from_db()
        self.assertEqual(app.status, 'ready_for_review')  # Existing API lifecycle untouched.

    def test_failed_attempt_consumes_quota_and_requires_explicit_new_retry(self):
        object.__setattr__(self.transport, 'result', Result('definite_failure', failure_category='provider_rejected'))
        app = self.application()
        first = self.deliver(app)
        with self.assertRaises(DeliveryError):
            self.deliver(app)
        self.deliver(app, retry_of=first.pk)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 2)
        self.assertEqual(len(self.transport.calls), 2)

    def test_unknown_stops_retries_and_cross_day_duplicate(self):
        object.__setattr__(self.transport, 'result', Result('unknown', failure_category='timeout'))
        app, key = self.application(), uuid.uuid4()
        self.deliver(app, idempotency_key=key)
        self.deliver(app, idempotency_key=key)
        with patch('jobs.delivery_service.timezone.now', return_value=datetime(2026, 11, 1, tzinfo=dt_timezone.utc)):
            with self.assertRaises(DeliveryError):
                self.deliver(app)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(sum(Budget.objects.filter(scope='global').values_list('application_reserved', flat=True)), 1)

    def test_per_user_ten_and_rollback_global_increment(self):
        for _ in range(10):
            self.deliver()
        with self.assertRaises(QuotaExceeded):
            self.deliver()
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 10)
        self.assertEqual(len(self.transport.calls), 10)

    def test_fixed_allocation_and_account_shared_capacity(self):
        self.service.policy = Policy(total=3, applications=1, accounts=1, alerts=1)
        self.deliver()
        with self.assertRaises(QuotaExceeded):
            self.deliver()
        for index, channel in enumerate(('password_reset', 'email_verification')):
            if index:
                with self.assertRaises(QuotaExceeded):
                    self.deliver(channel=channel, recipient=self.user.email, application_id=None)
            else:
                self.deliver(channel=channel, recipient=self.user.email, application_id=None)
        self.assertEqual(Budget.objects.get(scope='global').account_reserved, 1)

    def test_alert_requires_confirmation_and_retry_bound_remains_disabled(self):
        notification = Notification.objects.create(user=self.user, job=self.application().job, match_score=90)
        args = dict(channel='alert', application_id=None, recipient=self.user.email, notification_id=notification.pk)
        with self.assertRaises(DeliveryError):
            self.deliver(**args)
        with self.assertRaises(DeliveryError):
            self.deliver(**args, alert_consent_confirmed=True)
        self.assertEqual(len(self.transport.calls), 0)
        from profiles.alert_consent import record_choice
        record_choice(self.user, True, uuid.uuid4())
        object.__setattr__(self.transport, 'result', Result('definite_failure', failure_category='provider_rejected'))
        first = self.deliver(**args, alert_consent_confirmed=True)
        with self.assertRaises(DeliveryError):
            self.deliver(**args, alert_consent_confirmed=True, retry_of=first.pk)
        self.assertEqual(len(self.transport.calls), 1)

    def test_alert_revocation_during_prepare_blocks_reservation(self):
        from profiles.alert_consent import record_choice
        record_choice(self.user, True, uuid.uuid4())
        notification = Notification.objects.create(user=self.user, job=self.application().job, match_score=90)
        original = self.transport.prepare
        def prepare(**kwargs):
            record_choice(self.user, False, uuid.uuid4())
            return original(**kwargs)
        with patch.object(type(self.transport), 'prepare', side_effect=prepare):
            with self.assertRaises(DeliveryError):
                self.deliver(channel='alert', recipient=self.user.email, application_id=None,
                    notification_id=notification.pk, alert_consent_confirmed=True)
        self.assertFalse(Attempt.objects.exists())
        self.assertEqual(len(self.transport.calls), 0)

    def test_nairobi_rollover(self):
        for moment in (datetime(2026, 10, 16, 20, 59, tzinfo=dt_timezone.utc),
                       datetime(2026, 10, 16, 21, 1, tzinfo=dt_timezone.utc)):
            with patch('jobs.delivery_service.timezone.now', return_value=moment):
                self.deliver()
        self.assertEqual(Budget.objects.filter(scope='global').count(), 2)

    def test_conflicting_key_recipient_and_invalid_attachment_do_not_spend(self):
        key = uuid.uuid4()
        self.deliver(idempotency_key=key)
        for changes in ({'idempotency_key': key}, {'recipient': 'wrong@example.invalid'},
                        {'attachments': [('cv.docx', b'x')]}):
            with self.assertRaises((DeliveryError, ValueError)):
                self.deliver(**changes)
        self.assertEqual(len(self.transport.calls), 1)

    def test_global_total_boundary_even_if_category_has_room(self):
        Budget.objects.create(scope='global', day=timezone.now().astimezone(__import__('zoneinfo').ZoneInfo('Africa/Nairobi')).date(),
            account_reserved=190, alert_reserved=10)
        with self.assertRaises(QuotaExceeded):
            self.deliver()
        self.assertFalse(Attempt.objects.exists())

    def test_concurrent_same_request_produces_one_provider_call(self):
        app = self.application()
        authorization = app.test_authorization
        # Freeze the actual request BEFORE starting workers. The convenience
        # helper lazily checks authorization state and mutates self.keys, which
        # can race the first handoff before DeliveryService is even called.
        # see docs/CONCEPTS.md#delivery-concurrency-fixtures
        args = dict(user_id=self.user.pk, channel='application', application_id=app.pk,
            authorization_id=authorization.pk, idempotency_key=authorization.pk,
            **dispatch_inputs(self.user, authorization))
        gate = threading.Barrier(2)
        results, errors = [], []
        def worker():
            close_old_connections()
            try:
                gate.wait(timeout=10)
                results.append(self.service.deliver(**args).pk)
            except Exception as error:
                errors.append((type(error).__name__, str(error)))
            finally:
                close_old_connections()
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        # A bounded SQLite lock response is a documented no-send outcome. Only
        # that exact error is allowed, and only with one durable winning receipt.
        self.assertTrue(all(error == ('DeliveryError',
            'Delivery accounting is busy; no email was attempted.') for error in errors), errors)
        self.assertEqual(Attempt.objects.count(), 1)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 1)
        for _ in errors:
            results.append(self.service.deliver(**args).pk)
        self.assertEqual(len(results), 2)
        self.assertEqual(len(set(results)), 1)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 1)

    def test_concurrent_global_last_slot(self):
        self.service.policy = Policy(total=1, applications=1, accounts=0, alerts=0)
        apps = [self.application(), self.application()]
        gate = threading.Barrier(2)
        outcomes = []
        def worker(app):
            close_old_connections()
            try:
                gate.wait(timeout=10)
                attempt = self.deliver(app, idempotency_key=app.test_authorization.pk)
                outcomes.append((app.pk, attempt.state))
            except QuotaExceeded:
                outcomes.append((app.pk, 'quota'))
            except DeliveryError as error:
                outcomes.append((app.pk, 'busy' if str(error) ==
                    'Delivery accounting is busy; no email was attempted.' else 'unexpected_delivery_error'))
            except Exception as error:
                outcomes.append((app.pk, type(error).__name__))
            finally:
                close_old_connections()
        threads = [threading.Thread(target=worker, args=(app,)) for app in apps]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        states = [state for _, state in outcomes]
        self.assertEqual(states.count('accepted'), 1)
        self.assertEqual(len(states), 2)
        self.assertTrue(all(state in ('accepted', 'quota', 'busy') for state in states), outcomes)
        # Exhausted SQLite lock retries are a documented no-handoff outcome.
        # Reconcile that same key only after both workers finish; never resend a winner.
        for pk, state in outcomes:
            if state == 'busy':
                app = next(app for app in apps if app.pk == pk)
                self.assertFalse(Attempt.objects.filter(application=app).exists())
                with self.assertRaises(QuotaExceeded):
                    self.deliver(app, idempotency_key=app.test_authorization.pk)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(Attempt.objects.count(), 1)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 1)

    def test_unexpected_transport_exception_is_sanitized_and_never_retried(self):
        with patch.object(FakeTransport, 'send', side_effect=RuntimeError('sensitive provider text')) as send:
            app, key = self.application(), uuid.uuid4()
            attempt = self.deliver(app, idempotency_key=key)
            self.assertEqual(attempt.state, 'unknown')
            self.assertNotIn('sensitive', str(attempt.__dict__))
            self.deliver(app, idempotency_key=key)
            self.assertEqual(send.call_count, 1)

    def test_exhausted_reservation_lock_retries_never_handoff_or_consume_budget(self):
        app = self.application()
        with patch.object(self.service, '_reserve', side_effect=OperationalError('synthetic lock')) as reserve:
            with self.assertRaisesMessage(DeliveryError, 'no email was attempted'):
                self.deliver(app, idempotency_key=app.test_authorization.pk)
        self.assertEqual(reserve.call_count, 3)
        self.assertFalse(self.transport.calls)
        self.assertFalse(Attempt.objects.exists())
        self.assertFalse(Budget.objects.exists())

    def test_failed_receipt_write_retains_blocking_reservation(self):
        original = QuerySet.update
        def fail_receipt(queryset, **kwargs):
            if queryset.model is Attempt:
                raise OperationalError('sensitive database detail')
            return original(queryset, **kwargs)
        app = self.application()
        with patch.object(QuerySet, 'update', autospec=True, side_effect=fail_receipt) as update, \
                patch('jobs.delivery_service.time.sleep') as sleep:
            with self.assertRaisesMessage(DeliveryError, 'needs reconciliation'):
                self.deliver(app)
        self.assertEqual(sum(call.args[0].model is Attempt for call in update.call_args_list), 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(Attempt.objects.get().state, 'reserved')
        with self.assertRaises(DeliveryError):
            self.deliver(app)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 1)

    def test_receipt_read_retry_preserves_committed_result_without_resending(self):
        original = Attempt.refresh_from_db
        reads = []

        def read(attempt, *args, **kwargs):
            reads.append(attempt.pk)
            if len(reads) == 1:
                raise OperationalError('private database detail')
            return original(attempt, *args, **kwargs)

        app, key = self.application(), uuid.uuid4()
        with patch.object(Attempt, 'refresh_from_db', new=read), \
                patch('jobs.delivery_service.time.sleep') as sleep:
            receipt = self.deliver(app, idempotency_key=key)
        self.assertEqual(receipt.state, 'accepted')
        self.assertEqual(len(reads), 2)
        self.assertEqual(sleep.call_count, 1)
        self.assertEqual(self.deliver(app, idempotency_key=key).pk, receipt.pk)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 1)

    def test_receipt_recovers_from_overlapping_sqlite_writer_without_resending(self):
        """An unrelated reservation can hold SQLite's writer lock after send."""
        locked, release = threading.Event(), threading.Event()
        errors = []

        def writer():
            close_old_connections()
            try:
                with transaction.atomic():
                    Budget.objects.filter(scope='global').update(account_reserved=0)
                    locked.set()
                    if not release.wait(timeout=10):
                        raise RuntimeError('Writer release timed out')
            except Exception as error:
                errors.append(type(error).__name__)
            finally:
                close_old_connections()

        thread = threading.Thread(target=writer)

        def send(payload):
            self.assertFalse(connection.in_atomic_block)
            thread.start()
            self.assertTrue(locked.wait(timeout=10))
            return Result('accepted', '<synthetic@brevo.invalid>')

        def release_writer(delay):
            release.set()
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())

        app, key = self.application(), uuid.uuid4()
        try:
            with patch.object(FakeTransport, 'send', side_effect=send) as provider, \
                    patch('jobs.delivery_service.time.sleep', side_effect=release_writer) as sleep:
                receipt = self.deliver(app, idempotency_key=key)
                self.assertEqual(receipt.state, 'accepted')
                self.assertEqual(sleep.call_count, 1)
                self.assertEqual(self.deliver(app, idempotency_key=key).pk, receipt.pk)
                self.assertEqual(provider.call_count, 1)
        finally:
            release.set()
            if thread.ident is not None:
                thread.join(timeout=10)
        self.assertEqual(errors, [])
        self.assertEqual(Attempt.objects.count(), 1)
        self.assertEqual(Budget.objects.get(scope='global').application_reserved, 1)
        self.assertEqual(Budget.objects.get(scope=f'user:{self.user.pk}').application_reserved, 1)

    def test_busy_accounting_is_bounded_and_outer_transaction_rejected(self):
        with patch.object(self.service, '_reserve', side_effect=OperationalError('private')) as reserve:
            with self.assertRaisesMessage(DeliveryError, 'no email was attempted'):
                self.deliver()
            self.assertEqual(reserve.call_count, 3)
        with transaction.atomic():
            with self.assertRaisesMessage(DeliveryError, 'outside caller transactions'):
                self.deliver()
        self.assertEqual(self.transport.calls, [])

    def test_policy_validation_and_preflight_failure_leave_no_reservation(self):
        for values in ({'total': 1}, {'applications': -1}, {'total': True}):
            with self.assertRaises(ValueError):
                Policy(**values)
        with self.assertRaises(ValueError):
            self.deliver(idempotency_key='not-a-uuid')
        self.assertFalse(Budget.objects.exists())
