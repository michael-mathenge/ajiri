from datetime import timedelta
from unittest.mock import patch
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

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
        client = APIClient()
        client.force_authenticate(self.user)
        url = f'/api/jobs/applications/{self.app.pk}/send-authorizations/{self.auth.pk}/dispatch/'
        for _ in range(2):
            response = client.post(url, {}, format='json')
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.data['queue']['id'], self.task.pk)
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

    def test_disabled_and_owner_status_do_not_expose_lease_or_documents(self):
        with override_settings(DELIVERY_QUEUE_ENABLED=False):
            self.assertEqual(execute(self.task.pk), 'disabled')
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.get(f'/api/jobs/delivery-tasks/{self.task.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('lease_token', response.data)
        self.assertNotIn('recipient', response.data)
        other = self.user.__class__.objects.create_user(email='queue-other@example.invalid')
        client.force_authenticate(other)
        self.assertEqual(client.get(f'/api/jobs/delivery-tasks/{self.task.pk}/').status_code, 404)
        self.send.assert_not_called()

    def test_matching_task_is_durable_deduplicated_and_contains_no_mail_payload(self):
        task = enqueue('matching')
        self.assertEqual(enqueue('matching').pk, task.pk)
        with patch('jobs.matching.sweep_all_active_jobs_for_matches', return_value=0) as matching:
            self.assertEqual(execute(task.pk), 'succeeded')
            matching.assert_called_once()
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
