"""Owner choice, ranking and eligibility tests use only disposable synthetic roles."""
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.utils import timezone
from django.db import OperationalError
from profiles.models import Skill
from .models import RecommendationChoice, JobPublication, Application, Notification, DeliveryAttempt
from .matching import calculate_match_score
from .test_saved_searches import SearchFixtures


@override_settings(JOB_FRESHNESS_ENFORCED=True)
class RecommendationTests(SearchFixtures, TestCase):
    suggestions = '/api/jobs/suggestions/'
    dismissed = '/api/jobs/suggestions/dismissed/'

    def choice(self, job, revision=0, dismissed=True, **extra):
        return self.client.patch(f'/api/jobs/{job.pk}/suggestion-choice/',
            {'expected_revision': revision, 'dismissed': dismissed, **extra}, format='json')

    def test_rank_matches_existing_skill_arithmetic_without_a_seventy_percent_cutoff(self):
        python = Skill.objects.create(name='Synthetic Python')
        sql = Skill.objects.create(name='Synthetic SQL')
        self.owner.profile.skills.add(python)
        exact = self.job(); exact.skills_required.add(python)
        half = self.job(); half.skills_required.add(python, sql)
        unknown = self.job()
        rows = self.client.get(self.suggestions).data['results']
        self.assertEqual([r['id'] for r in rows], [exact.pk, half.pk, unknown.pk])
        self.assertEqual([r['match_score'] for r in rows], [100, 50, 0])
        for job, row in zip((exact, half, unknown), rows):
            self.assertEqual(row['match_score'], calculate_match_score(self.owner.profile, job))
            self.assertEqual(row['choice_revision'], 0)

    def test_dismissal_is_reversible_and_does_not_change_browse_application_or_delivery_state(self):
        job = self.job()
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            response = self.choice(job)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['revision'], 1)
            self.assertTrue(response.data['dismissed'])
            self.assertIn('no-store', response['Cache-Control'])
            self.assertEqual(self.client.get(self.suggestions).data['count'], 0)
            self.assertEqual(self.client.get('/api/jobs/').data['count'], 1)
            self.assertEqual(self.client.get(f'/api/jobs/{job.pk}/').status_code, 200)
            self.assertEqual(self.client.get(self.dismissed).data['count'], 1)
            restored = self.choice(job, revision=1, dismissed=False)
            self.assertEqual(restored.status_code, 200)
            self.assertEqual(restored.data['revision'], 2)
            self.assertEqual(self.client.get(self.suggestions).data['count'], 1)
            self.assertEqual(self.client.get(self.dismissed).data['count'], 0)
            provider.assert_not_called()
        self.assertEqual(Application.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(DeliveryAttempt.objects.count(), 0)
        self.assertFalse(self.owner.profile.notify_email)
        self.assertFalse(self.owner.profile.alert_consent_events.exists())

    def test_other_owner_sees_own_revision_and_cannot_restore_someone_elses_choice(self):
        job = self.job()
        self.assertEqual(self.choice(job).status_code, 200)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.dismissed).data['count'], 0)
        self.assertEqual(self.client.get(self.suggestions).data['count'], 1)
        own = self.client.get(f'/api/jobs/{job.pk}/suggestion-choice/')
        self.assertEqual(own.data['revision'], 0)
        self.assertFalse(own.data['dismissed'])
        self.assertEqual(self.choice(job, revision=1, dismissed=False).status_code, 409)
        self.assertEqual(RecommendationChoice.objects.count(), 1)
        self.assertTrue(RecommendationChoice.objects.get(owner=self.owner).dismissed)

    def test_replay_and_stale_restore_do_not_overwrite_a_newer_choice(self):
        job = self.job()
        self.assertEqual(self.choice(job).status_code, 200)
        self.assertEqual(self.choice(job).status_code, 409)
        self.assertEqual(self.choice(job, revision=1, dismissed=False).status_code, 200)
        self.assertEqual(self.choice(job, revision=1).status_code, 409)
        row = RecommendationChoice.objects.get(owner=self.owner, job=job)
        self.assertEqual(row.revision, 2)
        self.assertFalse(row.dismissed)

    def test_expired_or_unverified_roles_never_become_suggestions_or_new_choices(self):
        expired = self.job()
        JobPublication.objects.filter(job=expired).update(closes_at=timezone.now())
        unverified = self.job()
        JobPublication.objects.filter(job=unverified).update(status='unverified')
        self.assertEqual(self.client.get(self.suggestions).data['count'], 0)
        self.assertEqual(self.choice(expired).status_code, 404)
        self.assertEqual(self.choice(unverified).status_code, 404)
        self.assertFalse(RecommendationChoice.objects.exists())

    def test_restoring_an_expired_owned_choice_does_not_restore_eligibility(self):
        job = self.job()
        self.assertEqual(self.choice(job).status_code, 200)
        JobPublication.objects.filter(job=job).update(closes_at=timezone.now())
        self.assertEqual(self.client.get(self.dismissed).data['count'], 1)
        self.assertEqual(self.choice(job, revision=1, dismissed=False).status_code, 200)
        self.assertEqual(self.client.get(self.suggestions).data['count'], 0)
        self.assertEqual(self.client.get(f'/api/jobs/{job.pk}/').status_code, 404)

    def test_same_county_and_zero_experience_filter_contract_applies_to_suggestions(self):
        expected = self.job(county='nairobi-city', work_arrangement='remote', min_experience_years=0)
        self.job(county='mombasa', work_arrangement='remote', min_experience_years=0)
        self.job(county='nairobi-city', work_arrangement='remote', min_experience_years=3)
        self.job(county='nairobi-city', work_arrangement='remote')
        response = self.client.get(self.suggestions, {'county': 'nairobi-city',
            'work_arrangement': 'remote', 'max_experience_years': 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r['id'] for r in response.data['results']], [expected.pk])

    def test_anonymous_strict_input_and_disabled_freshness_fail_closed(self):
        job = self.job()
        self.assertEqual(self.choice(job, owner=self.other.pk).status_code, 400)
        response = self.client.patch(f'/api/jobs/{job.pk}/suggestion-choice/',
            {'expected_revision': 0, 'dismissed': 'false'}, format='json')
        self.assertEqual(response.status_code, 400)
        with override_settings(JOB_FRESHNESS_ENFORCED=False):
            self.assertEqual(self.client.get(self.suggestions).data['count'], 0)
            self.assertEqual(self.choice(job).status_code, 404)
        self.client.force_authenticate(None)
        for path in (self.suggestions, self.dismissed, f'/api/jobs/{job.pk}/suggestion-choice/'):
            self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.choice(job).status_code, 401)

    def test_database_lock_returns_generic_recoverable_error_and_no_choice(self):
        job = self.job()
        with patch('jobs.recommendation_views.RecommendationChoice.objects.filter', side_effect=OperationalError('synthetic')):
            response = self.choice(job)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('synthetic', str(response.data))
        self.assertFalse(RecommendationChoice.objects.exists())
