"""Synthetic explicit metadata, zero/unknown semantics and saved-query equivalence."""
import uuid

from django.test import TestCase, override_settings

from .filters import JobFilter
from .models import EmployerJobDraft, Job, SavedSearchMatch
from .saved_searches import collect_due
from .serializers import JobListSerializer, JobDetailSerializer
from .test_saved_searches import SearchFixtures
from . import test_original_source as original
from .vacancy_metadata import COUNTIES


class VacancyFilterTests(TestCase):
    def job(self, **values):
        return Job.objects.create(title='Synthetic role', company_name='Synthetic',
            source_name='Synthetic', source_url='https://example.invalid/'+uuid.uuid4().hex, **values)

    def test_legacy_unknown_is_not_fabricated_from_location_or_description(self):
        job = self.job(location='Nairobi, Kenya', description='Remote role with zero experience')
        for serializer in (JobListSerializer, JobDetailSerializer):
            data = serializer(job).data
            self.assertIsNone(data['county'])
            self.assertIsNone(data['work_arrangement'])
            self.assertIsNone(data['min_experience_years'])
        self.assertEqual(len(COUNTIES), 47)
        self.assertEqual(len({key for key, _ in COUNTIES}), 47)

    def test_combined_filters_and_explicit_zero_exclude_unknown_and_other_requirements(self):
        expected = self.job(county='nairobi-city', work_arrangement='remote', min_experience_years=0)
        self.job(county='nairobi-city', work_arrangement='remote', min_experience_years=2)
        self.job(county='mombasa', work_arrangement='remote', min_experience_years=0)
        self.job(county='nairobi-city', work_arrangement='on_site', min_experience_years=0)
        self.job(county='nairobi-city', work_arrangement='remote')
        query = JobFilter({'county': 'nairobi-city', 'work_arrangement': 'remote', 'max_experience_years': '0'},
                          queryset=Job.objects.all())
        self.assertTrue(query.is_valid(), query.errors)
        self.assertEqual(list(query.qs), [expected])
        self.assertEqual(JobFilter({}, queryset=Job.objects.all()).qs.count(), 5)

    def test_invalid_values_never_silently_broaden_search(self):
        for values in ({'county': 'invented'}, {'work_arrangement': 'maybe'},
                       *({'max_experience_years': v} for v in ('-1', '1.5', 'abc', '81'))):
            with self.subTest(values=values):
                self.assertFalse(JobFilter(values, queryset=Job.objects.none()).is_valid())


@override_settings(SAVED_SEARCHES_ENABLED=True, JOB_FRESHNESS_ENFORCED=True)
class SavedVacancyFilterTests(SearchFixtures, TestCase):
    def test_roundtrip_preserves_zero_and_owner_boundary_without_email_consent(self):
        response = self.client.post('/api/jobs/saved-searches/', {'name': 'Explicit filters',
            'county': 'nairobi-city', 'work_arrangement': 'remote', 'max_experience_years': 0}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['max_experience_years'], 0)
        self.assertEqual(response.data['county'], 'nairobi-city')
        self.assertEqual(response.data['work_arrangement'], 'remote')
        self.assertEqual(response.data['email_frequency'], 'off')
        self.assertFalse(self.owner.profile.alert_consent_events.exists())
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/jobs/saved-searches/'+response.data['id']+'/').status_code, 404)

    def test_due_window_uses_same_filters_and_does_not_hide_low_skill_matches(self):
        expected = self.job(county='nairobi-city', work_arrangement='remote', min_experience_years=0)
        self.job(county='nairobi-city', work_arrangement='remote', min_experience_years=3)
        self.job(county='mombasa', work_arrangement='remote', min_experience_years=0)
        self.job(county='nairobi-city', work_arrangement='remote')
        search = self.search(county='nairobi-city', work_arrangement='remote', max_experience_years=0)
        ids = collect_due(search.pk)
        self.assertEqual(list(SavedSearchMatch.objects.filter(pk__in=ids).values_list('job_id', flat=True)), [expected.pk])
        response = self.client.get('/api/jobs/', {'county': 'nairobi-city', 'work_arrangement': 'remote', 'max_experience_years': 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['id'] for row in response.data['results']], [expected.pk])
        self.assertEqual(response.data['results'][0]['match_score'], 0)

    def test_clear_filters_is_explicit_and_conflicted_edits_preserve_saved_intent(self):
        search = self.search(county='nairobi-city', work_arrangement='remote', max_experience_years=0)
        path = f'/api/jobs/saved-searches/{search.pk}/'
        first = self.client.patch(path, {'expected_revision': 1, 'county': None,
            'work_arrangement': None, 'max_experience_years': None}, format='json')
        self.assertEqual(first.status_code, 200)
        stale = self.client.patch(path, {'expected_revision': 1, 'max_experience_years': 5}, format='json')
        self.assertEqual(stale.status_code, 409)
        search.refresh_from_db()
        self.assertIsNone(search.county)
        self.assertIsNone(search.work_arrangement)
        self.assertIsNone(search.max_experience_years)

    def test_saved_query_rejects_invalid_metadata(self):
        for field, value in [('county', 'invented'), ('work_arrangement', 'maybe'),
                             ('max_experience_years', -1), ('max_experience_years', 0.5), ('max_experience_years', 81)]:
            with self.subTest(field=field, value=value):
                response = self.client.post('/api/jobs/saved-searches/', {'name': 'Invalid', field: value}, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)


@override_settings(JOB_FRESHNESS_ENFORCED=True, EMPLOYER_POSTING_ENABLED=True,
                   PUBLIC_JOB_ORIGIN='https://jobs.example.invalid', PUBLIC_JOBS_ENABLED=False)
class EmployerVacancyMetadataTests(TestCase):
    def setUp(self):
        original.OriginalSourceTests.setUp(self)

    def test_explicit_facts_survive_retry_and_independent_review(self):
        payload = dict(self.payload, county='nairobi-city', work_arrangement='hybrid', min_experience_years=0)
        first = self.client.post(self.url, payload, format='json')
        replay = self.client.post(self.url, payload, format='json')
        self.assertEqual((first.status_code, replay.status_code), (201, 200))
        changed = self.client.post(self.url, dict(payload, min_experience_years=2), format='json')
        self.assertEqual(changed.status_code, 409)
        reviewer = original.User.objects.create_user(email='metadata-reviewer@example.invalid', is_staff=True)
        self.client.force_authenticate(reviewer)
        review = self.client.post(f"{self.url}{first.data['id']}/review/", {'approve': True, 'revision': 1,
            'reason': 'Synthetic independent review of explicit requirements'}, format='json')
        self.assertEqual(review.status_code, 200)
        draft = EmployerJobDraft.objects.get(pk=first.data['id'])
        self.assertEqual((draft.job.county, draft.job.work_arrangement, draft.job.min_experience_years), ('nairobi-city', 'hybrid', 0))

    def test_invalid_facts_are_rejected_and_omitted_facts_remain_unknown(self):
        for field, value in [('county', 'invented'), ('work_arrangement', 'maybe'),
                             ('min_experience_years', -1), ('min_experience_years', 0.5), ('min_experience_years', 81)]:
            with self.subTest(field=field, value=value):
                response = self.client.post(self.url, dict(self.payload, **{field: value}), format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
        response = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data['county'])
        self.assertIsNone(response.data['work_arrangement'])
        self.assertIsNone(response.data['min_experience_years'])
