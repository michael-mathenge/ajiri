"""Private references cannot confer vacancy evidence or application authority."""
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.utils import timezone
from django.db import OperationalError
from .models import SavedJob, JobPublication, JobBrowsingSettings, Application, Notification, DeliveryAttempt
from .freshness import eligible_jobs
from .saved_searches import collect_due
from .test_saved_searches import SearchFixtures


@override_settings(JOB_FRESHNESS_ENFORCED=True, JOB_FEED_DISPLAY_FORCE_OFF=False, SAVED_SEARCHES_ENABLED=True)
class SavedJobTests(SearchFixtures, TestCase):
    def path(self, job):
        return f'/api/jobs/{job.pk}/saved/'

    def test_save_is_idempotent_private_and_preserves_its_original_time(self):
        job = self.job()
        self.assertFalse(self.client.get(self.path(job)).data['saved'])
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            first = self.client.put(self.path(job), {}, format='json')
            second = self.client.put(self.path(job), {}, format='json')
            provider.assert_not_called()
        self.assertEqual((first.status_code, second.status_code), (200, 200))
        self.assertEqual(first.data, second.data)
        self.assertTrue(first.data['saved'])
        self.assertIsNotNone(first.data['saved_at'])
        self.assertIn('no-store', first['Cache-Control'])
        self.assertEqual(SavedJob.objects.count(), 1)
        self.assertEqual(Application.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(DeliveryAttempt.objects.count(), 0)
        self.assertFalse(self.owner.profile.alert_consent_events.exists())

    def test_other_owner_cannot_read_or_remove_my_private_saved_reference(self):
        job = self.job()
        self.client.put(self.path(job), {}, format='json')
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/jobs/saved/').data['count'], 0)
        self.assertFalse(self.client.get(self.path(job)).data['saved'])
        self.assertEqual(self.client.delete(self.path(job)).status_code, 204)
        self.assertTrue(SavedJob.objects.filter(owner=self.owner, job=job).exists())

    def test_supplemental_bookmark_stays_unverified_and_outside_applications_alerts_and_saved_matches(self):
        JobBrowsingSettings.objects.filter(pk=1).update(supplemental_browsing_enabled=True)
        job = self.job(posted_at=timezone.now())
        JobPublication.objects.filter(job=job).update(status='unverified', confirmed_at=None, closes_at=None)
        before = list(eligible_jobs().values_list('pk', flat=True))
        response = self.client.put(self.path(job), {}, format='json')
        self.assertEqual(response.status_code, 200)
        row = self.client.get('/api/jobs/saved/').data['results'][0]
        self.assertFalse(row['job']['can_apply'])
        self.assertTrue(row['job']['display_only'])
        self.assertEqual(list(eligible_jobs().values_list('pk', flat=True)), before)
        self.assertEqual(self.client.post(f'/api/jobs/{job.pk}/apply/', {}, format='json').status_code, 404)
        self.assertEqual(collect_due(self.search().pk), [])
        self.assertEqual(Application.objects.count(), 0)

    def test_expiry_retains_owned_reference_but_never_restores_eligibility(self):
        job = self.job()
        first = self.client.put(self.path(job), {}, format='json')
        JobPublication.objects.filter(job=job).update(closes_at=timezone.now()-timedelta(seconds=1))
        repeated = self.client.put(self.path(job), {}, format='json')
        self.assertEqual(repeated.data, first.data)
        self.assertFalse(self.client.get('/api/jobs/saved/').data['results'][0]['job']['can_apply'])
        self.assertEqual(self.client.get(f'/api/jobs/{job.pk}/').status_code, 404)
        self.assertEqual(self.client.delete(self.path(job)).status_code, 204)
        self.assertEqual(self.client.delete(self.path(job)).status_code, 204)
        self.assertEqual(self.client.put(self.path(job), {}, format='json').status_code, 404)

    def test_hidden_roles_and_arbitrary_payloads_cannot_be_saved_and_anonymous_requests_are_denied(self):
        job = self.job()
        self.assertEqual(self.client.put(self.path(job), {'owner': self.other.pk}, format='json').status_code, 400)
        JobPublication.objects.filter(job=job).update(status='unverified')
        self.assertEqual(self.client.put(self.path(job), {}, format='json').status_code, 404)
        self.assertFalse(SavedJob.objects.exists())
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/jobs/saved/').status_code, 401)
        self.assertEqual(self.client.get(self.path(job)).status_code, 401)
        self.assertEqual(self.client.put(self.path(job), {}, format='json').status_code, 401)
        self.assertEqual(self.client.delete(self.path(job)).status_code, 401)

    def test_list_is_paginated_and_lock_errors_are_generic(self):
        for _ in range(21):
            SavedJob.objects.create(owner=self.owner, job=self.job())
        first = self.client.get('/api/jobs/saved/')
        self.assertEqual(first.data['count'], 21)
        self.assertEqual(len(first.data['results']), 20)
        self.assertTrue(first.data['next'])
        with patch('jobs.saved_job_views.SavedJob.objects.filter', side_effect=OperationalError('synthetic')):
            response = self.client.put(self.path(self.job()), {}, format='json')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('synthetic', str(response.data))
