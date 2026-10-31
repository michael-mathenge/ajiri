import hashlib
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core import serializers as django_serializers
from django.db import OperationalError, close_old_connections, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from accounts.erasure import inventory
from .certificates import private_bytes, put
from .cv_builder import CVConflict, save_workspace
from .cv_validation import validate_content
from .models import CertificateEvidence, CVWorkspace
from .upload_fixtures import pdf_bytes


@override_settings(CERTIFICATE_EVIDENCE_ENABLED=True,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CertificateTests(TransactionTestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        settings = override_settings(MEDIA_ROOT=folder.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_user(email='certificate@example.invalid')
        self.other = get_user_model().objects.create_user(email='other-certificate@example.invalid')
        self.ids = [uuid.uuid4() for _ in range(6)]
        self.workspace = CVWorkspace.objects.create(profile=self.user.profile, content=validate_content({
            'schema_version': 1, 'contact': {'name': 'Synthetic Applicant'},
            'certifications': [{'id': str(key), 'name': 'Synthetic training', 'issuer': 'Test fixture'} for key in self.ids]}))
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def upload(self, data=None, name='certificate.pdf'):
        return SimpleUploadedFile(name, data if data is not None else pdf_bytes(), content_type='application/pdf')

    def create(self, index=0):
        return put(self.user.profile, self.ids[index], 1, self.upload())

    def url(self, index=0):
        return f'/api/profiles/me/certificates/{self.ids[index]}/'

    def test_actual_multipart_upload_metadata_is_private_and_quarantined(self):
        response = self.client.put(self.url(), {'expected_revision': '1', 'document': self.upload()}, format='multipart')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data['qualification_verified'])
        self.assertEqual(response.data['scan_state'], 'pending')
        self.assertNotIn('document', response.data)
        self.assertEqual(self.client.get(self.url()).status_code, 409)
        self.assertEqual(self.client.get('/api/profiles/me/certificates/').data['results'][0]['sha256'],
            hashlib.sha256(pdf_bytes()).hexdigest())

    def test_disabled_anonymous_and_other_owner_do_not_reveal_evidence(self):
        self.create()
        with override_settings(CERTIFICATE_EVIDENCE_ENABLED=False):
            self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.assertEqual(self.client.get('/api/profiles/me/certificates/').data['results'], [])
        self.client.force_authenticate(None)
        self.assertIn(self.client.get(self.url()).status_code, (401, 403))

    def test_unsupported_empty_spoofed_truncated_and_oversized_files_leave_no_rows_or_bytes(self):
        for data, name in [(b'', 'a.pdf'), (b'<html>fake</html>', 'a.pdf'), (b'%PDF-1.4\n', 'a.pdf'),
                           (pdf_bytes(), 'a.docx'), (b'x'*(5*1024*1024+1), 'a.pdf')]:
            with self.subTest(name=name, size=len(data)), self.assertRaises(ValidationError):
                put(self.user.profile, self.ids[0], 1, self.upload(data, name))
        self.assertFalse(CertificateEvidence.objects.exists())
        self.assertEqual(list(self.folder.rglob('*.pdf')), [])

    def test_stale_revision_or_missing_entry_cleans_staged_file(self):
        with self.assertRaises(CVConflict):
            put(self.user.profile, self.ids[0], 2, self.upload())
        with self.assertRaises(ValidationError):
            put(self.user.profile, uuid.uuid4(), 1, self.upload())
        self.assertEqual(list(self.folder.rglob('*.pdf')), [])

    def test_replacement_requires_current_identity_hash_and_removes_old_after_commit(self):
        old = self.create()
        old_path = Path(old.document.path)
        with self.assertRaises(CVConflict):
            self.create()
        new = put(self.user.profile, self.ids[0], 1, self.upload(), expected_id=old.pk, expected_hash=old.sha256)
        self.assertNotEqual(new.pk, old.pk)
        self.assertFalse(old_path.exists())
        self.assertTrue(Path(new.document.path).exists())
        with self.assertRaises(CVConflict):
            put(self.user.profile, self.ids[0], 1, self.upload(), expected_id=old.pk, expected_hash=old.sha256)
        self.assertEqual(len(list(self.folder.rglob('*.pdf'))), 1)

    def test_five_file_quota_and_failed_database_swap_preserve_active_bytes(self):
        rows = [self.create(index) for index in range(5)]
        with self.assertRaises(ValidationError):
            self.create(5)
        with patch('profiles.certificates.CertificateEvidence.objects.create', side_effect=RuntimeError('synthetic DB failure')):
            with self.assertRaises(RuntimeError):
                put(self.user.profile, self.ids[0], 1, self.upload(), expected_id=rows[0].pk, expected_hash=rows[0].sha256)
        self.assertEqual(CertificateEvidence.objects.count(), 5)
        self.assertTrue(Path(rows[0].document.path).exists())
        self.assertEqual(len(list(self.folder.rglob('*.pdf'))), 5)

    def test_clean_fresh_hash_required_for_attachment_download(self):
        row = self.create()
        CertificateEvidence.objects.filter(pk=row.pk).update(scan_state='clean', scan_version='test-result-only', scanned_at=timezone.now())
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, pdf_bytes())
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="certificate.pdf"')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        Path(row.document.path).write_bytes(b'changed')
        self.assertEqual(self.client.get(self.url()).status_code, 503)
        CertificateEvidence.objects.filter(pk=row.pk).update(scanned_at=timezone.now()-timedelta(days=2))
        self.assertEqual(self.client.get(self.url()).status_code, 409)

    def test_explicit_removal_precedes_entry_removal_and_inventory_contains_evidence(self):
        row = self.create()
        self.assertIn(row.document.name, inventory(self.user))
        with self.assertRaises(CVConflict):
            save_workspace(self.workspace, 1, {'certifications': []})
        payload = {'expected_revision': 1, 'expected_id': str(row.pk), 'expected_hash': row.sha256, 'confirm': False}
        self.assertEqual(self.client.delete(self.url(), payload, format='json').status_code, 400)
        payload['confirm'] = True
        self.assertEqual(self.client.delete(self.url(), payload, format='json').status_code, 204)
        self.assertFalse(Path(row.document.path).exists())
        updated = save_workspace(self.workspace, 1, {'certifications': []})
        self.assertEqual(updated.revision, 2)

    def test_total_byte_quota_counts_all_quarantine_states(self):
        for index in range(4):
            put(self.user.profile, self.ids[index], 1, self.upload(pdf_bytes(5*1024*1024)))
        with self.assertRaises(ValidationError):
            self.create(4)
        self.assertEqual(CertificateEvidence.objects.count(), 4)

    def test_simultaneous_last_slot_never_exceeds_owner_quota(self):
        for index in range(4):
            self.create(index)
        barrier = Barrier(2)

        def contender(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                put(self.user.profile, self.ids[index], 1, self.upload())
                return 'saved'
            except (OperationalError, ValidationError):
                return 'busy_or_full'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(contender, (4, 5)))
        self.assertEqual(outcomes.count('saved'), 1)
        self.assertEqual(CertificateEvidence.objects.count(), 5)
        self.assertEqual(len(list(self.folder.rglob('*.pdf'))), 5)

    def test_report_only_audit_detects_orphans_without_deleting_them(self):
        row = self.create()
        orphan = Path(row.document.path).with_name(uuid.uuid4().hex+'.pdf')
        orphan.write_bytes(pdf_bytes())
        output = StringIO()
        call_command('audit_certificate_evidence', stdout=output)
        self.assertIn('"unreferenced": 1', output.getvalue())
        self.assertIn('"changed": false', output.getvalue())
        self.assertTrue(orphan.exists())

    def test_injected_storage_failure_preserves_draft_and_records(self):
        before = self.workspace.content
        with patch('profiles.certificates.default_storage.save', side_effect=OSError('synthetic unavailable storage')):
            with self.assertRaises(OSError):
                self.create()
        self.workspace.refresh_from_db()
        self.assertEqual(self.workspace.content, before)
        self.assertEqual(self.workspace.revision, 1)
        self.assertFalse(CertificateEvidence.objects.exists())

    def test_isolated_synthetic_metadata_and_file_restoration_preserves_hash_and_quota(self):
        row = self.create()
        payload = django_serializers.serialize('json', [row])
        data = private_bytes(row)
        name, identity = row.document.name, row.pk
        # Simulate loss only inside this disposable test database/private temp folder.
        row.delete()
        restore_root = self.folder/'isolated-restore'
        destination = restore_root/name
        destination.parent.mkdir(parents=True)
        destination.write_bytes(data)
        with override_settings(MEDIA_ROOT=str(restore_root)):
            for restored in django_serializers.deserialize('json', payload):
                restored.save()
            restored = CertificateEvidence.objects.get(pk=identity)
            self.assertEqual(private_bytes(restored), data)
            self.assertEqual(restored.profile_id, self.user.profile.pk)
            self.assertEqual(restored.size_bytes, len(data))
            self.assertEqual(restored.sha256, hashlib.sha256(data).hexdigest())


class CertificateMigrationTests(TransactionTestCase):
    def test_additive_migration_preserves_existing_profile_and_workspace(self):
        executor = MigrationExecutor(connection)
        leaves = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(leaves))
        before = [('profiles', '0007_alert_consent')]
        executor.migrate(before)
        old = executor.loader.project_state(before).apps
        user = old.get_model('accounts', 'User').objects.create(
            email='legacy-certificate@example.invalid', password='synthetic-hash-unchanged')
        profile = old.get_model('profiles', 'Profile').objects.create(user_id=user.pk,
            headline='Synthetic existing headline', cv_file='cvs/existing-test.docx')
        content = {'schema_version': 1, 'contact': {}, 'certifications': []}
        workspace = old.get_model('profiles', 'CVWorkspace').objects.create(
            profile_id=profile.pk, revision=3, content=content)
        MigrationExecutor(connection).migrate(leaves)
        self.assertFalse(CertificateEvidence.objects.exists())
        restored = CVWorkspace.objects.select_related('profile__user').get(pk=workspace.pk)
        self.assertEqual(restored.content, content)
        self.assertEqual(restored.revision, 3)
        self.assertEqual(restored.profile.cv_file.name, 'cvs/existing-test.docx')
        self.assertEqual(restored.profile.user.password, 'synthetic-hash-unchanged')
