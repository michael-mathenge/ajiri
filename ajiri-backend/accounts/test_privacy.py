from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PrivacyRegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.payload = {'email': 'privacy@example.invalid', 'password': 'Forest!Quartz-91',
                        'privacy_consent': True, 'privacy_policy_version': 'privacy-draft-v1'}

    def test_explicit_agreement_records_server_time_and_policy_visible_only_to_owner(self):
        response = self.client.post('/api/accounts/register/', self.payload, format='json')
        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get()
        self.assertIsNotNone(user.profile.privacy_consented_at)
        self.assertEqual(user.profile.privacy_policy_version, 'privacy-draft-v1')
        self.client.force_authenticate(user)
        data = self.client.get('/api/profiles/me/').data
        self.assertTrue(data['privacy_consented_at'])
        self.assertEqual(data['privacy_policy_version'], 'privacy-draft-v1')
        self.client.patch('/api/profiles/me/', {'privacy_policy_version': 'forged'}, format='json')
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.privacy_policy_version, 'privacy-draft-v1')

    def test_missing_false_or_stale_agreement_creates_nothing(self):
        for changes in ({'privacy_consent': False}, {'privacy_policy_version': 'old'},
                        {'privacy_consent': None}):
            self.assertEqual(self.client.post('/api/accounts/register/',
                {**self.payload, **changes}, format='json').status_code, 400)
        data = {k: v for k, v in self.payload.items() if k != 'privacy_consent'}
        self.assertEqual(self.client.post('/api/accounts/register/', data, format='json').status_code, 400)
        self.assertFalse(get_user_model().objects.exists())

    def test_existing_account_and_manager_creation_do_not_infer_agreement(self):
        user = get_user_model().objects.create_user(email='existing@example.invalid', password=None)
        self.assertIsNone(user.profile.privacy_consented_at)
        self.assertEqual(user.profile.privacy_policy_version, '')
