from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


@override_settings(ALLOWED_HOSTS=['testserver'], CSRF_TRUSTED_ORIGINS=['http://localhost:5173'],
                   PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
                   REFRESH_COOKIE_SECURE=True)
class CookieCSRFTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(email='csrf@example.invalid', password='Valid-phrase-2026!')
        self.client = APIClient(enforce_csrf_checks=True)

    def bootstrap(self):
        response = self.client.get('/api/accounts/csrf/', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('csrftoken', response.cookies)
        self.client.credentials(HTTP_ORIGIN='https://testserver', HTTP_X_CSRFTOKEN=response.data['csrfToken'])
        return response.data['csrfToken']

    def login(self):
        return self.client.post('/api/accounts/login/', {'email': self.user.email, 'password': 'Valid-phrase-2026!'}, secure=True)

    def test_login_refresh_logout_and_replay(self):
        self.bootstrap()
        previous_csrf = self.client.cookies['csrftoken'].value
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {'access'})
        self.assertNotEqual(previous_csrf, self.client.cookies['csrftoken'].value)
        raw = response.cookies['refresh_token'].value
        access = response.data['access']
        self.assertTrue(response.cookies['refresh_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['secure'])
        self.assertEqual(response.cookies['refresh_token']['samesite'], 'Lax')
        self.bootstrap()
        response = self.client.post('/api/accounts/refresh/', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(raw, response.cookies['refresh_token'].value)
        self.client.credentials(HTTP_ORIGIN='https://testserver', HTTP_X_CSRFTOKEN=self.bootstrap(), HTTP_AUTHORIZATION='Bearer '+access)
        self.assertEqual(self.client.post('/api/accounts/logout/', secure=True).status_code, 200)
        self.client.cookies['refresh_token'] = raw
        self.client.credentials(HTTP_ORIGIN='https://testserver', HTTP_X_CSRFTOKEN=self.bootstrap())
        self.assertEqual(self.client.post('/api/accounts/refresh/', secure=True).status_code, 401)

    def test_bad_origins_and_tokens_never_rotate_or_blacklist(self):
        raw = str(RefreshToken.for_user(self.user))
        self.client.cookies['refresh_token'] = raw
        self.bootstrap()
        before = BlacklistedToken.objects.count()
        for origin in [None, 'null', 'https://evil.invalid', 'https://testserver:444', 'https://testserver.evil.invalid']:
            self.client.credentials(HTTP_X_CSRFTOKEN=self.bootstrap())
            if origin is not None:
                self.client.credentials(HTTP_X_CSRFTOKEN=self.bootstrap(), HTTP_ORIGIN=origin)
            for action in ['login', 'refresh', 'logout']:
                response = self.client.post(f'/api/accounts/{action}/', {}, secure=True)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.data['code'], 'csrf_failed')
                self.assertNotIn('refresh_token', response.cookies)
            self.assertEqual(BlacklistedToken.objects.count(), before)
        for token in ['', 'wrong', 'a'*64]:
            self.client.credentials(HTTP_ORIGIN='https://testserver', HTTP_X_CSRFTOKEN=token)
            self.assertEqual(self.client.post('/api/accounts/refresh/', secure=True).status_code, 403)
        self.client.cookies.pop('csrftoken', None)
        self.assertEqual(self.client.post('/api/accounts/refresh/', secure=True).status_code, 403)

    def test_existing_session_bootstraps_and_invalid_token_stays_401(self):
        self.client.cookies['refresh_token'] = str(RefreshToken.for_user(self.user))
        self.assertEqual(self.client.post('/api/accounts/refresh/', secure=True).status_code, 403)
        token = self.bootstrap()
        self.assertEqual(self.client.post('/api/accounts/refresh/', secure=True).status_code, 200)
        self.client.cookies['refresh_token'] = 'invalid'
        self.assertEqual(self.client.post('/api/accounts/refresh/', secure=True).status_code, 401)
        self.client.credentials(HTTP_ORIGIN='http://localhost:5173', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(self.client.post('/api/accounts/refresh/', secure=True).status_code, 401)

    def test_bootstrap_excludes_jwt_authentication(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer expired')
        self.assertEqual(self.client.get('/api/accounts/csrf/', secure=True).status_code, 200)
