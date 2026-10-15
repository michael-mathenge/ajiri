import json
import os
import subprocess
import sys
import tempfile
from django.conf import settings
from django.test import SimpleTestCase


class SharedThrottleTests(SimpleTestCase):
    def child(self, directory, action='request', **extra):
        env = {**os.environ, 'PYTHON_DOTENV_DISABLED': '1', 'DEBUG': 'True',
               'THROTTLE_CACHE_DIR': directory, **extra}
        code = '''
import django, json, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from accounts.throttles import EndpointThrottle
from rest_framework.test import APIRequestFactory
from django.core.cache import caches
if ACTION == 'clear':
    caches['throttle'].clear()
    print('true')
else:
    throttle = EndpointThrottle()
    throttle.get_rate = lambda: '1/min'
    view = type('View', (), {'throttle_scope': 'login'})()
    request = APIRequestFactory().post('/', REMOTE_ADDR='192.0.2.81')
    print(json.dumps(throttle.allow_request(request, view)))
'''.replace('ACTION', repr(action))
        return subprocess.run([sys.executable, '-c', code], env=env,
                              cwd=settings.BASE_DIR, text=True, capture_output=True)

    def test_independent_workers_share_budget_and_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            first = self.child(directory)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue(json.loads(first.stdout))
            second = self.child(directory)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertFalse(json.loads(second.stdout))
            reset = self.child(directory, 'clear')
            self.assertEqual(reset.returncode, 0, reset.stderr)
            self.assertTrue(json.loads(self.child(directory).stdout))

    def test_relative_and_application_paths_fail_configuration(self):
        for directory in ['relative-cache', str(settings.BASE_DIR / 'frontend_build' / 'cache')]:
            result = self.child(directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('ImproperlyConfigured', result.stderr)
