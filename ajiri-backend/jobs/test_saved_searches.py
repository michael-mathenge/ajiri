"""Synthetic owner isolation, frequency windows and closed email-accounting integration."""
from datetime import datetime, timedelta, timezone as dt_timezone
import uuid
from unittest.mock import patch

from django.core.cache import caches
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from profiles.alert_consent import record_choice
from .brevo_transport import Result
from .models import Job, JobPublication, SavedSearch, SavedSearchMatch, DeliveryAttempt, DeliveryDailyBudget
from .saved_searches import collect_due, next_window, reset_windows
from .saved_search_email import capture_due_email


class SearchFixtures:
    def setUp(self):
        for cache in caches.all():
            cache.clear()
        self.owner = User.objects.create_user(email='saved@example.invalid', password='Synthetic-Pass-982!')
        self.other = User.objects.create_user(email='other-saved@example.invalid')
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        self.start = timezone.now() - timedelta(days=2)

    def search(self, **values):
        search = SavedSearch(owner=self.owner, name='Synthetic Python', q='Python',
            in_app_frequency='daily', **values)
        reset_windows(search, self.start)
        search.save()
        return search

    def job(self, **values):
        job = Job.objects.create(title=values.pop('title', 'Python engineer'), company_name='Synthetic',
            source_url='https://example.invalid/' + uuid.uuid4().hex, source_name='synthetic', **values)
        Job.objects.filter(pk=job.pk).update(scraped_at=self.start+timedelta(minutes=10))
        JobPublication.objects.create(job=job, origin='rss', status='published',
            closes_at=timezone.now()+timedelta(days=2), confirmed_at=timezone.now())
        return job

    def consent(self):
        profile = self.owner.profile
        profile.email_verified_at = timezone.now()
        profile.verified_email = self.owner.email
        profile.save()
        record_choice(self.owner, True, uuid.uuid4())
        profile.alert_consent_events.update(created_at=self.start-timedelta(minutes=10))


@override_settings(SAVED_SEARCHES_ENABLED=True, JOB_FRESHNESS_ENFORCED=True)
class SavedSearchTests(SearchFixtures, TestCase):
    def test_creation_is_private_and_never_grants_consent_or_sends(self):
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            response = self.client.post('/api/jobs/saved-searches/',
                {'name': 'Synthetic', 'q': 'Python', 'email_frequency': 'weekly'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['in_app_frequency'], 'off')
        self.assertEqual(response.data['email_delivery'], 'disabled')
        self.assertIn('no-store', response['Cache-Control'])
        self.owner.profile.refresh_from_db()
        self.assertFalse(self.owner.profile.notify_email)
        self.assertFalse(self.owner.profile.alert_consent_events.exists())
        self.assertEqual(DeliveryAttempt.objects.count(), 0)
        self.assertEqual(DeliveryDailyBudget.objects.count(), 0)
        provider.assert_not_called()

    def test_other_owner_cannot_read_change_delete_or_view_results(self):
        search = self.search()
        self.client.force_authenticate(self.other)
        root = f'/api/jobs/saved-searches/{search.pk}/'
        for method, url, data in [('get', root, {}), ('patch', root, {'name': 'stolen', 'expected_revision': 1}),
                                  ('delete', root, {}), ('get', root+'matches/', {})]:
            response = getattr(self.client, method)(url, data, format='json')
            self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get('/api/jobs/saved-searches/').data['count'], 0)

    def test_anonymous_and_disabled_route_fail_closed(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/jobs/saved-searches/').status_code, 401)
        self.client.force_authenticate(self.owner)
        with override_settings(SAVED_SEARCHES_ENABLED=False):
            self.assertEqual(self.client.get('/api/jobs/saved-searches/').status_code, 403)
            search = self.search()
            self.job()
            self.assertEqual(collect_due(search.pk), [])

    def test_limit_and_validation_do_not_accept_arbitrary_fields_or_queries(self):
        for index in range(10):
            self.assertEqual(self.client.post('/api/jobs/saved-searches/', {'name': str(index)}).status_code, 201)
        self.assertEqual(self.client.post('/api/jobs/saved-searches/', {'name': 'eleven'}).status_code, 400)
        self.assertEqual(SavedSearch.objects.count(), 10)
        for values in [{'owner': self.other.pk}, {'q': 'a'*65}, {'email_frequency': 'hourly'}, {'job_type': 'invalid'}]:
            self.assertEqual(self.client.post('/api/jobs/saved-searches/', {'name': 'bad', **values}, format='json').status_code, 400)

    def test_update_claims_revision_and_resets_history_without_inferred_consent(self):
        search = self.search()
        self.job()
        self.assertEqual(len(collect_due(search.pk)), 1)
        url = f'/api/jobs/saved-searches/{search.pk}/'
        self.assertEqual(self.client.patch(url, {'q': 'Testing'}, format='json').status_code, 400)
        response = self.client.patch(url, {'q': 'Testing', 'expected_revision': 1}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['revision'], 2)
        self.assertEqual(self.client.patch(url, {'q': 'stale', 'expected_revision': 1}, format='json').status_code, 409)
        self.assertEqual(self.client.get(url+'matches/').data['count'], 0)
        self.assertEqual(SavedSearchMatch.objects.count(), 1)  # Historical preference evidence retained.

    def test_due_window_is_deduplicated_and_only_current_new_matching_jobs_appear(self):
        search = self.search()
        current = self.job()
        old = self.job()
        Job.objects.filter(pk=old.pk).update(scraped_at=self.start-timedelta(minutes=1))
        self.job(title='Unrelated accountancy')
        scam = self.job(is_flagged_scam=True)
        expired = self.job()
        JobPublication.objects.filter(job=expired).update(closes_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(len(collect_due(search.pk)), 1)
        self.assertEqual(collect_due(search.pk), [])
        self.assertEqual(list(SavedSearchMatch.objects.values_list('job_id', flat=True)), [current.pk])
        url = f'/api/jobs/saved-searches/{search.pk}/matches/'
        self.assertEqual([x['id'] for x in self.client.get(url).data['results']], [current.pk])
        JobPublication.objects.filter(job=current).update(closes_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.client.get(url).data['count'], 0)
        self.assertNotEqual(scam.pk, current.pk)

    def test_independent_in_app_choice_honors_global_preference(self):
        search = self.search(email_frequency='daily')
        self.job()
        self.owner.profile.notify_in_app = False
        self.owner.profile.save()
        self.assertEqual(collect_due(search.pk), [])
        self.assertEqual(SavedSearchMatch.objects.count(), 0)

    def test_missing_profile_does_not_create_matches_or_fail_the_sweep(self):
        search = self.search()
        self.job()
        self.owner.profile.delete()
        self.assertEqual(collect_due(search.pk), [])
        self.assertFalse(SavedSearchMatch.objects.exists())

    def test_nairobi_daily_and_weekly_boundaries(self):
        at = datetime(2026, 10, 20, 21, 30, tzinfo=dt_timezone.utc)
        self.assertEqual(next_window(at, 'daily').isoformat(), '2026-10-22T00:00:00+03:00')
        self.assertEqual(next_window(at, 'weekly').isoformat(), '2026-10-28T00:00:00+03:00')
        self.assertIsNone(next_window(at, 'off'))

    def test_weekly_search_waits_seven_days_and_caps_the_current_window(self):
        # Keep samples inside the completed week, even within ten minutes of Nairobi midnight.
        self.start = timezone.now() - timedelta(days=3)
        search = self.search()
        search.in_app_frequency = 'weekly'
        reset_windows(search, self.start)
        search.save()
        self.job()
        self.assertEqual(collect_due(search.pk), [])
        reset_windows(search, timezone.now()-timedelta(days=8))
        search.save()
        for _ in range(52):
            self.job()
        self.assertEqual(len(collect_due(search.pk)), 50)
        self.assertEqual(collect_due(search.pk), [])

    def test_busy_sweep_keeps_the_due_window_available(self):
        from django.db import OperationalError
        from .saved_searches import run_due_saved_searches
        search = self.search()
        old = search.next_in_app_at
        with patch('jobs.saved_searches.collect_due', side_effect=OperationalError('synthetic')):
            self.assertEqual(run_due_saved_searches(), 0)
        search.refresh_from_db()
        self.assertEqual(search.next_in_app_at, old)

    def test_preferences_cascade_only_with_their_owner(self):
        search = self.search()
        self.job()
        collect_due(search.pk)
        self.owner.delete()  # Synthetic fixture only, never a production erasure operation.
        self.assertFalse(SavedSearch.objects.exists())
        self.assertFalse(SavedSearchMatch.objects.exists())
        self.assertTrue(User.objects.filter(pk=self.other.pk).exists())

    def test_sweep_connects_in_app_without_changing_existing_match_count_or_sending(self):
        from .matching import sweep_all_active_jobs_for_matches
        self.search()
        self.job()
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            self.assertEqual(sweep_all_active_jobs_for_matches(), 0)
        self.assertEqual(SavedSearchMatch.objects.count(), 1)
        provider.assert_not_called()

    def test_deleting_preference_removes_private_matches_and_stops_collection(self):
        search = self.search()
        self.job()
        collect_due(search.pk)
        self.assertEqual(self.client.delete(f'/api/jobs/saved-searches/{search.pk}/').status_code, 204)
        self.assertEqual(collect_due(search.pk), [])
        self.assertFalse(SavedSearchMatch.objects.exists())


@override_settings(SAVED_SEARCHES_ENABLED=True, JOB_FRESHNESS_ENFORCED=True,
    SAVED_SEARCH_EMAIL_TEST_CAPTURE=True, ACCOUNT_EMAIL_TEST_CAPTURE=True, REAL_EMAIL_ENABLED=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', ACCOUNT_LINK_ORIGIN='https://example.invalid')
class SavedSearchEmailTests(SearchFixtures, TransactionTestCase):
    def test_memory_acceptance_uses_shared_ledger_and_overlapping_searches_never_duplicate(self):
        self.consent()
        first, second = self.search(email_frequency='daily'), self.search(email_frequency='daily')
        self.job()
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            self.assertEqual(capture_due_email(first.pk), ['accepted'])
            self.assertEqual(capture_due_email(first.pk), [])
            self.assertEqual(capture_due_email(second.pk), ['accepted'])
        self.assertEqual(DeliveryAttempt.objects.count(), 1)
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').alert_reserved, 1)
        provider.assert_not_called()

    def test_saving_email_frequency_and_legacy_flag_are_not_consent(self):
        search = self.search(email_frequency='daily')
        self.job()
        self.owner.profile.notify_email = True
        self.owner.profile.save()
        self.assertEqual(capture_due_email(search.pk), [])
        self.assertEqual(DeliveryAttempt.objects.count(), 0)

    def test_real_mode_cannot_open_the_memory_integration_or_mutate_ledger(self):
        self.consent()
        search = self.search(email_frequency='daily')
        self.job()
        with override_settings(REAL_EMAIL_ENABLED=True), patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            self.assertEqual(capture_due_email(search.pk), [])
        self.assertFalse(SavedSearchMatch.objects.exists())
        self.assertFalse(DeliveryAttempt.objects.exists())
        provider.assert_not_called()

    def test_unknown_outcome_is_not_retried(self):
        self.consent()
        search = self.search(email_frequency='daily')
        self.job()
        with patch('jobs.saved_search_email.MemoryTransport.send', return_value=Result('unknown')) as transport:
            self.assertEqual(capture_due_email(search.pk), ['unknown'])
            self.assertEqual(capture_due_email(search.pk), [])
        transport.assert_called_once()
        self.assertEqual(DeliveryAttempt.objects.count(), 1)

    def test_revocation_at_transport_boundary_prevents_memory_handoff(self):
        self.consent()
        search = self.search(email_frequency='daily')
        self.job()
        from .saved_search_email import RecheckedMemoryTransport
        original = RecheckedMemoryTransport.send
        def revoke(transport, payload):
            record_choice(self.owner, False, uuid.uuid4())
            return original(transport, payload)
        with patch.object(RecheckedMemoryTransport, 'send', revoke), patch('jobs.saved_search_email.MemoryTransport.send') as memory:
            self.assertEqual(capture_due_email(search.pk), ['definite_failure'])
        memory.assert_not_called()
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').alert_reserved, 1)

    def test_changed_verified_recipient_cannot_receive_a_prepared_payload_for_the_old_address(self):
        self.consent()
        search = self.search(email_frequency='daily')
        self.job()
        from .saved_search_email import RecheckedMemoryTransport
        original = RecheckedMemoryTransport.send
        def change_recipient(transport, payload):
            User.objects.filter(pk=self.owner.pk).update(email='changed@example.invalid')
            self.owner.profile.__class__.objects.filter(user=self.owner).update(verified_email='changed@example.invalid')
            return original(transport, payload)
        with patch.object(RecheckedMemoryTransport, 'send', change_recipient), patch('jobs.saved_search_email.MemoryTransport.send') as memory:
            self.assertEqual(capture_due_email(search.pk), ['definite_failure'])
        memory.assert_not_called()

    def test_search_revision_changed_before_handoff_does_not_send(self):
        self.consent()
        search = self.search(email_frequency='daily')
        self.job()
        from .saved_search_email import RecheckedMemoryTransport
        original = RecheckedMemoryTransport.send
        def change_search(transport, payload):
            SavedSearch.objects.filter(pk=search.pk).update(revision=2, q='Different')
            return original(transport, payload)
        with patch.object(RecheckedMemoryTransport, 'send', change_search), patch('jobs.saved_search_email.MemoryTransport.send') as memory:
            self.assertEqual(capture_due_email(search.pk), ['definite_failure'])
        memory.assert_not_called()

    def test_quota_exhaustion_cannot_repeat_a_network_handoff(self):
        self.consent()
        search = self.search(email_frequency='daily')
        self.job()
        from .delivery_service import QuotaExceeded
        with patch('jobs.saved_search_email.DeliveryService.deliver', side_effect=QuotaExceeded()), patch('jobs.saved_search_email.MemoryTransport.send') as memory:
            self.assertEqual(capture_due_email(search.pk), [])
        self.assertFalse(DeliveryAttempt.objects.exists())
        memory.assert_not_called()
