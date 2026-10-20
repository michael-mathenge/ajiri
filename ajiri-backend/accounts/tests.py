from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AuthFlowTests(TestCase):
    # Fast hashing is isolated to these synthetic tests; real settings stay unchanged.
    # see docs/CONCEPTS.md#isolated-auth-tests
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.payload = {'email': 'auth@example.com', 'password': 'test-password', 'full_name': 'Test User', 'phone_number': '0700000000', 'privacy_consent': True, 'privacy_policy_version': 'privacy-draft-v1'}

    def register_and_login(self):
        self.assertEqual(self.client.post('/api/accounts/register/', self.payload).status_code, 201)
        return self.client.post('/api/accounts/login/', {'email': self.payload['email'], 'password': self.payload['password']})

    def test_registration_hashes_password_and_creates_profile(self):
        response = self.client.post('/api/accounts/register/', self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('password', response.data)
        user = get_user_model().objects.get(email=self.payload['email'])
        self.assertNotEqual(user.password, self.payload['password'])
        self.assertTrue(user.check_password(self.payload['password']))
        self.assertEqual(user.profile.user, user)

    def test_registration_returns_multiple_field_errors_and_duplicate_email(self):
        self.client.post('/api/accounts/register/', self.payload)
        response = self.client.post('/api/accounts/register/', {**self.payload, 'password': 'short'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)

    def test_login_returns_access_only_and_httponly_refresh_cookie(self):
        response = self.register_and_login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {'access'})
        AccessToken(response.data['access'])
        cookie = response.cookies['refresh_token']
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'Lax')
        self.assertEqual(cookie['path'], '/')

    def test_invalid_credentials_and_inactive_user(self):
        self.register_and_login()
        self.assertEqual(self.client.post('/api/accounts/login/', {'email': self.payload['email'], 'password': 'wrong'}).status_code, 401)
        user = get_user_model().objects.get(email=self.payload['email'])
        user.is_active = False
        user.save()
        self.assertEqual(self.client.post('/api/accounts/login/', self.payload).status_code, 401)

    def test_refresh_rotates_and_blacklists_previous_cookie(self):
        response = self.register_and_login()
        previous = response.cookies['refresh_token'].value
        for _ in range(2):
            response = self.client.post('/api/accounts/refresh/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(set(response.data), {'access'})
            rotated = response.cookies['refresh_token'].value
            self.assertNotEqual(previous, rotated)
            replay = APIClient()
            replay.cookies['refresh_token'] = previous
            self.assertEqual(replay.post('/api/accounts/refresh/').status_code, 401)
            previous = rotated

    def test_missing_invalid_and_expired_refresh_tokens(self):
        self.assertEqual(self.client.post('/api/accounts/refresh/').status_code, 401)
        self.client.cookies['refresh_token'] = 'invalid'
        self.assertEqual(self.client.post('/api/accounts/refresh/').status_code, 401)
        token = RefreshToken()
        token['exp'] = 1
        self.client.cookies['refresh_token'] = str(token)
        self.assertEqual(self.client.post('/api/accounts/refresh/').status_code, 401)

    def test_logout_blacklists_cookie_and_protected_endpoints_reject_no_access(self):
        response = self.register_and_login()
        raw_refresh = response.cookies['refresh_token'].value
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        response = self.client.post('/api/accounts/logout/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies['refresh_token']['max-age'], 0)
        replay = APIClient()
        replay.cookies['refresh_token'] = raw_refresh
        self.assertEqual(replay.post('/api/accounts/refresh/').status_code, 401)
        self.assertEqual(replay.get('/api/profiles/me/').status_code, 401)
        self.assertEqual(APIClient().post('/api/accounts/logout/').status_code, 401)

    def test_expired_access_is_rejected_but_cookie_can_refresh(self):
        response = self.register_and_login()
        access = AccessToken(response.data['access'])
        access['exp'] = 1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(self.client.get('/api/profiles/me/').status_code, 401)
        # The browser's public-endpoint exclusion prevents stale headers on refresh.
        self.client.credentials()
        response = self.client.post('/api/accounts/refresh/')
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertEqual(self.client.get('/api/profiles/me/').status_code, 200)
