from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient, APIRequestFactory
from .throttles import EndpointThrottle


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'], INGEST_API_KEY='synthetic-test-only')
class EndpointThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.clock = [1000.0]
        timer = patch.object(EndpointThrottle, 'timer', lambda _: self.clock[0])
        timer.start()
        self.addCleanup(timer.stop)
        rate = patch.object(EndpointThrottle, 'get_rate', return_value='2/min')
        rate.start()
        self.addCleanup(rate.stop)
        self.client = APIClient()

    def test_public_scopes_trigger_reset_and_remain_independent(self):
        for path in ['login', 'register', 'refresh']:
            url = f'/api/accounts/{path}/'
            for _ in range(2):
                self.assertNotEqual(self.client.post(url, {}).status_code, 429)
            response = self.client.post(url, {})
            self.assertEqual(response.status_code, 429)
            self.assertIn('Retry-After', response)
        self.clock[0] += 61
        self.assertNotEqual(self.client.post('/api/accounts/login/', {}).status_code, 429)

    def test_authenticated_actions_key_by_user(self):
        one = get_user_model().objects.create_user(email='one@example.invalid', password=None)
        two = get_user_model().objects.create_user(email='two@example.invalid', password=None)
        for url in ['/api/jobs/99999/apply/', '/api/jobs/applications/99999/send/']:
            self.client.force_authenticate(one)
            for _ in range(2):
                self.assertEqual(self.client.post(url).status_code, 404)
            self.assertEqual(self.client.post(url).status_code, 429)
            self.client.force_authenticate(two)
            self.assertEqual(self.client.post(url).status_code, 404)
            self.clock[0] += 61
            self.client.force_authenticate(one)
            self.assertEqual(self.client.post(url).status_code, 404)

    def test_ingestion_and_sweep_are_not_throttled(self):
        with patch('jobs.views.feedparser.parse') as parse, patch('jobs.views.ingest_feed', return_value={'created': 0}), patch('jobs.views.sweep_all_active_jobs_for_matches', return_value=0):
            parse.return_value.entries = [object()]
            for _ in range(4):
                self.assertEqual(self.client.post('/api/jobs/ingest/', b'feed', content_type='application/xml', HTTP_X_INGEST_KEY='synthetic-test-only').status_code, 200)
                self.assertEqual(self.client.post('/api/jobs/sweep/', HTTP_X_INGEST_KEY='synthetic-test-only').status_code, 200)
            self.assertEqual(self.client.post('/api/jobs/sweep/').status_code, 403)

    def test_proxy_identity_ignores_spoofed_prefix(self):
        request = APIRequestFactory().get('/', REMOTE_ADDR='192.0.2.9', HTTP_X_FORWARDED_FOR='spoofed, 198.51.100.7')
        with override_settings(REST_FRAMEWORK={**settings.REST_FRAMEWORK, 'NUM_PROXIES': 0}):
            self.assertEqual(EndpointThrottle().get_ident(request), '192.0.2.9')
        with override_settings(REST_FRAMEWORK={**settings.REST_FRAMEWORK, 'NUM_PROXIES': 1}):
            self.assertEqual(EndpointThrottle().get_ident(request), '198.51.100.7')
