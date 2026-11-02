import json
import os
import subprocess
import sys
from unittest.mock import patch

from django.conf import settings
from django.core.cache import caches
from django.test import SimpleTestCase, override_settings


@override_settings(CACHES={
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    'admin_login': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'admin-test'},
})
class AdminLoginTests(SimpleTestCase):
    def setUp(self):
        caches['admin_login'].clear()
        self.addCleanup(caches['admin_login'].clear)

    def test_login_is_throttled_before_authentication_and_get_stays_available(self):
        from .admin_site import AdminLoginThrottle
        with patch.object(AdminLoginThrottle, 'get_rate', return_value='2/min'):
            for _ in range(2):
                self.assertEqual(self.client.post('/admin/login/', {}).status_code, 200)
            response = self.client.post('/admin/login/', {})
            self.assertEqual(response.status_code, 429)
            self.assertIn('Retry-After', response)
            self.assertIn('no-store', response['Cache-Control'])
            self.assertEqual(self.client.get('/admin/login/').status_code, 200)
            self.assertEqual(self.client.post('/admin/login/', {}, REMOTE_ADDR='192.0.2.8').status_code, 200)

    def test_admin_login_counter_failure_closes_and_csrf_is_enforced(self):
        with patch('config.admin_site.AdminLoginThrottle.allow_request', side_effect=OSError):
            self.assertEqual(self.client.post('/admin/login/', {}).status_code, 503)
        from django.test import Client
        self.assertEqual(Client(enforce_csrf_checks=True).post('/admin/login/', {}).status_code, 403)

    def test_configured_route_replaces_default_and_retired_environment_flag_is_ignored(self):
        env = {**os.environ, 'DEBUG': 'True', 'PYTHON_DOTENV_DISABLED': '1',
               'ADMIN_URL_PATH': 'operator-test/', 'JOB_FEED_DISPLAY_ENABLED': 'True'}
        code = '''
import os, django, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from django.conf import settings
from django.test import Client, override_settings
from django.urls import reverse
with override_settings(ALLOWED_HOSTS=['testserver']):
    c = Client()
    print(json.dumps({'admin': c.get('/admin/').status_code,
                     'admin_login': c.get('/admin/login/').status_code,
                     'configured': c.get('/operator-test/').status_code,
                     'unknown_admin': c.get('/operator-test/not-a-route/').status_code,
                     'login_url': reverse('admin:login'),
                     'retired_flag_loaded': hasattr(settings, 'JOB_FEED_DISPLAY_ENABLED')}))
'''
        result = subprocess.run([sys.executable, '-c', code], cwd=settings.BASE_DIR,
                                env=env, text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), {'admin': 404, 'admin_login': 404,
            'configured': 302, 'unknown_admin': 302, 'login_url': '/operator-test/login/', 'retired_flag_loaded': False})
        for path in ('api/', 'jobs/', '../hidden/', '', '/hidden/', 'hidden', 'a/b/'):
            env['ADMIN_URL_PATH'] = path
            result = subprocess.run([sys.executable, '-c', 'import config.settings'], cwd=settings.BASE_DIR,
                env=env, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
