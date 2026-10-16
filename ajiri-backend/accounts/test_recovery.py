from datetime import timedelta
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail, signing
from django.core.cache import caches
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from profiles.models import Profile
from .recovery import VERIFY_SALT, password_fingerprint, verification_token


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', ACCOUNT_EMAIL_TEST_CAPTURE=True,
    ALLOWED_HOSTS=['testserver'], ACCOUNT_LINK_ORIGIN='https://testserver')
class RecoveryTests(TestCase):
    def setUp(self):
        for cache in caches.all():
            cache.clear()
        self.user = get_user_model().objects.create_user(email='recovery@example.invalid', password='Original-river-phrase-2026!')
        self.client = APIClient()
        mail.get_connection()

    def reset_data(self, password='New-forest-phrase-2027!'):
        return {'uid': urlsafe_base64_encode(force_bytes(self.user.pk)),
                'token': default_token_generator.make_token(self.user), 'password': password, 'password_confirm': password}

    def confirm(self, data):
        return self.client.post('/api/accounts/password-reset/confirm/', data)

    def test_known_unknown_inactive_and_unusable_requests_identical(self):
        first = self.client.post('/api/accounts/password-reset/request/', {'email': self.user.email})
        second = self.client.post('/api/accounts/password-reset/request/', {'email': 'absent@example.invalid'})
        self.assertEqual((first.status_code, first.data), (second.status_code, second.data))
        self.assertEqual(len(mail.outbox), 1)
        link = mail.outbox[0].body.split()[-1]
        parsed = urlsplit(link)
        self.assertEqual(parsed.netloc, 'testserver')
        self.assertEqual(parsed.query, '')
        self.assertIn('token', parse_qs(parsed.fragment))
        self.assertNotIn('token', first.data)
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.assertEqual(self.client.post('/api/accounts/password-reset/request/', {'email': self.user.email}).data, first.data)
        self.assertEqual(len(mail.outbox), 1)
        self.user.is_active = True
        self.user.set_unusable_password()
        self.user.save(update_fields=['is_active', 'password'])
        self.assertEqual(self.client.post('/api/accounts/password-reset/request/', {'email': self.user.email}).data, first.data)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(ACCOUNT_EMAIL_TEST_CAPTURE=False)
    def test_disabled_requests_generate_no_token_and_no_email(self):
        with patch('accounts.recovery.default_token_generator.make_token') as token:
            response = self.client.post('/api/accounts/password-reset/request/', {'email': self.user.email})
        self.assertEqual(response.status_code, 202)
        self.assertFalse(response.data['delivery_available'])
        self.assertEqual(mail.outbox, [])
        token.assert_not_called()

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend')
    def test_console_backend_never_receives_security_links(self):
        with patch('accounts.recovery.EmailMessage.send') as send:
            response = self.client.post('/api/accounts/password-reset/request/', {'email': self.user.email})
        self.assertFalse(response.data['delivery_available'])
        send.assert_not_called()

    def test_password_reset_validators_mismatch_and_all_errors(self):
        data = self.reset_data('123')
        data['password_confirm'] = 'different'
        response = self.confirm(data)
        self.assertEqual(response.status_code, 400)
        self.assertGreaterEqual(len(response.data['password']), 2)
        self.assertIn('password_confirm', response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Original-river-phrase-2026!'))
        self.assertIsNone(self.user.profile.password_reset_at)

    def test_success_replay_and_blacklisted_outstanding_refresh(self):
        refresh = RefreshToken.for_user(self.user)
        data = self.reset_data()
        response = self.confirm(data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(data['password']))
        self.assertIsNotNone(Profile.objects.get(user=self.user).password_reset_at)
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=refresh['jti']).exists())
        self.assertEqual(self.confirm(data).status_code, 400)
        self.assertIn('no-store', response['Cache-Control'])

    def test_expiry_tampering_and_email_change(self):
        data = self.reset_data()
        with patch.object(default_token_generator, '_now', return_value=default_token_generator._now()+timedelta(minutes=31)):
            self.assertEqual(self.confirm(data).status_code, 400)
        data['token'] += 'tampered'
        self.assertEqual(self.confirm(data).status_code, 400)
        data = self.reset_data()
        self.user.email = 'changed@example.invalid'
        self.user.save(update_fields=['email'])
        self.assertEqual(self.confirm(data).status_code, 400)
        for uid in ('invalid', 'OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5'):
            data['uid'] = uid
            self.assertEqual(self.confirm(data).status_code, 400)

    def test_verification_is_explicit_idempotent_and_bound_to_email(self):
        token = verification_token(self.user, self.user.profile)
        self.assertIsNone(self.user.profile.email_verified_at)
        for _ in range(2):
            response = self.client.post('/api/accounts/verification/confirm/', {'token': token})
            self.assertEqual(response.status_code, 200)
        profile = Profile.objects.get(user=self.user)
        self.assertIsNotNone(profile.email_verified_at)
        self.assertEqual(profile.verified_email, self.user.email)
        self.user.email = 'new@example.invalid'
        self.user.save(update_fields=['email'])
        self.assertEqual(self.client.post('/api/accounts/verification/confirm/', {'token': token}).status_code, 400)

    def test_verification_expiry_purpose_and_password_reset_invalidation(self):
        token = verification_token(self.user, self.user.profile)
        with patch('django.core.signing.time.time', return_value=timezone.now().timestamp()+86401):
            self.assertEqual(self.client.post('/api/accounts/verification/confirm/', {'token': token}).status_code, 400)
        other = signing.dumps({'uid': self.user.pk}, salt='wrong-purpose')
        self.assertEqual(self.client.post('/api/accounts/verification/confirm/', {'token': other}).status_code, 400)
        self.assertEqual(self.confirm(self.reset_data()).status_code, 200)
        self.assertEqual(self.client.post('/api/accounts/verification/confirm/', {'token': token}).status_code, 400)

    def test_verification_request_requires_auth_and_status_checks_current_address(self):
        self.assertEqual(self.client.get('/api/accounts/verification/status/').status_code, 401)
        self.assertEqual(self.client.post('/api/accounts/verification/request/').status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertFalse(self.client.get('/api/accounts/verification/status/').data['verified'])
        response = self.client.post('/api/accounts/verification/request/')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIsNone(Profile.objects.get(user=self.user).email_verified_at)

    def test_csrf_and_stale_jwt_on_public_requests(self):
        strict = APIClient(enforce_csrf_checks=True)
        for path in ('password-reset/request', 'password-reset/confirm', 'verification/confirm'):
            self.assertEqual(strict.post('/api/accounts/'+path+'/', {}).status_code, 403)
        bootstrap = strict.get('/api/accounts/csrf/', secure=True)
        response = strict.post('/api/accounts/password-reset/request/', {'email': 'absent@example.invalid'},
            secure=True, HTTP_ORIGIN='https://testserver', HTTP_X_CSRFTOKEN=bootstrap.data['csrfToken'],
            HTTP_AUTHORIZATION='Bearer stale')
        self.assertEqual(response.status_code, 202)
        self.assertIn('no-store', response['Cache-Control'])

    def test_target_throttle_shared_across_ips_and_reset_after_window(self):
        with patch('accounts.throttles.AccountTargetThrottle.get_rate', return_value='1/min'):
            self.assertEqual(self.client.post('/api/accounts/password-reset/request/', {'email': 'absent@example.invalid'}, REMOTE_ADDR='192.0.2.1').status_code, 202)
            self.assertEqual(self.client.post('/api/accounts/password-reset/request/', {'email': 'ABSENT@example.invalid'}, REMOTE_ADDR='192.0.2.2').status_code, 429)
            from rest_framework.throttling import SimpleRateThrottle
            with patch.object(SimpleRateThrottle, 'timer', return_value=SimpleRateThrottle.timer()+61):
                self.assertEqual(self.client.post('/api/accounts/password-reset/request/', {'email': 'absent@example.invalid'}, REMOTE_ADDR='192.0.2.2').status_code, 202)

    def test_legacy_untracked_rotated_refresh_revoked_after_reset_new_login_works(self):
        legacy = RefreshToken.for_user(self.user)
        legacy.set_jti()  # Reproduce the pre-fix token missing from outstanding inventory.
        legacy_raw = str(legacy)
        self.assertFalse(OutstandingToken.objects.filter(jti=legacy['jti']).exists())
        self.client.cookies['refresh_token'] = legacy_raw
        before = self.client.post('/api/accounts/refresh/')
        self.assertEqual(before.status_code, 200)
        rotated = before.cookies['refresh_token'].value
        self.assertTrue(OutstandingToken.objects.filter(jti=RefreshToken(rotated)['jti']).exists())
        old_access = before.data['access']
        self.assertEqual(self.confirm(self.reset_data()).status_code, 200)
        for raw in (legacy_raw, rotated):
            self.client.cookies['refresh_token'] = raw
            self.assertEqual(self.client.post('/api/accounts/refresh/').status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+old_access)
        self.assertEqual(self.client.get('/api/accounts/verification/status/').status_code, 200)
        self.client.credentials()
        login = self.client.post('/api/accounts/login/', {'email': self.user.email, 'password': 'New-forest-phrase-2027!'})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.post('/api/accounts/refresh/').status_code, 200)

    def test_fingerprint_refresh_rejected_on_password_change(self):
        refresh = RefreshToken.for_user(self.user)
        refresh['password_version'] = password_fingerprint(self.user)
        self.user.set_password('Another-strong-phrase-2027!')
        self.user.save(update_fields=['password'])
        self.client.cookies['refresh_token'] = str(refresh)
        self.assertEqual(self.client.post('/api/accounts/refresh/').status_code, 401)
