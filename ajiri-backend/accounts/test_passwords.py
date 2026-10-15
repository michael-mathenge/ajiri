from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .forms import AccountCreationForm


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PasswordPolicyTests(TestCase):
    def test_weak_categories(self):
        for password in ['password', '1234567890', 'short', 'applicant@example.invalid', 'applicant']:
            with self.subTest(password=password):
                response = APIClient().post('/api/accounts/register/', {'email': 'applicant@example.invalid', 'password': password})
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.data['password'], list)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_all_errors_and_good_password(self):
        client = APIClient()
        response = client.post('/api/accounts/register/', {'email': 'applicant@example.invalid', 'password': '123'})
        self.assertGreaterEqual(len(response.data['password']), 3)
        response = client.post('/api/accounts/register/', {'email': 'applicant@example.invalid', 'password': 'Rivers!Quartz78-Orbit'})
        self.assertEqual(response.status_code, 201)

    def test_manager_and_forms(self):
        User = get_user_model()
        for method in [User.objects.create_user, User.objects.create_superuser]:
            with self.assertRaises(ValidationError):
                method(email='manager@example.invalid', password='12345678')
        form = AccountCreationForm(data={'email': 'form@example.invalid', 'password1': '12345678', 'password2': '12345678', 'usable_password': 'true'})
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        user = User.objects.create_user(email='unusable@example.invalid', password=None)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(SetPasswordForm(user, {'new_password1': '12345678', 'new_password2': '12345678'}).is_valid())

    def test_existing_password_unchanged(self):
        user = get_user_model().objects.create_user(email='legacy@example.invalid', password=None)
        user.set_password('12345678')
        user.save()
        response = APIClient().post('/api/accounts/login/', {'email': user.email, 'password': '12345678'})
        self.assertEqual(response.status_code, 200)
