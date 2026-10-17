from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
import tempfile
from threading import Barrier
from unittest.mock import patch
from docx import Document
from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from .cv_builder import approve_workspace, content_hash, render_docx, start_workspace
from .models import CVWorkspace, CVApproval

ROOT = '/api/profiles/me/'


class CVBuilderTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        setting = override_settings(MEDIA_ROOT=self.temp.name)
        setting.enable()
        self.addCleanup(setting.disable)
        self.user = get_user_model().objects.create_user(email='cv-flow@example.invalid', password='test-only', full_name='Test Applicant')
        self.user.profile.bio = 'Build useful things.'
        self.user.profile.save()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def start(self):
        response = self.client.post(ROOT + 'cv-draft/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        return response.data

    def approve(self, draft=None):
        draft = draft or self.start()
        return self.client.post(ROOT + 'cv-draft/approve/', {'expected_revision': draft['revision'],
            'content_sha256': draft['content_sha256'], 'approval': True}, format='json')

    def test_explicit_start_save_preview_approve_and_exact_download(self):
        self.assertEqual(self.client.get(ROOT + 'cv-draft/').data, {'content': None})
        self.assertFalse(CVWorkspace.objects.exists())
        draft = self.start()
        self.assertEqual(self.start()['revision'], 1)
        self.assertEqual(CVWorkspace.objects.count(), 1)
        saved = self.client.patch(ROOT + 'cv-draft/', {'expected_revision': 1, 'content': {
            'contact': {'name': 'Reviewed Name'}, 'employment': [{'title': 'Engineer', 'organisation': 'Test Team', 'start': '2020-01',
                'current': True, 'achievements': ['Built a tool.']}], 'education': [{'qualification': 'Course', 'institution': 'Test School'}],
            'certifications': [{'name': 'Certificate', 'issuer': 'Test Institute'}], 'projects': [{'name': 'Project', 'url': 'https://example.com/project'}],
        }}, format='json')
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.data['revision'], 2)
        self.assertEqual(saved.data['content']['contact']['email'], self.user.email)
        response = self.approve(saved.data)
        self.assertEqual(response.status_code, 200)
        approval = CVApproval.objects.get()
        url = ROOT + f'cv-versions/{approval.pk}/download/'
        download = self.client.get(url)
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.content, Path(approval.document.path).read_bytes())
        self.assertIn('private, no-store', download['Cache-Control'])
        paragraphs = '\n'.join(p.text for p in Document(BytesIO(download.content)).paragraphs)
        for expected in ['Reviewed Name', 'Engineer', 'Built a tool.', 'Education', 'Course', 'Certificate', 'Project', 'Present']:
            self.assertIn(expected, paragraphs)
        self.assertNotIn('0 year', paragraphs)
        self.assertEqual(self.client.get(ROOT + 'generate-cv/').content, download.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Test Applicant')
        self.assertEqual(self.client.get(ROOT + 'cv-draft/').data['approval_id'], approval.pk)
        self.assertEqual(self.approve(saved.data).data['approval_id'], approval.pk)
        self.assertEqual(CVApproval.objects.count(), 1)

    def test_edit_requires_reapproval_and_preserves_earlier_snapshot(self):
        draft = self.start()
        approval = self.approve(draft).data['approval_id']
        old_bytes = self.client.get(ROOT + f'cv-versions/{approval}/download/').content
        saved = self.client.patch(ROOT + 'cv-draft/', {'expected_revision': 1, 'content': {'summary': 'New text'}}, format='json')
        self.assertEqual(saved.status_code, 200)
        self.assertIsNone(saved.data['approval_id'])
        self.assertEqual(self.client.get(ROOT + 'generate-cv/').status_code, 409)
        self.assertEqual(self.approve(draft).status_code, 409)
        self.assertEqual(self.client.get(ROOT + f'cv-versions/{approval}/download/').content, old_bytes)
        self.assertEqual(self.approve(saved.data).status_code, 200)
        self.assertEqual(CVApproval.objects.count(), 2)

    def test_stale_save_bad_hash_and_missing_consent_do_not_write(self):
        draft = self.start()
        for payload in [
            {'expected_revision': 1, 'content_sha256': '0' * 64, 'approval': True},
            {'expected_revision': 1, 'content_sha256': draft['content_sha256'], 'approval': False},
            {'expected_revision': 1, 'content_sha256': draft['content_sha256']},
        ]:
            self.assertIn(self.client.post(ROOT + 'cv-draft/approve/', payload, format='json').status_code, (400, 409))
        self.client.patch(ROOT + 'cv-draft/', {'expected_revision': 1, 'content': {'summary': 'Changed'}}, format='json')
        self.assertEqual(self.client.patch(ROOT + 'cv-draft/', {'expected_revision': 1, 'content': {'summary': 'Stale'}}, format='json').status_code, 409)
        self.assertFalse(CVApproval.objects.exists())
        self.assertFalse(list(Path(self.temp.name).rglob('*.docx')))

    def test_incomplete_unknown_fields_and_no_ownership_override(self):
        self.assertEqual(self.client.post(ROOT + 'cv-draft/', {'profile': 99}, format='json').status_code, 400)
        self.user.full_name = ''
        self.user.save()
        draft = self.start()
        self.assertEqual(self.approve(draft).status_code, 400)
        response = self.client.patch(ROOT + 'cv-draft/', {'expected_revision': 1, 'content': {'secret': 'bad'}}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(CVWorkspace.objects.get().revision, 1)

    def test_corrupt_missing_and_oversized_files_are_not_regenerated(self):
        self.approve()
        approval = CVApproval.objects.get()
        url = ROOT + f'cv-versions/{approval.pk}/download/'
        for data in [b'corrupt', b'x' * (2 * 1024 * 1024 + 1)]:
            Path(approval.document.path).write_bytes(data)
            self.assertEqual(self.client.get(url).status_code, 503)
        Path(approval.document.path).unlink()
        self.assertEqual(self.client.get(url).status_code, 503)

    def test_anonymous_and_other_owner_cannot_access(self):
        approval = self.approve().data['approval_id']
        other = get_user_model().objects.create_user(email='other-cv-flow@example.invalid', password='test-only')
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(ROOT + f'cv-versions/{approval}/download/').status_code, 404)
        self.assertEqual(self.client.get(ROOT + 'cv-draft/').data, {'content': None})
        self.client.force_authenticate(None)
        for url in ['cv-draft/', 'cv-draft/approve/', f'cv-versions/{approval}/download/', 'generate-cv/']:
            self.assertEqual(self.client.get(ROOT + url).status_code, 401)

    def test_changed_revision_during_render_leaves_no_approval_or_file(self):
        draft = self.start()
        original = render_docx
        def changed(content):
            CVWorkspace.objects.update(revision=2)
            return original(content)
        with patch('profiles.cv_builder.render_docx', side_effect=changed):
            self.assertEqual(self.approve(draft).status_code, 409)
        self.assertFalse(CVApproval.objects.exists())
        self.assertFalse(list(Path(self.temp.name).rglob('*.docx')))

    def test_database_failure_cleans_request_file(self):
        with patch('profiles.cv_builder.CVApproval.objects.create', side_effect=RuntimeError('synthetic')):
            with self.assertRaises(RuntimeError):
                approve_workspace(start_workspace(self.user.profile), 1, content_hash(start_workspace(self.user.profile).content))
        self.assertFalse(CVApproval.objects.exists())
        self.assertFalse(list(Path(self.temp.name).rglob('*.docx')))

    def test_deletion_removes_private_file_only_after_commit(self):
        self.approve()
        path = Path(CVApproval.objects.get().document.path)
        with self.captureOnCommitCallbacks(execute=True):
            self.user.delete()
            self.assertTrue(path.exists())
        self.assertFalse(path.exists())

    def test_oversized_render_and_storage_failure_publish_no_approval(self):
        from .cv_builder import CVUnavailable
        draft = self.start()
        with patch('profiles.cv_builder.Document') as document:
            document.return_value.save.side_effect = lambda buffer: buffer.write(b'x' * (2 * 1024 * 1024 + 1))
            with self.assertRaises(CVUnavailable):
                render_docx(CVWorkspace.objects.get().content)
        with patch('profiles.cv_builder.default_storage.save', side_effect=OSError('private-filename-must-not-leak')):
            response = self.approve(draft)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private-filename', str(response.data))
        self.assertFalse(CVApproval.objects.exists())

    def test_profile_change_never_silently_changes_saved_cv(self):
        draft = self.start()
        self.user.full_name = 'Later Profile Name'
        self.user.save()
        self.assertEqual(self.start()['content'], draft['content'])

    def test_rollback_of_account_deletion_keeps_approved_file(self):
        from django.db import transaction
        self.approve()
        path = Path(CVApproval.objects.get().document.path)
        try:
            with transaction.atomic():
                self.user.delete()
                raise RuntimeError('rollback')
        except RuntimeError:
            pass
        self.assertTrue(path.exists())
        self.assertEqual(CVApproval.objects.count(), 1)


class CVApprovalRaceTests(TransactionTestCase):
    def test_concurrent_approval_has_one_receipt_and_one_file(self):
        user = get_user_model().objects.create_user(email='cv-approval-race@example.invalid', password='test-only', full_name='Test')
        user.profile.bio = 'Test summary'
        user.profile.save()
        workspace = start_workspace(user.profile)
        barrier = Barrier(2)
        original = render_docx
        def render(content):
            data = original(content)
            barrier.wait(timeout=15)
            return data
        def approve():
            from django.db import OperationalError
            close_old_connections()
            try:
                return approve_workspace(CVWorkspace.objects.get(pk=workspace.pk), 1, content_hash(workspace.content)).pk
            except OperationalError as error:
                if 'locked' not in str(error).lower():
                    raise
                return None
            finally:
                close_old_connections()
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder), patch('profiles.cv_builder.render_docx', side_effect=render):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(approve) for _ in range(2)]
                results = [f.result() for f in futures]
            self.assertEqual(CVApproval.objects.count(), 1)
            self.assertTrue(any(results))
            self.assertEqual(len(list(Path(folder).rglob('*.docx'))), 1)
