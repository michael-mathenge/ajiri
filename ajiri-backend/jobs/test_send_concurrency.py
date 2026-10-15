from django.core.cache import cache
import copy
import tempfile
import threading
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail import EmailMessage
from django.db import close_old_connections
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient

from .models import Application, Job


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'], EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ConcurrentSendTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.tmp.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.user = get_user_model().objects.create_user(email='concurrent@example.com', password='test-password')
        job = Job.objects.create(title='Test', company_name='Test', description='Test', source_name='test', source_url='https://example.com/concurrent', application_method='email', application_email='jobs@example.com')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        response = self.client.post(f'/api/jobs/{job.pk}/apply/')
        self.app = Application.objects.get(pk=response.data['id'])
        self.url = f'/api/jobs/applications/{self.app.pk}/send/'
        mail.get_connection()  # Initialize the captured outbox before spawning.

    def test_overlapping_stale_requests_send_one_email(self):
        claimed = threading.Event()
        release = threading.Event()
        results, errors = [], []
        original_send = EmailMessage.send
        stale = copy.copy(self.app)

        def delayed_send(message, **kwargs):
            claimed.set()
            if not release.wait(10):
                raise TimeoutError('Test did not release delivery')
            return original_send(message, **kwargs)

        def first_request():
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(self.user)
                results.append(client.post(self.url).status_code)
            except BaseException as error:
                errors.append(error)
            finally:
                close_old_connections()

        with patch('jobs.views.EmailMessage.send', autospec=True, side_effect=delayed_send):
            thread = threading.Thread(target=first_request)
            thread.start()
            try:
                self.assertTrue(claimed.wait(10), 'First request never reached delivery')
                # Emulate a second request that read READY before the winner's write.
                # Its status check passes, so only the atomic conditional claim protects SMTP.
                with patch('jobs.views.get_object_or_404', return_value=stale):
                    second = self.client.post(self.url)
                self.assertEqual(second.status_code, 400)
                self.assertEqual(len(mail.outbox), 0)  # first is still in-flight
            finally:
                release.set()
                thread.join(10)
            self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(results, [200])
        self.assertEqual(len(mail.outbox), 1)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'sent')
        self.assertIsNotNone(self.app.sent_at)

    def test_failure_releases_claim_and_retry_sends_once(self):
        with patch('jobs.views.EmailMessage.send', side_effect=OSError('delivery failed')):
            self.assertEqual(self.client.post(self.url).status_code, 502)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'ready_for_review')
        self.assertIsNone(self.app.sent_at)
        self.assertEqual(self.client.post(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url).status_code, 400)
        self.assertEqual(len(mail.outbox), 1)

    def test_stale_dismiss_cannot_undo_send_claim(self):
        stale = copy.copy(self.app)
        self.assertEqual(self.client.post(self.url).status_code, 200)
        with patch('jobs.views.get_object_or_404', return_value=stale):
            response = self.client.post(f'/api/jobs/applications/{self.app.pk}/dismiss/')
        self.assertEqual(response.status_code, 400)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'sent')
