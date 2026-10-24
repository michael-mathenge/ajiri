"""Private reports are independent of employer decisions and sending evidence."""
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import caches
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Application, DeliveryAttempt, DeliveryDailyBudget, Job
from .pilot_test_helpers import prepared_pilot, pilot_settings
from .serializers import ApplicationSerializer


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
                   EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ApplicationProgressTests(TestCase):
    def setUp(self):
        for cache in caches.all():
            cache.clear()
        self.user = get_user_model().objects.create_user(email='progress@example.invalid')
        self.other = get_user_model().objects.create_user(email='other-progress@example.invalid')
        self.job = Job.objects.create(title='Synthetic role', company_name='Synthetic company',
            source_name='synthetic', source_url='https://example.invalid/progress')
        self.app = Application.objects.create(user=self.user, job=self.job, status='ready_for_review',
            application_method='external_link')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def url(self, app=None):
        return f'/api/jobs/applications/{(app or self.app).pk}/progress/'

    def save(self, **changes):
        return self.client.patch(self.url(), {'expected_revision': 0, 'stage': 'interview',
                                             'note': 'Synthetic private note', **changes}, format='json')

    def test_user_report_does_not_change_submission_or_delivery(self):
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            response = self.save()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'ready_for_review')
        self.assertIsNone(self.app.sent_at)
        self.assertEqual(self.app.progress_revision, 1)
        self.assertEqual(self.app.progress_stage, 'interview')
        self.assertIsNotNone(self.app.progress_reported_at)
        self.assertFalse(DeliveryAttempt.objects.exists())
        self.assertFalse(DeliveryDailyBudget.objects.exists())
        self.assertEqual(mail.outbox, [])
        provider.assert_not_called()

    def test_other_owner_and_anonymous_cannot_write(self):
        other_app = Application.objects.create(user=self.other, job=self.job)
        self.assertEqual(self.client.patch(self.url(other_app), {'expected_revision': 0, 'stage': 'offer'}, format='json').status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.save().status_code, 401)

    def test_revision_conflict_preserves_the_first_saved_report(self):
        self.assertEqual(self.save().status_code, 200)
        self.assertEqual(self.save(stage='offer').status_code, 409)
        self.app.refresh_from_db()
        self.assertEqual(self.app.progress_stage, 'interview')
        self.assertEqual(self.app.progress_revision, 1)

    def test_validation_requires_revision_and_rejects_delivery_fields(self):
        response = self.client.patch(self.url(), {'stage': 'invented', 'note': 'x'*1001, 'status': 'sent'}, format='json')
        self.assertEqual(response.status_code, 400)
        # Strict input rejects unexpected sending fields before accepting a report.
        self.assertFalse(self.app.progress_reported_at)
        response = self.client.patch(self.url(), {'stage': 'invented', 'note': 'x'*1001}, format='json')
        self.assertEqual(set(response.data), {'expected_revision', 'stage', 'note'})
        self.assertEqual(self.save(expected_revision=10**99).status_code, 400)

    def test_clearing_report_does_not_infer_an_employer_outcome(self):
        self.assertEqual(self.save(stage='not_reported', note='').status_code, 200)
        self.assertEqual(self.save(expected_revision=1, stage='not_reported').status_code, 400)

    def test_provider_receipt_labels_do_not_claim_delivery(self):
        self.app.application_method = 'email'
        self.app.status = 'sent'
        self.app.save()
        for state, text in [('accepted', 'inbox delivery unconfirmed'), ('unknown', 'reconciliation required'),
                            ('reserved', 'reconciliation required'), ('definite_failure', 'attempt failed')]:
            DeliveryAttempt.objects.all().delete()
            DeliveryAttempt.objects.create(user=self.user, application=self.app, channel='application',
                state=state, recipient_digest='a'*64,
                resolved_at=timezone.now() if state in ('accepted', 'definite_failure') else None)
            evidence = ApplicationSerializer(self.app).data['delivery_evidence']
            self.assertEqual(evidence['kind'], state)
            self.assertIn(text, evidence['label'])

    def test_external_and_legacy_email_records_remain_distinct(self):
        self.app.status = 'sent'
        self.assertEqual(ApplicationSerializer(self.app).data['delivery_evidence']['kind'], 'user_report')
        self.app.application_method = 'email'
        self.assertEqual(ApplicationSerializer(self.app).data['delivery_evidence']['kind'], 'unverified_record')

    def test_inconsistent_other_owner_receipt_is_not_presented_as_evidence(self):
        DeliveryAttempt.objects.create(user=self.other, application=self.app, channel='application',
            state='accepted', recipient_digest='b'*64, resolved_at=timezone.now())
        self.assertEqual(ApplicationSerializer(self.app).data['delivery_evidence']['kind'], 'ready_for_review')
        response = self.client.get('/api/jobs/applications/')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertEqual(response.data['results'][0]['delivery_evidence']['kind'], 'ready_for_review')

    def test_owner_list_is_paginated_and_does_not_expose_other_notes(self):
        Application.objects.create(user=self.other, job=self.job, progress_note='Other private note')
        response = self.client.get('/api/jobs/applications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertNotIn('Other private note', str(response.data))
        self.assertEqual(response.data['results'][0]['progress_stage'], 'not_reported')

    def test_report_preserves_approved_package_and_document_bytes(self):
        from profiles.models import Profile
        Profile.objects.filter(user=self.user).update(email_verified_at=timezone.now(), verified_email=self.user.email)
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory, **pilot_settings(self.user)):
            app, package = prepared_pilot(self.user)
            before = (package.content_sha256, package.job_snapshot,
                      Path(package.cv_document.path).read_bytes(), Path(package.letter_document.path).read_bytes())
            response = self.client.patch(self.url(app), {'expected_revision': 0, 'stage': 'offer', 'note': 'My report only'}, format='json')
            self.assertEqual(response.status_code, 200)
            package.refresh_from_db()
            self.assertEqual(before, (package.content_sha256, package.job_snapshot,
                      Path(package.cv_document.path).read_bytes(), Path(package.letter_document.path).read_bytes()))
            self.assertIsNotNone(package.approval)
