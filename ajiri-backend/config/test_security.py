import json
import os
import subprocess
import sys
from pathlib import Path
from django.conf import settings
from django.test import SimpleTestCase, override_settings


class DeploySettingsTests(SimpleTestCase):
    def settings_snapshot(self, **overrides):
        env = os.environ.copy()
        env.update(PYTHON_DOTENV_DISABLED='1', DEBUG='False', SECRET_KEY='audit-dummy-not-real-configuration-' * 3,
                   ALLOWED_HOSTS='audit.invalid', TRUST_PROXY_SSL_HEADER='False',
                   SECURE_HSTS_INCLUDE_SUBDOMAINS='False', SECURE_HSTS_PRELOAD='False')
        for name in ['SECURE_SSL_REDIRECT', 'SECURE_HSTS_SECONDS', 'SESSION_COOKIE_SECURE',
                     'CSRF_COOKIE_SECURE', 'SECURE_CONTENT_TYPE_NOSNIFF', 'SECURE_REFERRER_POLICY', 'X_FRAME_OPTIONS']:
            env.pop(name, None)
        env.update(overrides)
        code = ("import os,json; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; "
                "import django; django.setup(); from django.conf import settings as s; "
                "print(json.dumps({k:getattr(s,k,None) for k in "
                "['SECURE_SSL_REDIRECT','SECURE_HSTS_SECONDS','SECURE_HSTS_INCLUDE_SUBDOMAINS',"
                "'SECURE_HSTS_PRELOAD','SESSION_COOKIE_SECURE','CSRF_COOKIE_SECURE',"
                "'REFRESH_COOKIE_SECURE','SECURE_PROXY_SSL_HEADER','SECURE_CONTENT_TYPE_NOSNIFF',"
                "'SECURE_REFERRER_POLICY','X_FRAME_OPTIONS']}))")
        result = subprocess.run([sys.executable, '-c', code], cwd=settings.BASE_DIR, env=env, text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_production_defaults_and_local_defaults(self):
        prod = self.settings_snapshot()
        self.assertTrue(prod['SECURE_SSL_REDIRECT'])
        self.assertEqual(prod['SECURE_HSTS_SECONDS'], 300)
        self.assertFalse(prod['SECURE_HSTS_INCLUDE_SUBDOMAINS'])
        self.assertFalse(prod['SECURE_HSTS_PRELOAD'])
        self.assertIsNone(prod['SECURE_PROXY_SSL_HEADER'])
        self.assertTrue(prod['SESSION_COOKIE_SECURE'])
        self.assertTrue(prod['CSRF_COOKIE_SECURE'])
        self.assertTrue(prod['REFRESH_COOKIE_SECURE'])
        local = self.settings_snapshot(DEBUG='True')
        self.assertFalse(local['SECURE_SSL_REDIRECT'])
        self.assertEqual(local['SECURE_HSTS_SECONDS'], 0)
        self.assertFalse(local['SESSION_COOKIE_SECURE'])

    def test_environment_overrides_and_explicit_proxy_opt_in(self):
        result = self.settings_snapshot(TRUST_PROXY_SSL_HEADER='True', SECURE_SSL_REDIRECT='False',
                    SECURE_HSTS_SECONDS='0', SESSION_COOKIE_SECURE='False', CSRF_COOKIE_SECURE='False',
                    SECURE_REFERRER_POLICY='no-referrer', X_FRAME_OPTIONS='SAMEORIGIN')
        self.assertEqual(result['SECURE_PROXY_SSL_HEADER'], ['HTTP_X_FORWARDED_PROTO', 'https'])
        self.assertFalse(result['SECURE_SSL_REDIRECT'])
        self.assertEqual(result['SECURE_HSTS_SECONDS'], 0)
        self.assertFalse(result['CSRF_COOKIE_SECURE'])
        self.assertEqual(result['X_FRAME_OPTIONS'], 'SAMEORIGIN')

    @override_settings(ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=True,
                       SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'),
                       SECURE_HSTS_SECONDS=300, SECURE_HSTS_INCLUDE_SUBDOMAINS=False,
                       SECURE_HSTS_PRELOAD=False)
    def test_proxy_https_does_not_loop_and_plain_http_redirects(self):
        response = self.client.get('/login', HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Strict-Transport-Security'], 'max-age=300')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['Referrer-Policy'], 'same-origin')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        response = self.client.get('/login', HTTP_X_FORWARDED_PROTO='http')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://testserver/login')

    @override_settings(SECURE_SSL_REDIRECT=False, SECURE_PROXY_SSL_HEADER=None)
    def test_forwarded_proto_is_not_trusted_without_opt_in(self):
        from django.test import RequestFactory
        request = RequestFactory().get('/', HTTP_X_FORWARDED_PROTO='https')
        self.assertFalse(request.is_secure())
