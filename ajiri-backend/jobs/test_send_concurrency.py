"""External confirmation keeps its atomic claim; legacy email is always disabled."""
import copy
import threading
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import close_old_connections
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient

from .models import Application, Job


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ConcurrentSendTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(email='concurrent@example.invalid', password='test-password')
        job = Job.objects.create(title='Test', company_name='Test', description='Test', source_name='test',
                                 source_url='https://example.invalid/concurrent')
        self.app = Application.objects.create(user=self.user, job=job, application_method='external_link',
                                               status='ready_for_review')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f'/api/jobs/applications/{self.app.pk}/send/'

    def test_overlapping_stale_external_confirmations_have_one_winner(self):
        barrier = threading.Barrier(2)
        results, errors = [], []

        def stale_read(*args, **kwargs):
            barrier.wait(10)
            return copy.copy(self.app)

        def confirm():
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(self.user)
                results.append(client.post(self.url).status_code)
            except BaseException as error:
                errors.append(error)
            finally:
                close_old_connections()

        with patch('jobs.views.get_object_or_404', side_effect=stale_read):
            threads = [threading.Thread(target=confirm) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(15)
            self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(sorted(results), [200, 400])

    def test_repeated_email_requests_never_reach_mail(self):
        self.app.application_method = 'email'
        self.app.save()
        with patch('django.core.mail.EmailMessage.send') as send:
            for _ in range(2):
                self.assertEqual(self.client.post(self.url).status_code, 409)
            send.assert_not_called()
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'ready_for_review')

    def test_stale_dismiss_cannot_undo_external_confirmation(self):
        stale = copy.copy(self.app)
        self.assertEqual(self.client.post(self.url).status_code, 200)
        with patch('jobs.views.get_object_or_404', return_value=stale):
            self.assertEqual(self.client.post(f'/api/jobs/applications/{self.app.pk}/dismiss/').status_code, 400)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'sent')
