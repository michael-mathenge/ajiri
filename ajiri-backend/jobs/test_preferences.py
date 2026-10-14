from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from profiles.models import Skill
from .matching import notify_matching_profiles
from .models import Application, Job, Notification


class NotificationChannelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='channels@example.com', password='test-password')
        self.job = Job.objects.create(title='Developer', company_name='Example', description='Build', source_url='https://example.com/channels', source_name='test')
        skill = Skill.objects.create(name='Python')
        self.job.skills_required.add(skill)
        self.user.profile.skills.add(skill)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @patch('jobs.matching.send_match_email')
    def test_channel_combinations_and_duplicate_prevention(self, send):
        for email, in_app in [(False, False), (True, False), (False, True), (True, True)]:
            with self.subTest(email=email, in_app=in_app):
                Notification.objects.all().delete()
                send.reset_mock()
                profile = self.user.profile
                profile.notify_email, profile.notify_in_app = email, in_app
                profile.save()
                self.assertEqual(notify_matching_profiles(self.job), int(email or in_app))
                self.assertEqual(notify_matching_profiles(self.job), 0)
                self.assertEqual(send.call_count, int(email))
                response = self.client.get(reverse('notification-list'))
                self.assertEqual(response.data['count'], int(in_app))
                if email or in_app:
                    receipt = Notification.objects.get()
                    self.assertEqual(receipt.in_app, in_app)
                    self.assertEqual(receipt.sent_email, email)

    def test_email_only_receipt_cannot_be_marked_read(self):
        receipt = Notification.objects.create(user=self.user, job=self.job, match_score=100, in_app=False)
        self.assertEqual(self.client.post(reverse('notification-mark-read', args=[receipt.pk])).status_code, 404)


class DismissApplicationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='dismiss@example.com', password='test-password')
        other = get_user_model().objects.create_user(email='other@example.com', password='test-password')
        job = Job.objects.create(title='Developer', company_name='Example', description='Build', source_url='https://example.com/dismiss', source_name='test')
        self.application = Application.objects.create(user=self.user, job=job, application_method='external_link')
        self.other = other
        self.url = reverse('application-dismiss', args=[self.application.pk])
        self.client = APIClient()

    def test_authentication_and_ownership(self):
        self.assertEqual(self.client.post(self.url).status_code, 401)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(self.url).status_code, 404)

    def test_draft_and_reviewable_can_be_dismissed_idempotently(self):
        self.client.force_authenticate(self.user)
        for status in ['draft', 'ready_for_review']:
            self.application.status = status
            self.application.save()
            self.assertEqual(self.client.post(self.url).data['status'], 'dismissed')
            self.assertEqual(self.client.post(self.url).status_code, 200)
            self.application.refresh_from_db()
            self.assertIsNone(self.application.sent_at)

    def test_sent_application_cannot_be_dismissed(self):
        self.client.force_authenticate(self.user)
        self.application.status = 'sent'
        self.application.save()
        self.assertEqual(self.client.post(self.url).status_code, 400)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'sent')
