from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from profiles.models import Skill
from .matching import calculate_match_score, explain_skill_match
from .models import Job, JobPublication
from .serializers import JobDetailSerializer


@override_settings(JOB_FRESHNESS_ENFORCED=True, JOB_FEED_DISPLAY_FORCE_OFF=True)
class SkillMatchExplanationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(email='match@example.invalid', password='Synthetic-892!')
        self.other = get_user_model().objects.create_user(email='other@example.invalid', password='Synthetic-892!')
        self.python = Skill.objects.create(name='Python')
        self.sql = Skill.objects.create(name='SQL')
        self.job = Job.objects.create(title='Synthetic developer', company_name='Example',
            description='Synthetic role', source_url='https://example.invalid/job', source_name='test')
        self.job.skills_required.add(self.sql, self.python)
        self.user.profile.skills.add(self.python)
        self.other.profile.skills.add(self.sql)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        JobPublication.objects.create(job=self.job, origin='rss', status='published',
            closes_at=timezone.now() + timedelta(days=2), confirmed_at=timezone.now())

    def test_authenticated_detail_explains_only_current_owners_skills(self):
        response = self.client.get(f'/api/jobs/{self.job.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['match_score'], 50)
        self.assertEqual(response.data['match_explanation'], {
            'status': 'compared', 'matched_skills': [{'id': self.python.pk, 'name': 'Python'}],
            'missing_skills': [{'id': self.sql.pk, 'name': 'SQL'}], 'required_count': 2, 'matched_count': 1,
        })
        self.assertTrue(response.data['can_apply'])
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        # A low match does not hide discovery or add a preparation threshold.
        self.assertEqual(self.client.get('/api/jobs/').data['count'], 1)
        self.assertEqual(self.client.post(f'/api/jobs/{self.job.pk}/apply/', {}).data['code'], 'cv_approval_required')
        self.client.force_authenticate(self.other)
        explanation = self.client.get(f'/api/jobs/{self.job.pk}/').data['match_explanation']
        self.assertEqual(explanation['matched_skills'], [{'id': self.sql.pk, 'name': 'SQL'}])

    def test_unknown_states_and_score_consistency_after_profile_edits(self):
        for skills in [[], [self.sql], [self.python, self.sql]]:
            self.user.profile.skills.set(skills)
            explanation = explain_skill_match(self.user.profile, self.job)
            self.assertEqual(calculate_match_score(self.user.profile, self.job),
                round(explanation['matched_count'] / explanation['required_count'] * 100))
            self.assertEqual(explanation['status'], 'compared' if skills else 'no_profile_skills')
        self.job.skills_required.clear()
        self.assertEqual(explain_skill_match(self.user.profile, self.job), {
            'status': 'no_job_skills', 'matched_skills': [], 'missing_skills': [],
            'required_count': 0, 'matched_count': 0,
        })
        self.assertEqual(calculate_match_score(self.user.profile, self.job), 0)

    def test_no_private_explanation_without_owner_context_or_authentication(self):
        serializer = JobDetailSerializer(self.job)
        self.assertIsNone(serializer.data['match_explanation'])
        serializer = JobDetailSerializer(self.job, context={'request': SimpleNamespace(user=object())})
        self.assertIsNone(serializer.data['match_explanation'])
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f'/api/jobs/{self.job.pk}/').status_code, 401)

    def test_skill_overlap_never_makes_expired_job_available(self):
        self.user.profile.skills.add(self.sql)
        JobPublication.objects.filter(job=self.job).update(closes_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.client.get(f'/api/jobs/{self.job.pk}/').status_code, 404)
        self.assertEqual(self.client.post(f'/api/jobs/{self.job.pk}/apply/', {}).status_code, 404)
