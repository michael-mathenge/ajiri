from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class ProfilePreferencesTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(email='profile@example.com', password='test-password')
        self.client = APIClient()

    def test_preferences_require_authentication(self):
        self.assertEqual(self.client.get('/api/profiles/me/').status_code, 401)
        self.assertEqual(self.client.patch('/api/profiles/me/', {'notify_email': False}).status_code, 401)

    def test_preferences_can_be_read_and_updated_independently(self):
        self.client.force_authenticate(self.user)
        data = self.client.get('/api/profiles/me/').data
        self.assertTrue(data['notify_email'])
        self.assertTrue(data['notify_in_app'])
        response = self.client.patch('/api/profiles/me/', {'notify_email': False}, format='json')
        self.assertFalse(response.data['notify_email'])
        self.assertTrue(response.data['notify_in_app'])
        response = self.client.patch('/api/profiles/me/', {'notify_in_app': False}, format='json')
        self.assertFalse(response.data['notify_in_app'])
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.notify_in_app)

    def test_invalid_preference_is_rejected(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch('/api/profiles/me/', {'notify_in_app': 'invalid'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('notify_in_app', response.data)
