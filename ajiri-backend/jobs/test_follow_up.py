"""Personal dates never establish employer outcomes or clear delivery uncertainty."""
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from . import test_application_progress as progress_cases
from .models import DeliveryAttempt


class FollowUpTests(TestCase):
    url = progress_cases.ApplicationProgressTests.url
    save = progress_cases.ApplicationProgressTests.save

    def setUp(self):
        progress_cases.ApplicationProgressTests.setUp(self)

    def test_explicit_date_is_private_planning_without_sending_or_state_inference(self):
        target = timezone.now() + timedelta(days=2)
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            response = self.save(follow_up_at=target.isoformat())
            provider.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.app.refresh_from_db()
        self.assertEqual(self.app.follow_up_at, target)
        self.assertEqual(self.app.status, 'ready_for_review')
        self.assertIsNone(self.app.sent_at)
        self.assertFalse(DeliveryAttempt.objects.exists())
        self.assertIn('no-store', response['Cache-Control'])

    def test_legacy_omission_preserves_date_and_explicit_null_clears_it(self):
        target = timezone.now() + timedelta(days=2)
        self.assertEqual(self.save(follow_up_at=target.isoformat()).status_code, 200)
        self.assertEqual(self.save(expected_revision=1).status_code, 200)
        self.app.refresh_from_db()
        self.assertEqual(self.app.follow_up_at, target)
        self.assertEqual(self.save(expected_revision=2, follow_up_at=None).status_code, 200)
        self.app.refresh_from_db()
        self.assertIsNone(self.app.follow_up_at)

    def test_conflicts_and_other_owners_cannot_change_the_date(self):
        target = timezone.now() + timedelta(days=2)
        self.assertEqual(self.save(follow_up_at=target.isoformat()).status_code, 200)
        self.assertEqual(self.save(follow_up_at=None).status_code, 409)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.save(expected_revision=1, follow_up_at=None).status_code, 404)
        self.app.refresh_from_db()
        self.assertEqual(self.app.follow_up_at, target)

    def test_invalid_date_rejects_entire_report(self):
        response = self.save(follow_up_at='not-a-date')
        self.assertEqual(response.status_code, 400)
        self.assertIn('follow_up_at', response.data)
        self.app.refresh_from_db()
        self.assertEqual(self.app.progress_revision, 0)
        self.assertEqual(self.app.progress_note, '')

    def test_unknown_delivery_remains_unknown_after_personal_follow_up_update(self):
        self.app.application_method = 'email'
        self.app.status = 'sent'
        self.app.save()
        attempt = DeliveryAttempt.objects.create(user=self.user, application=self.app, channel='application',
            state='unknown', recipient_digest='a'*64)
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            response = self.save(follow_up_at=(timezone.now()+timedelta(days=2)).isoformat())
            provider.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['delivery_evidence']['kind'], 'unknown')
        attempt.refresh_from_db()
        self.assertEqual(attempt.state, 'unknown')
