from datetime import timedelta
from unittest.mock import patch
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from . import test_delivery_service as fixtures
from .brevo_transport import BrevoTransport, Result
from .delivery_queue import enqueue, execute, publish, recover_leases
from .models import DeliveryAttempt, DeliveryDailyBudget, DeliveryTask, JobPublication
from . import test_saved_searches as search_fixtures
from .models import Notification


@override_settings(DELIVERY_QUEUE_ENABLED=True, REAL_EMAIL_ENABLED=True,
    ACCOUNT_SECURITY_EMAIL_ENABLED=True, GENERAL_APPLICATION_EMAIL_ENABLED=True,
    APPLICATION_EMAIL_ENABLED=True, JOB_FRESHNESS_ENFORCED=True,
    EMAIL_DELIVERY_MODE='account_security', ACCOUNT_EMAIL_TEST_CAPTURE=False,
    EMAIL_PLATFORM_FROM='platform@example.invalid', BREVO_TIMEOUT_SECONDS=10,
    ACCOUNT_LINK_ORIGIN='https://example.invalid', BREVO_API_KEY='synthetic-test-only',
    EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DurableQueueTests(TransactionTestCase):
    application = fixtures.DeliveryServiceTests.application
    authorization = fixtures.DeliveryServiceTests.authorization

    def setUp(self):
        fixtures.DeliveryServiceTests.setUp(self)
        with override_settings(JOB_FRESHNESS_ENFORCED=False):
            self.app = self.application()
        self.auth = self.app.test_authorization
        self.user.refresh_from_db()
        JobPublication.objects.create(job=self.app.job, origin='rss', status='published',
            confirmed_at=timezone.now(), closes_at=timezone.now()+timedelta(days=1))
        self.task = enqueue('application', self.auth.pk, owner=self.user)
        sender = patch.object(BrevoTransport, 'send', return_value=Result('accepted', '<synthetic>'))
        self.send = sender.start()
        self.addCleanup(sender.stop)

    def expired(self):
        DeliveryTask.objects.filter(pk=self.task.pk).update(lease_until=timezone.now()-timedelta(seconds=1))

    def test_duplicate_http_enqueue_and_worker_use_one_receipt_and_budget(self):
        self.assertEqual(enqueue('application', self.auth.pk, owner=self.user).pk, self.task.pk)
        self.send.assert_not_called()
        self.assertEqual(DeliveryTask.objects.count(), 1)
        self.assertEqual(execute(self.task.pk), 'succeeded')
        self.assertEqual(execute(self.task.pk), 'succeeded')
        self.send.assert_called_once()
        self.assertEqual(DeliveryAttempt.objects.count(), 1)
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').application_reserved, 1)

    def test_expired_lease_before_handoff_recovers_without_duplicate_work(self):
        with patch('jobs.delivery_queue._run', side_effect=SystemExit):
            with self.assertRaises(SystemExit):
                execute(self.task.pk)
        self.send.assert_not_called()
        self.expired()
        self.assertEqual(recover_leases(), 1)
        self.send.assert_called_once()

    def test_crash_after_handoff_recovers_existing_receipt_even_when_sending_disabled(self):
        from .delivery_queue import _run

        def crash(task):
            _run(task)
            raise SystemExit

        with patch('jobs.delivery_queue._run', crash):
            with self.assertRaises(SystemExit):
                execute(self.task.pk)
        self.expired()
        with override_settings(GENERAL_APPLICATION_EMAIL_ENABLED=False, APPLICATION_EMAIL_ENABLED=False):
            recover_leases()
        self.send.assert_called_once()
        self.task.refresh_from_db()
        self.assertEqual(self.task.state, 'succeeded')
        self.assertEqual(DeliveryAttempt.objects.count(), 1)

    def test_unknown_provider_handoff_is_never_automatically_retried(self):
        self.send.return_value = Result('unknown', failure_category='timeout')
        self.assertEqual(execute(self.task.pk), 'needs_reconciliation')
        self.assertEqual(execute(self.task.pk), 'needs_reconciliation')
        self.assertEqual(recover_leases(), 0)
        self.send.assert_called_once()

    def test_ambiguous_broker_publication_is_not_republished(self):
        with patch('config.celery.app.connection_for_write'), patch('config.celery.app.send_task', side_effect=TimeoutError) as send:
            self.assertEqual(publish(self.task.pk), 'publication_unknown')
            self.assertEqual(publish(self.task.pk), 'unchanged')
            send.assert_called_once()
            self.assertEqual(send.call_args.kwargs['args'], [str(self.task.pk)])
            self.assertFalse(send.call_args.kwargs['retry'])
        self.send.assert_not_called()
        self.assertEqual(execute(self.task.pk), 'succeeded')  # Original received message/explicit operator work.
        self.send.assert_called_once()

    def test_disabled_and_foreign_owner_targets_are_rejected(self):
        with override_settings(DELIVERY_QUEUE_ENABLED=False):
            self.assertEqual(execute(self.task.pk), 'disabled')
            self.assertEqual(recover_leases(), 0)
            self.assertEqual(publish(self.task.pk), 'disabled')
            with self.assertRaises(ValueError):
                enqueue('application', self.auth.pk, owner=self.user)
        other = self.user.__class__.objects.create_user(email='queue-other@example.invalid')
        with self.assertRaises(self.auth.__class__.DoesNotExist):
            enqueue('application', self.auth.pk, owner=other)
        with self.assertRaises(ValueError):
            enqueue('matching')
        self.send.assert_not_called()

    def test_crash_inside_handoff_retains_reserved_receipt_and_never_repeats_io(self):
        self.send.side_effect = SystemExit
        with self.assertRaises(SystemExit):
            execute(self.task.pk)
        self.assertEqual(DeliveryAttempt.objects.get().state, 'reserved')
        self.expired()
        self.assertEqual(recover_leases(), 1)
        self.assertEqual(execute(self.task.pk, resume_blocked=True), 'needs_reconciliation')
        self.send.assert_called_once()
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').application_reserved, 1)

    def test_only_three_expired_lease_claims_then_dead_without_io(self):
        with patch('jobs.delivery_queue._run', side_effect=SystemExit) as run:
            for _ in range(3):
                with self.assertRaises(SystemExit):
                    execute(self.task.pk)
                self.expired()
            self.assertEqual(recover_leases(), 1)
            self.assertEqual(execute(self.task.pk), 'dead')
            self.assertEqual(run.call_count, 3)
        self.task.refresh_from_db()
        self.assertEqual(self.task.attempts, 3)
        self.assertEqual(self.task.last_error, 'lease_exhausted')
        self.send.assert_not_called()

    def test_duplicate_claim_and_stale_worker_cannot_overwrite_new_settlement(self):
        from .delivery_queue import _run
        nested = False
        def replace(task):
            nonlocal nested
            if nested:
                return _run(task)
            self.assertEqual(execute(task.pk), 'running')
            nested = True
            self.expired()
            self.assertEqual(execute(task.pk), 'succeeded')
            return 'definite_failure'
        with patch('jobs.delivery_queue._run', replace):
            self.assertEqual(execute(self.task.pk), 'succeeded')
        self.send.assert_called_once()
        self.assertEqual(DeliveryAttempt.objects.count(), 1)

    def test_operator_arguments_are_validated_without_mutation_or_handoff(self):
        from io import StringIO
        from django.core.management import call_command
        from django.core.management.base import CommandError
        for limit in (0, 51, True, '2'):
            with self.assertRaises(CommandError):
                call_command('delivery_queue', recover_leases=True, limit=limit, stdout=StringIO())
            with self.assertRaises(ValueError):
                recover_leases(limit)
        for options in ({'resume_blocked': True}, {'execute_id': 'invalid'},
                        {'publish_pending': True, 'recover_leases': True}):
            with self.assertRaises(CommandError):
                call_command('delivery_queue', stdout=StringIO(), **options)
        with self.assertRaises(CommandError):
            call_command('enqueue_delivery_work', authorization_id=self.auth.pk,
                         notification_id=1, owner_id=self.user.pk, stdout=StringIO())
        self.task.refresh_from_db()
        self.assertEqual(self.task.attempts, 0)
        output = StringIO()
        call_command('delivery_queue', stdout=output)
        self.assertNotIn(self.user.email, output.getvalue())
        self.assertNotIn(str(self.auth.pk), output.getvalue())
        self.send.assert_not_called()

    def test_fast_worker_settlement_survives_publisher_timeout(self):
        def fast(*args, **kwargs):
            execute(self.task.pk)
            raise TimeoutError
        with patch('config.celery.app.connection_for_write'), patch('config.celery.app.send_task', side_effect=fast):
            self.assertEqual(publish(self.task.pk), 'succeeded')
        self.send.assert_called_once()

    def test_registered_task_is_inert_while_queue_disabled(self):
        from .tasks import run_delivery_task
        with override_settings(DELIVERY_QUEUE_ENABLED=False):
            self.assertEqual(run_delivery_task(str(self.task.pk)), 'disabled')
        self.send.assert_not_called()


@override_settings(DELIVERY_QUEUE_ENABLED=True, REAL_EMAIL_ENABLED=True,
    ACCOUNT_SECURITY_EMAIL_ENABLED=True, GENERAL_ALERT_EMAIL_ENABLED=True,
    SAVED_SEARCH_EMAIL_ENABLED=True, SAVED_SEARCHES_ENABLED=True, ALERT_EMAIL_ENABLED=True,
    JOB_FRESHNESS_ENFORCED=True, EMAIL_DELIVERY_MODE='account_security',
    ACCOUNT_EMAIL_TEST_CAPTURE=False, EMAIL_PLATFORM_FROM='platform@example.invalid',
    BREVO_TIMEOUT_SECONDS=10, ACCOUNT_LINK_ORIGIN='https://example.invalid',
    BREVO_API_KEY='synthetic-test-only', EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class QueuedSearchAndAlertTests(search_fixtures.SearchFixtures, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.consent()
        sender = patch.object(BrevoTransport, 'send', return_value=Result('accepted', '<synthetic>'))
        self.send = sender.start()
        self.addCleanup(sender.stop)

    def test_due_search_uses_same_window_receipt_and_future_window_cannot_be_consumed_early(self):
        search = self.search(email_frequency='daily')
        self.job()
        task = enqueue('saved_search', search.pk, owner=self.owner)
        self.assertEqual(enqueue('saved_search', search.pk, owner=self.owner).pk, task.pk)
        self.assertEqual(execute(task.pk), 'succeeded')
        self.assertEqual(execute(task.pk), 'succeeded')
        self.send.assert_called_once()
        search.refresh_from_db()
        search.next_email_at = timezone.now()+timedelta(days=1)
        search.save(update_fields=['next_email_at'])
        with self.assertRaises(ValueError):
            enqueue('saved_search', search.pk, owner=self.owner)

    def test_match_alert_queue_reuses_direct_transport_receipt(self):
        from .general_alert_email import deliver
        notification = Notification.objects.create(user=self.owner, job=self.job(), match_score=70, in_app=False)
        task = enqueue('alert', notification.pk, owner=self.owner)
        self.assertEqual(execute(task.pk), 'succeeded')
        self.assertEqual(deliver(notification.pk), 'accepted')
        self.send.assert_called_once()
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').alert_reserved, 1)

    def test_search_edit_cannot_retarget_queued_window(self):
        search = self.search(email_frequency='daily')
        self.job()
        task = enqueue('saved_search', search.pk, owner=self.owner)
        search.revision += 1
        search.save(update_fields=['revision'])
        self.assertEqual(execute(task.pk), 'blocked')
        self.send.assert_not_called()
        self.assertFalse(search.matches.exists())

    def test_search_delayed_task_cannot_collect_later_due_window(self):
        search = self.search(email_frequency='daily')
        self.job()
        task = enqueue('saved_search', search.pk, owner=self.owner)
        self.assertEqual(execute(task.pk), 'succeeded')
        first_count = search.matches.count()
        search.refresh_from_db()
        self.assertGreater(search.next_email_at, task.window_end)
        self.assertEqual(execute(task.pk), 'succeeded')
        self.assertEqual(search.matches.count(), first_count)
        self.send.assert_called_once()
