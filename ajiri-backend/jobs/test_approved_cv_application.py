from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import OperationalError, close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from profiles.cv_test_helpers import approved_cv
from .application_drafting import prepare_application
from .models import Application, Job


class ApprovedCVApplicationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        setting = override_settings(MEDIA_ROOT=self.temp.name)
        setting.enable()
        self.addCleanup(setting.disable)
        self.user = get_user_model().objects.create_user(email='application-cv@example.invalid', password='test-only')
        self.approval = approved_cv(self.user)
        self.job = Job.objects.create(title='Developer', company_name='Unsafe/name', description='Test', source_url='https://example.invalid/role', source_name='test')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f'/api/jobs/{self.job.pk}/apply/'

    def apply(self, approval=None):
        return self.client.post(self.url, {'cv_version': str((approval or self.approval).pk)}, format='json')

    def test_exact_independent_snapshot_and_existing_application_unchanged(self):
        original = Path(self.approval.document.path).read_bytes()
        self.user.full_name = 'Later Name'
        self.user.save()
        with patch('django.core.mail.EmailMessage.send') as send:
            response = self.apply()
        self.assertEqual(response.status_code, 201)
        send.assert_not_called()
        application = Application.objects.get()
        snapshot = application.generated_cv.name
        self.assertEqual(Path(application.generated_cv.path).read_bytes(), original)
        self.assertNotIn('Unsafe', snapshot)
        other_version = approved_cv(self.user, revision=2)
        self.assertEqual(self.apply(other_version).status_code, 200)
        application.refresh_from_db()
        self.assertEqual(application.generated_cv.name, snapshot)
        with self.captureOnCommitCallbacks(execute=True):
            self.approval.delete()
        self.assertEqual(Path(application.generated_cv.path).read_bytes(), original)
        self.assertEqual(self.client.post(self.url).status_code, 200)

    def test_missing_selection_requires_review_unknown_or_cross_owner_is_404(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['code'], 'cv_approval_required')
        other = get_user_model().objects.create_user(email='other-application-cv@example.invalid', password='test-only')
        self.assertEqual(self.apply(approved_cv(other)).status_code, 404)
        self.assertEqual(self.client.post(self.url, {'cv_version': '00000000-0000-0000-0000-000000000000'}, format='json').status_code, 404)
        self.assertEqual(self.client.post(self.url, {'cv_version': 'invalid'}, format='json').status_code, 400)
        self.assertFalse(Application.objects.exists())

    def test_version_selector_returns_only_owner_metadata_without_cv_content(self):
        other = get_user_model().objects.create_user(email='version-list-other@example.invalid', password='test-only')
        approved_cv(other)
        response = self.client.get('/api/profiles/me/cv-versions/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(len(response.data['versions']), 1)
        self.assertEqual(set(response.data['versions'][0]), {'id', 'revision', 'approved_at'})
        self.assertNotIn('content', response.data)
        self.assertNotIn('Synthetic CV', str(response.data))
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/profiles/me/cv-versions/').status_code, 401)

    def test_missing_or_corrupt_source_never_creates_partial_application(self):
        Path(self.approval.document.path).write_bytes(b'corrupt')
        self.assertEqual(self.apply().status_code, 503)
        Path(self.approval.document.path).unlink()
        self.assertEqual(self.apply().status_code, 503)
        self.assertFalse(Application.objects.exists())
        self.assertFalse(list((Path(self.temp.name) / 'applications').rglob('*.docx')))

    def test_failed_record_write_cleans_only_request_files(self):
        with patch('jobs.application_drafting.Application.save', side_effect=OperationalError('private text')):
            response = self.apply()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private text', str(response.data))
        self.assertFalse(Application.objects.exists())
        self.assertFalse(list((Path(self.temp.name) / 'applications').rglob('*.docx')))
        self.assertTrue(Path(self.approval.document.path).exists())

    def test_second_file_write_failure_cleans_the_first(self):
        from django.db.models.fields.files import FieldFile
        original = FieldFile.save
        def fail_letter(field, *args, **kwargs):
            if field.field.name == 'generated_cover_letter':
                raise OSError('private text')
            return original(field, *args, **kwargs)
        with patch.object(FieldFile, 'save', fail_letter):
            self.assertEqual(self.apply().status_code, 503)
        self.assertFalse(Application.objects.exists())
        self.assertFalse(list((Path(self.temp.name) / 'applications').rglob('*.docx')))


class ConcurrentDraftTests(TransactionTestCase):
    def test_concurrent_drafts_keep_one_application_and_two_snapshot_files(self):
        user = get_user_model().objects.create_user(email='draft-race@example.invalid', password='test-only')
        job = Job.objects.create(title='Test', company_name='Test', description='Test', source_name='test', source_url='https://example.invalid/draft-race')
        barrier = Barrier(2)
        from .application_drafting import generate_cover_letter_docx
        def letter(*args):
            buffer = generate_cover_letter_docx(*args)
            barrier.wait(timeout=15)
            return buffer
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            approval = approved_cv(user)
            def prepare():
                close_old_connections()
                try:
                    return prepare_application(get_user_model().objects.get(pk=user.pk), job, approval)[0].pk
                except OperationalError as error:
                    if 'locked' not in str(error).lower():
                        raise
                    return None
                finally:
                    close_old_connections()
            with patch('jobs.application_drafting.generate_cover_letter_docx', side_effect=letter), ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(prepare) for _ in range(2)]
                results = [future.result() for future in futures]
            self.assertEqual(Application.objects.count(), 1)
            self.assertTrue(any(results))
            self.assertEqual(len(list((Path(folder) / 'applications').rglob('*.docx'))), 2)
