import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.core.cache import cache
from django.db import OperationalError
from django.test import TestCase, SimpleTestCase, RequestFactory
from rest_framework.test import APIClient
from accounts.throttles import EndpointThrottle
from .safe_logging import SafeJSONFormatter, PrivateProcessRotatingHandler, CorrelationMiddleware


class HealthTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_get_head_stale_jwt_and_method(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer expired')
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'ok'})
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.client.head('/api/health/').content, b'')
        self.assertEqual(self.client.post('/api/health/').status_code, 405)

    def test_db_failure_generic_and_no_cache(self):
        with patch('config.views.connection.cursor', side_effect=OperationalError('secret SQL filename')):
            response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, {'status': 'unavailable'})
        self.assertNotIn(b'secret', response.content)
        self.assertIn('no-store', response['Cache-Control'])

    def test_loose_throttle_and_reset(self):
        clock = [1000]
        with patch.object(EndpointThrottle, 'get_rate', return_value='1/min'), patch.object(EndpointThrottle, 'timer', lambda _: clock[0]):
            self.assertEqual(self.client.get('/api/health/').status_code, 200)
            self.assertEqual(self.client.get('/api/health/').status_code, 429)
            clock[0] += 61
            self.assertEqual(self.client.get('/api/health/').status_code, 200)


class SanitizedLogTests(SimpleTestCase):
    def record(self):
        try:
            raise ValueError('secret@example.invalid password token private CV filename')
        except ValueError:
            import sys
            return logging.LogRecord('django.request', logging.ERROR, '/private/path', 1,
                                     'secret %s', ('secret-token',), sys.exc_info())

    def test_formatter_drops_messages_arguments_exceptions_and_headers(self):
        record = self.record()
        record.request = RequestFactory().get('/secret-file?token=secret', HTTP_AUTHORIZATION='secret')
        value = SafeJSONFormatter().format(record)
        self.assertNotIn('secret', value)
        self.assertEqual(set(json.loads(value)), {'timestamp', 'severity', 'event', 'correlation_id', 'status', 'route'})

    def test_rotation_and_process_separation(self):
        with tempfile.TemporaryDirectory() as directory:
            handler = PrivateProcessRotatingHandler(directory, max_bytes=200, backup_count=2)
            try:
                with patch('config.safe_logging.os.getpid', return_value=101):
                    for _ in range(8): handler.emit(self.record())
                with patch('config.safe_logging.os.getpid', return_value=102):
                    handler.emit(self.record())
            finally:
                handler.close()
            names = [p.name for p in Path(directory).iterdir()]
            self.assertIn('errors-101.jsonl.1', names)
            self.assertIn('errors-102.jsonl', names)
            self.assertLessEqual(len(names), 4)
            for path in Path(directory).iterdir():
                self.assertNotIn('secret', path.read_text())
