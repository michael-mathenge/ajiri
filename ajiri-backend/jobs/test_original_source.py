from datetime import timedelta
from io import StringIO
import json
import uuid

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from jobs.models import EmployerJobDraft, EmployerOrganisation, Job, JobPublication
from jobs.serializers import JobListSerializer

User = get_user_model()


@override_settings(JOB_FRESHNESS_ENFORCED=True, EMPLOYER_POSTING_ENABLED=True,
                   PUBLIC_JOB_ORIGIN='https://jobs.example.invalid', PUBLIC_JOBS_ENABLED=False)
class OriginalSourceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='original-owner@example.invalid')
        profile = self.owner.profile
        profile.email_verified_at = timezone.now()
        profile.verified_email = self.owner.email
        profile.save()
        self.organisation = EmployerOrganisation.objects.create(
            owner=self.owner, name='Synthetic original employer', website='https://example.invalid', status='approved')
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        self.payload = {'submission_id': str(uuid.uuid4()), 'organisation': self.organisation.pk,
                        'title': 'Synthetic original role', 'description': 'Synthetic responsibilities. ' * 8,
                        'requirements': '', 'location': 'Nairobi, Kenya', 'job_type': 'full_time',
                        'application_url': 'https://example.invalid/apply',
                        'closes_at': (timezone.now() + timedelta(days=2)).isoformat()}
        self.url = '/api/jobs/employers/drafts/'

    def test_uncertain_request_replay_records_one_pending_vacancy(self):
        first = self.client.post(self.url, self.payload, format='json')
        second = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data['id'], second.data['id'])
        self.assertEqual(EmployerJobDraft.objects.count(), 1)
        self.assertEqual(second.data['status'], 'pending')
        self.assertFalse(Job.objects.exists())
        self.assertFalse(JobPublication.objects.exists())

    def test_same_decision_cannot_be_reused_for_changed_details(self):
        self.client.post(self.url, self.payload, format='json')
        changed = dict(self.payload, title='Changed role')
        response = self.client.post(self.url, changed, format='json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(EmployerJobDraft.objects.get().title, self.payload['title'])

    def test_omitting_optional_fields_cannot_change_the_replayed_intent(self):
        payload = dict(self.payload, requirements='Specific synthetic requirements', job_type='contract')
        self.assertEqual(self.client.post(self.url, payload, format='json').status_code, 201)
        omitted = {key: value for key, value in payload.items() if key not in ('requirements', 'job_type')}
        self.assertEqual(self.client.post(self.url, omitted, format='json').status_code, 409)

    def test_another_owner_cannot_replay_or_read_the_existing_submission(self):
        self.client.post(self.url, self.payload, format='json')
        other = User.objects.create_user(email='other-original@example.invalid')
        profile = other.profile
        profile.email_verified_at = timezone.now()
        profile.verified_email = other.email
        profile.save()
        org = EmployerOrganisation.objects.create(owner=other, name='Other', website='https://other.example.invalid')
        self.client.force_authenticate(other)
        response = self.client.post(self.url, dict(self.payload, organisation=org.pk), format='json')
        self.assertEqual(response.status_code, 409)
        self.assertNotIn(self.organisation.name, json.dumps(response.data))
        self.assertEqual(self.client.get(self.url).data['count'], 0)
        self.assertEqual(EmployerJobDraft.objects.count(), 1)

    def test_independent_review_publishes_one_stable_original_and_replay_does_not_republish(self):
        response = self.client.post(self.url, self.payload, format='json')
        draft = EmployerJobDraft.objects.get(pk=response.data['id'])
        self.assertEqual(self.client.post(f'{self.url}{draft.pk}/review/',
                         {'approve': True, 'reason': 'Self review', 'revision': 1}).status_code, 403)
        reviewer = User.objects.create_user(email='original-reviewer@example.invalid', is_staff=True)
        self.client.force_authenticate(reviewer)
        response = self.client.post(f'{self.url}{draft.pk}/review/',
                                    {'approve': True, 'reason': 'Synthetic independent authority/deadline review', 'revision': 1})
        self.assertEqual(response.status_code, 200)
        draft.refresh_from_db()
        job = draft.job
        self.assertEqual(job.source_url, f'https://jobs.example.invalid/jobs/{job.pk}')
        self.assertEqual(job.source_name, 'Ajiri employer posting')
        self.assertEqual(job.application_target, self.payload['application_url'])
        publication = JobListSerializer(job).data['publication']
        self.assertEqual(publication['publisher'], 'Ajiri')
        self.assertEqual(publication['listing_url'], job.source_url)
        self.client.force_authenticate(self.owner)
        replay = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.data['status'], 'published')
        self.assertEqual(Job.objects.count(), 1)

    def test_legacy_requests_remain_compatible_and_distinct_decisions_remain_distinct(self):
        legacy = {key: value for key, value in self.payload.items() if key != 'submission_id'}
        self.assertEqual(self.client.post(self.url, legacy, format='json').status_code, 201)
        self.assertEqual(self.client.post(self.url, self.payload, format='json').status_code, 201)
        self.assertEqual(self.client.post(self.url, dict(self.payload, submission_id=str(uuid.uuid4())), format='json').status_code, 201)
        self.assertEqual(EmployerJobDraft.objects.count(), 3)

    def test_malformed_id_and_unverified_accounts_cannot_create(self):
        self.assertEqual(self.client.post(self.url, dict(self.payload, submission_id='not-a-uuid'), format='json').status_code, 400)
        self.owner.profile.email_verified_at = None
        self.owner.profile.save()
        self.assertEqual(self.client.post(self.url, self.payload, format='json').status_code, 403)
        self.assertFalse(EmployerJobDraft.objects.exists())

    def test_feed_label_cannot_claim_original_publisher(self):
        job = Job.objects.create(title='Synthetic feed role', company_name='Synthetic', description='Synthetic',
                                 source_url='https://feed.example.invalid/role', source_name='Ajiri employer posting')
        JobPublication.objects.create(job=job, origin='rss', status='unverified')
        publication = JobListSerializer(job).data['publication']
        self.assertIsNone(publication['publisher'])
        self.assertIsNone(publication['listing_url'])

    def test_readiness_counts_are_aggregate_and_do_not_claim_a_live_pilot(self):
        before = (Job.objects.count(), EmployerJobDraft.objects.count())
        output = StringIO()
        call_command('original_source_readiness', stdout=output)
        data = json.loads(output.getvalue())
        self.assertEqual(data['eligible_original_roles'], 0)
        self.assertEqual(data['role_shortfall'], 50)
        self.assertEqual(data['employer_shortfall'], 10)
        self.assertFalse(data['inventory_targets_met'])
        self.assertNotIn(self.owner.email, output.getvalue())
        self.assertNotIn(self.organisation.name, output.getvalue())
        self.assertEqual(before, (Job.objects.count(), EmployerJobDraft.objects.count()))

    def test_disabled_freshness_cannot_claim_original_inventory_readiness(self):
        job = Job.objects.create(title='Synthetic closed role', company_name='Synthetic', description='Synthetic',
                                 source_url='https://example.invalid/closed', source_name='Ajiri employer posting')
        JobPublication.objects.create(job=job, origin='employer', status='published', organisation=self.organisation,
                                      closes_at=timezone.now() - timedelta(days=1))
        output = StringIO()
        with override_settings(JOB_FRESHNESS_ENFORCED=False):
            call_command('original_source_readiness', stdout=output)
        self.assertEqual(json.loads(output.getvalue())['eligible_original_roles'], 0)
