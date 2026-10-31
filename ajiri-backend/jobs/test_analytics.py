import uuid
from datetime import datetime, timezone as utc_timezone
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.core.management import call_command
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient

from .analytics import choose, record
from .models import AnalyticsChoice, AnalyticsDailyCount


@override_settings(ANALYTICS_ENABLED=True, ANALYTICS_PURPOSE_CONFIRMED=True,
    ANALYTICS_POLICY_VERSION='synthetic-purpose-v1',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AnalyticsTests(TransactionTestCase):
    def setUp(self):
        for cache in caches.all():
            cache.clear()
        self.user = get_user_model().objects.create_user(email='analytics@example.invalid')
        self.other = get_user_model().objects.create_user(email='other-analytics@example.invalid')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def choice(self, enabled=True, key=None, user=None):
        return choose(user or self.user, enabled=enabled, decision_id=key or uuid.uuid4(),
            policy_version='synthetic-purpose-v1')

    def test_independent_explicit_choice_required_and_only_daily_counts_are_stored(self):
        self.assertFalse(record(self.user, 'search_used'))
        self.assertFalse(AnalyticsDailyCount.objects.exists())
        self.choice()
        self.assertTrue(record(self.user, 'search_used'))
        row = AnalyticsDailyCount.objects.get()
        self.assertEqual(row.count, 1)
        self.assertEqual({field.name for field in row._meta.fields}, {'id', 'day', 'event', 'count'})
        self.assertNotIn(self.user.email, str(row.__dict__))
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.notify_email)

    def test_withdrawal_and_old_decision_replay_cannot_restore_collection(self):
        key = uuid.uuid4()
        self.choice(key=key)
        self.choice(False)
        self.choice(key=key)
        self.assertFalse(record(self.user, 'search_used'))
        self.assertFalse(AnalyticsDailyCount.objects.exists())

    def test_disabled_or_unconfirmed_purpose_never_collects_and_withdrawal_still_works(self):
        self.choice()
        for values in ({'ANALYTICS_ENABLED': False}, {'ANALYTICS_PURPOSE_CONFIRMED': False},
                       {'ANALYTICS_POLICY_VERSION': ''}, {'ANALYTICS_POLICY_VERSION': 'new-purpose-v2'}):
            with self.subTest(values=values), override_settings(**values):
                self.assertFalse(record(self.user, 'search_used'))
        with override_settings(ANALYTICS_ENABLED=False):
            self.choice(False)
        self.assertFalse(AnalyticsChoice.objects.order_by('-pk').first().enabled)
        self.assertFalse(AnalyticsDailyCount.objects.exists())

    def test_unknown_attributes_queries_and_documents_are_rejected_at_api_boundary(self):
        self.choice()
        for body in ({'event': 'unknown'}, {'event': 'search_used', 'query': 'private synthetic text'},
                     {'event': 'search_used', 'user_id': self.other.pk}, {'event': 'search_used', 'attributes': {}}):
            self.assertEqual(self.client.post('/api/jobs/analytics/events/', body, format='json').status_code, 400)
        self.assertFalse(AnalyticsDailyCount.objects.exists())
        self.assertEqual(self.client.post('/api/jobs/analytics/events/', {'event': 'search_used'}, format='json').status_code, 204)

    def test_choice_api_owner_isolation_strict_boolean_and_default_off(self):
        key = uuid.uuid4()
        payload = {'decision_id': str(key), 'enabled': 'true', 'policy_version': 'synthetic-purpose-v1'}
        self.assertEqual(self.client.post('/api/jobs/analytics/choice/', payload, format='json').status_code, 400)
        payload['enabled'] = True
        self.assertEqual(self.client.post('/api/jobs/analytics/choice/', payload, format='json').status_code, 200)
        self.client.force_authenticate(self.other)
        self.assertFalse(self.client.get('/api/jobs/analytics/choice/').data['enabled'])
        self.assertEqual(self.client.post('/api/jobs/analytics/choice/', payload, format='json').status_code, 400)
        with override_settings(ANALYTICS_ENABLED=False):
            self.assertEqual(self.client.post('/api/jobs/analytics/events/', {'event': 'search_used'}, format='json').status_code, 404)

    def test_nairobi_day_and_report_only_retention(self):
        at = datetime(2026, 10, 31, 21, 30, tzinfo=utc_timezone.utc)
        with patch('jobs.analytics.timezone.now', return_value=at):
            self.choice()
            self.assertTrue(record(self.user, 'search_used'))
        self.assertEqual(AnalyticsDailyCount.objects.get().day.isoformat(), '2026-11-01')
        output = StringIO()
        call_command('report_analytics_retention', before='2026-11-02', stdout=output)
        self.assertIn('"changed": false', output.getvalue())
        self.assertEqual(AnalyticsDailyCount.objects.count(), 1)
