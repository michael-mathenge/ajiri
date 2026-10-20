from django.core.cache import cache
import tempfile
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from profiles.models import Skill
from profiles.cv_test_helpers import approved_cv
from .models import Application, Job, Notification
from .matching import calculate_match_score, notify_matching_profiles


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'], EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class MatchingEdgeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(email='match@example.com', password='test-password')
        self.job = Job.objects.create(title='Developer', company_name='Example', description='Build', source_url='https://example.com/match', source_name='test')

    def test_no_required_skills_and_no_overlap_score_zero(self):
        self.assertEqual(calculate_match_score(self.user.profile, self.job), 0)
        self.job.skills_required.add(Skill.objects.create(name='Python'))
        self.assertEqual(calculate_match_score(self.user.profile, self.job), 0)
        self.assertEqual(notify_matching_profiles(self.job), 0)

    def test_rounding_and_threshold_boundary(self):
        skills = [Skill.objects.create(name=f'Skill {i}') for i in range(10)]
        self.job.skills_required.set(skills)
        self.user.profile.skills.set(skills[:6])
        self.assertEqual(calculate_match_score(self.user.profile, self.job), 60)
        self.assertEqual(notify_matching_profiles(self.job), 0)
        self.user.profile.skills.add(skills[6])
        self.assertEqual(calculate_match_score(self.user.profile, self.job), 70)
        self.assertEqual(notify_matching_profiles(self.job), 1)
        self.job.skills_required.set(skills[:3])
        self.user.profile.skills.set(skills[:2])
        self.assertEqual(calculate_match_score(self.user.profile, self.job), 67)

    def test_inactive_and_flagged_jobs_never_alert(self):
        skill = Skill.objects.create(name='Python')
        self.job.skills_required.add(skill)
        self.user.profile.skills.add(skill)
        for active, flagged in [(False, False), (True, True)]:
            self.job.is_active, self.job.is_flagged_scam = active, flagged
            self.job.save()
            self.assertEqual(notify_matching_profiles(self.job), 0)
        self.assertEqual(Notification.objects.count(), 0)

    def test_enabling_alerts_after_both_off_allows_a_new_match(self):
        skill = Skill.objects.create(name='Python')
        self.job.skills_required.add(skill)
        self.user.profile.skills.add(skill)
        profile = self.user.profile
        profile.notify_email = profile.notify_in_app = False
        profile.save()
        self.assertEqual(notify_matching_profiles(self.job), 0)
        profile.notify_in_app = True
        profile.save()
        self.assertEqual(notify_matching_profiles(self.job), 1)
        self.assertEqual(len(mail.outbox), 0)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'], EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ApplicationLifecycleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        override = override_settings(MEDIA_ROOT=self.tmp.name)
        override.enable()
        self.addCleanup(override.disable)
        self.user = get_user_model().objects.create_user(email='lifecycle@example.com', password='test-password', full_name='Test Candidate')
        self.other = get_user_model().objects.create_user(email='other-lifecycle@example.com', password='test-password')
        self.job = Job.objects.create(title='Developer', company_name='Example', description='Build', source_url='https://example.com/lifecycle', source_name='test', application_method='email', application_email='jobs@example.com')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def prepare(self):
        approval = approved_cv(self.user)
        response = self.client.post(f'/api/jobs/{self.job.pk}/apply/', {'cv_version': str(approval.pk)}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'ready_for_review')
        return Application.objects.get(pk=response.data['id'])

    def test_prepare_is_idempotent_and_saves_documents_without_sending(self):
        app = self.prepare()
        self.assertTrue(app.generated_cv.storage.exists(app.generated_cv.name))
        self.assertTrue(app.generated_cover_letter.storage.exists(app.generated_cover_letter.name))
        self.assertEqual(len(mail.outbox), 0)
        repeat = self.client.post(f'/api/jobs/{self.job.pk}/apply/')
        self.assertEqual(repeat.status_code, 200)
        self.assertEqual(repeat.data['id'], app.pk)
        self.assertEqual(Application.objects.count(), 1)

    @patch('django.core.mail.EmailMessage.send')
    def test_legacy_email_send_is_disabled_without_status_or_mail_changes(self, send):
        app = self.prepare()
        response = self.client.post(f'/api/jobs/applications/{app.pk}/send/')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['code'], 'application_sending_disabled')
        app.refresh_from_db()
        self.assertEqual(app.status, 'ready_for_review')
        self.assertIsNone(app.sent_at)
        send.assert_not_called()
        self.assertEqual(self.client.post(f'/api/jobs/applications/{app.pk}/send/').status_code, 409)
        self.assertEqual(len(mail.outbox), 0)

    def test_external_submission_records_confirmation_without_email(self):
        self.job.application_method = 'external_link'
        self.job.save()
        app = self.prepare()
        self.assertEqual(self.client.post(f'/api/jobs/applications/{app.pk}/send/').data['status'], 'sent')
        self.assertEqual(len(mail.outbox), 0)

    def test_draft_and_dismissed_cannot_send(self):
        app = self.prepare()
        for status in ['draft', 'dismissed']:
            app.status = status
            app.save()
            self.assertEqual(self.client.post(f'/api/jobs/applications/{app.pk}/send/').status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    @patch('django.core.mail.EmailMessage.send', side_effect=OSError('mail service unavailable'))
    def test_email_backend_is_not_called_even_when_unavailable(self, send):
        app = self.prepare()
        self.assertEqual(self.client.post(f'/api/jobs/applications/{app.pk}/send/').status_code, 409)
        send.assert_not_called()
        app.refresh_from_db()
        self.assertEqual(app.status, 'ready_for_review')
        self.assertIsNone(app.sent_at)

    def test_missing_attachment_does_not_bypass_disabled_sending(self):
        app = self.prepare()
        app.generated_cv.storage.delete(app.generated_cv.name)
        self.assertEqual(self.client.post(f'/api/jobs/applications/{app.pk}/send/').status_code, 409)
        app.refresh_from_db()
        self.assertEqual(app.status, 'ready_for_review')
        self.assertIsNone(app.sent_at)

    def test_cross_user_list_send_and_dismiss_are_blocked(self):
        app = self.prepare()
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/jobs/applications/').data['count'], 0)
        for action in ['send', 'dismiss', 'restore']:
            self.assertEqual(self.client.post(f'/api/jobs/applications/{app.pk}/{action}/').status_code, 404)

    def test_restore_preserves_exact_snapshot_and_sends_nothing(self):
        app = self.prepare()
        with app.generated_cv.open('rb') as stream:
            cv = stream.read()
        before = (app.generated_cv.name, app.generated_cover_letter.name,
                  app.email_subject, app.email_body, app.created_at)
        self.client.post(f'/api/jobs/applications/{app.pk}/dismiss/')
        self.user.full_name = 'Changed after preparation'
        self.user.save()
        response = self.client.post(f'/api/jobs/applications/{app.pk}/restore/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        app.refresh_from_db()
        self.assertEqual(app.status, 'ready_for_review')
        self.assertEqual(before, (app.generated_cv.name, app.generated_cover_letter.name,
                         app.email_subject, app.email_body, app.created_at))
        with app.generated_cv.open('rb') as stream:
            self.assertEqual(stream.read(), cv)
        self.assertEqual(self.client.post(f'/api/jobs/applications/{app.pk}/restore/').status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_restore_rejects_missing_documents_and_sent_status(self):
        app = self.prepare()
        self.client.post(f'/api/jobs/applications/{app.pk}/dismiss/')
        app.generated_cv.storage.delete(app.generated_cv.name)
        self.assertEqual(self.client.post(f'/api/jobs/applications/{app.pk}/restore/').status_code, 409)
        app.refresh_from_db()
        self.assertEqual(app.status, 'dismissed')
        app.status = 'sent'
        app.save()
        self.assertEqual(self.client.post(f'/api/jobs/applications/{app.pk}/restore/').status_code, 409)

    def test_inactive_flagged_and_anonymous_applications_are_blocked(self):
        for active, flagged in [(False, False), (True, True)]:
            self.job.is_active, self.job.is_flagged_scam = active, flagged
            self.job.save()
            self.assertEqual(self.client.post(f'/api/jobs/{self.job.pk}/apply/').status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(f'/api/jobs/{self.job.pk}/apply/').status_code, 401)
