import uuid
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from rest_framework.test import APIClient
from .alert_consent import POLICY, eligible, record_choice, unsubscribe, unsubscribe_token
from .models import AlertConsentEvent


class AlertConsentTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(email='consent@example.invalid', password='Synthetic-only-123')
        self.client = APIClient()
        self.url = '/api/profiles/me/alert-preferences/'

    def verify_address(self):
        p = self.user.profile
        p.email_verified_at = timezone.now(); p.verified_email = self.user.email
        p.save()

    def test_new_default_and_legacy_true_never_imply_consent(self):
        p = self.user.profile
        self.assertFalse(p.notify_email)
        self.assertTrue(p.notify_in_app)
        p.notify_email = True; p.save(); self.verify_address()
        self.assertFalse(eligible(p))
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertTrue(response.data['enabled'])
        self.assertFalse(response.data['confirmed'])
        self.assertIn('no-store', response['Cache-Control'])

    def test_authenticated_explicit_current_policy_choice_and_profile_cannot_bypass(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(self.url, {'enabled': True}, format='json').status_code, 400)
        self.assertEqual(self.client.patch('/api/profiles/me/', {'notify_email': True}, format='json').status_code, 400)
        self.user.profile.refresh_from_db(); self.assertFalse(self.user.profile.notify_email)
        result = self.client.post(self.url, {'enabled': True, 'decision_id': str(uuid.uuid4()),
            'policy_version': POLICY}, format='json')
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.data['confirmed']); self.assertFalse(result.data['eligible'])
        self.verify_address(); self.assertTrue(eligible(self.user.profile))

    def test_duplicate_decision_does_not_reverse_newer_revocation(self):
        key = uuid.uuid4()
        record_choice(self.user, True, key)
        record_choice(self.user, False, uuid.uuid4())
        record_choice(self.user, True, key)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.notify_email)
        self.assertEqual(AlertConsentEvent.objects.count(), 2)
        with self.assertRaises(ValueError): record_choice(self.user, False, key)
        self.user.profile.refresh_from_db(); self.assertFalse(self.user.profile.notify_email)

    def test_address_change_invalidates_proof_and_old_unsubscribe_link(self):
        self.verify_address(); record_choice(self.user, True, uuid.uuid4())
        token = unsubscribe_token(self.user.profile)
        self.user.email = 'changed@example.invalid'; self.user.save()
        self.assertFalse(eligible(self.user.profile))
        with self.assertRaises(ValueError): unsubscribe(token, confirm=True)
        self.user.profile.refresh_from_db(); self.assertTrue(self.user.profile.notify_email)

    def test_unsubscribe_preview_no_mutation_confirmation_idempotent_in_app_unchanged(self):
        record_choice(self.user, True, uuid.uuid4())
        token = unsubscribe_token(self.user.profile)
        url = '/api/profiles/alert-unsubscribe/'
        self.assertEqual(self.client.get(url, {'token': token}).status_code, 405)
        self.assertEqual(self.client.post(url, {'token': token}, format='json').status_code, 200)
        self.user.profile.refresh_from_db(); self.assertTrue(self.user.profile.notify_email)
        for _ in range(2):
            self.assertEqual(self.client.post(url, {'token': token, 'confirm': True}, format='json').status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.notify_email); self.assertTrue(self.user.profile.notify_in_app)
        self.assertEqual(AlertConsentEvent.objects.count(), 2)

    def test_invalid_expired_or_wrong_purpose_token_has_no_effect(self):
        record_choice(self.user, True, uuid.uuid4())
        for token in ('invalid', signing.dumps({'profile': self.user.profile.pk}, salt='other')):
            with self.assertRaises(ValueError): unsubscribe(token, confirm=True)
        with patch('profiles.alert_consent.signing.loads', side_effect=signing.SignatureExpired):
            with self.assertRaises(ValueError): unsubscribe('expired', confirm=True)
        self.user.profile.refresh_from_db(); self.assertTrue(self.user.profile.notify_email)


class AlertConsentMigrationTests(TransactionTestCase):
    def test_existing_values_preserved_and_no_consent_inferred(self):
        executor = MigrationExecutor(connection)
        leaves = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(leaves))
        before = [('profiles', '0006_privacy_notice')]
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        User = apps.get_model('accounts', 'User')
        Profile = apps.get_model('profiles', 'Profile')
        ids = []
        for index, enabled in enumerate((True, False)):
            user = User.objects.create(email=f'legacy-{index}@example.invalid', password='unchanged')
            ids.append(Profile.objects.create(user_id=user.pk, notify_email=enabled, notify_in_app=False).pk)
        executor = MigrationExecutor(connection)
        executor.migrate(leaves)
        current = executor.loader.project_state(leaves).apps
        Profile = current.get_model('profiles', 'Profile')
        self.assertEqual(list(Profile.objects.filter(pk__in=ids).order_by('pk').values_list('notify_email', flat=True)), [True, False])
        self.assertFalse(current.get_model('profiles', 'AlertConsentEvent').objects.exists())
        user = current.get_model('accounts', 'User').objects.create(email='new-default@example.invalid', password='unchanged')
        self.assertFalse(Profile.objects.create(user_id=user.pk).notify_email)

