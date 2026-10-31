"""Compatibility tests use synthetic local data and never send email."""
import json
from pathlib import Path
from django.test import TestCase, override_settings
from django.urls import URLPattern, URLResolver, resolve
from rest_framework.test import APIClient
from accounts.models import User
from config.v1_urls import urlpatterns


def routes(patterns, prefix=''):
    for pattern in patterns:
        part = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            yield from routes(pattern.url_patterns, part)
        elif isinstance(pattern, URLPattern):
            yield part, pattern.callback


@override_settings(SECURE_SSL_REDIRECT=False, REFRESH_COOKIE_SECURE=False,
                   CSRF_COOKIE_SECURE=False, REAL_EMAIL_ENABLED=False, ALERT_EMAIL_ENABLED=False)
class APIContractTests(TestCase):
    def test_every_versioned_alias_uses_the_exact_legacy_view(self):
        replacements = {'<int:pk>': '1', '<uuid:version>': '00000000-0000-0000-0000-000000000001',
            '<uuid:pk>': '00000000-0000-0000-0000-000000000004',
            '<uuid:certification_id>': '00000000-0000-0000-0000-000000000005',
            '<uuid:task_id>': '00000000-0000-0000-0000-000000000006',
            '<uuid:package_id>': '00000000-0000-0000-0000-000000000002',
            '<uuid:authorization_id>': '00000000-0000-0000-0000-000000000003', '<str:kind>': 'cv'}
        count = 0
        for route, callback in routes(urlpatterns):
            for key, value in replacements.items():
                route = route.replace(key, value)
            self.assertIs(resolve('/api/' + route).func.view_class, callback.view_class)
            self.assertIs(resolve('/api/v1/' + route).func.view_class, callback.view_class)
            count += 1
        self.assertGreater(count, 35)

    def test_private_aliases_deny_anonymous_and_do_not_add_ingestion_aliases(self):
        client = APIClient()
        for path in ('jobs/', 'profiles/me/', 'jobs/applications/', 'profiles/me/cv/'):
            self.assertEqual(client.get('/api/v1/' + path).status_code, 401)
        self.assertEqual(client.post('/api/v1/jobs/ingest/', {}, format='json').status_code, 404)
        self.assertEqual(client.post('/api/v1/jobs/sweep/', {}, format='json').status_code, 404)
        self.assertEqual(client.get('/api/v1/health/').status_code, 200)

    def test_versioned_login_and_legacy_refresh_share_cookie_csrf_protocol(self):
        User.objects.create_user(email='contract@example.invalid', password='Synthetic-river-2027!')
        client = APIClient(enforce_csrf_checks=True)
        token = client.get('/api/v1/accounts/csrf/').data['csrfToken']
        response = client.post('/api/v1/accounts/login/',
            {'email': 'contract@example.invalid', 'password': 'Synthetic-river-2027!'},
            format='json', HTTP_ORIGIN='http://testserver', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {'access'})
        self.assertEqual(response.cookies['refresh_token']['path'], '/')
        self.assertTrue(response.cookies['refresh_token']['httponly'])
        old_cookie = response.cookies['refresh_token'].value
        self.assertEqual(client.post('/api/accounts/refresh/', {}, format='json').status_code, 403)
        token = client.get('/api/accounts/csrf/').data['csrfToken']
        response = client.post('/api/accounts/refresh/', {}, format='json',
            HTTP_ORIGIN='http://testserver', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {'access'})
        self.assertNotEqual(response.cookies['refresh_token'].value, old_cookie)

    def test_published_schema_is_source_only_and_rejects_writes(self):
        client = APIClient()
        response = client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        document = json.loads(b''.join(response.streaming_content))
        self.assertEqual(document['openapi'], '3.0.3')
        self.assertEqual(document['info']['version'], '1.0.0')
        self.assertGreater(len(document['paths']), 35)
        self.assertTrue(all(path.startswith('/api/v1/') for path in document['paths']))
        self.assertFalse(any('/ingest/' in path or '/sweep/' in path for path in document['paths']))
        self.assertEqual(client.post('/api/schema/', {}, format='json').status_code, 405)
        self.assertEqual(document, json.loads(Path(__file__).with_name('openapi.json').read_text()))
        login = document['paths']['/api/v1/accounts/login/']['post']
        self.assertTrue(any(p['name'] == 'X-CSRFToken' and p['required'] for p in login['parameters']))
        self.assertEqual(document['paths']['/api/v1/accounts/refresh/']['post']['security'], [{'refreshCookie': []}])
        operation_ids = [value['operationId'] for item in document['paths'].values()
                         for key, value in item.items() if key in ('get', 'post', 'patch', 'put', 'delete')]
        self.assertEqual(len(operation_ids), len(set(operation_ids)))
