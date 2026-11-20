import hashlib
from contextlib import contextmanager
from io import StringIO
import json
from pathlib import Path
import tempfile
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command, CommandError
from django.test import TransactionTestCase, SimpleTestCase, override_settings
from rest_framework.test import APIClient

from accounts.erasure import read_journal
from .private_storage import (PrivateStorageError, inspect, read_exact, read_field,
    save_unique, delete_exact)
from .private_storage_test_helpers import PathlessPrivateStorage, workflow_storage
from .cv_test_helpers import approved_cv
from .cv_builder import document_bytes, content_hash
from .cv_validation import validate_content
from .models import CVWorkspace
from .upload_fixtures import pdf_bytes
from .private_copy import inventory, resume_copy, CopyInterrupted


class PrivateBoundaryTests(SimpleTestCase):
    def setUp(self):
        self.storage = PathlessPrivateStorage()
        self.storage.objects.clear()

    def test_exact_version_read_and_delete_reject_replacement_even_when_bytes_match(self):
        name = save_unique(self.storage, 'private/'+uuid.uuid4().hex+'.pdf', b'synthetic')
        reference = inspect(self.storage, name)
        self.assertEqual(read_exact(self.storage, reference), b'synthetic')
        self.storage.objects[name] = (str(uuid.uuid4()), b'synthetic')
        with self.assertRaises(PrivateStorageError): read_exact(self.storage, reference)
        with self.assertRaises(PrivateStorageError): delete_exact(self.storage, reference)
        self.assertTrue(self.storage.exists(name))
        with self.assertRaises(PrivateStorageError): self.storage.url(name)

    def test_partial_captured_version_cleanup_can_resume_without_deleting_a_replacement(self):
        class PartialCleanupStorage(PathlessPrivateStorage):
            interrupted = False
            def private_delete(self, reference):
                if not self.exists(reference['key']):
                    return
                version, data = self.objects[reference['key']]
                remaining, captured = set(version.split(',')), set(reference['version'].split(','))
                if not remaining <= captured:
                    raise PrivateStorageError('Replacement version is outside the signed identity.')
                if not self.interrupted:
                    remaining.remove(sorted(remaining)[0])
                    self.objects[reference['key']] = (','.join(sorted(remaining)), data)
                    self.interrupted = True
                    raise OSError('Synthetic lost cleanup acknowledgement')
                del self.objects[reference['key']]
        storage = PartialCleanupStorage()
        name = 'private/versions.pdf'
        storage.objects[name] = ('version-a,version-b', b'synthetic')
        reference = inspect(storage, name)
        with self.assertRaises(OSError): delete_exact(storage, reference)
        self.assertTrue(storage.exists(name))
        delete_exact(storage, reference)
        self.assertFalse(storage.exists(name))
        delete_exact(storage, reference)
        storage.objects[name] = ('replacement', b'synthetic')
        with self.assertRaises(PrivateStorageError): delete_exact(storage, reference)
        self.assertTrue(storage.exists(name))

    def test_unsafe_keys_invalid_bounds_and_unreviewed_pathless_backend_fail_closed(self):
        for name in ('../escape', '/absolute', 'a//b', 'a/./b', 'a\\b', 'a:b', 'a\n'):
            with self.assertRaises(PrivateStorageError): save_unique(self.storage, name, b'synthetic')
        name = save_unique(self.storage, 'private/example.pdf', b'synthetic')
        reference = inspect(self.storage, name)
        for limit in (0, True, '5', 6*1024*1024):
            with self.assertRaises(PrivateStorageError): read_exact(self.storage, reference, limit=limit)
        with patch.object(FileSystemStorage, 'path', side_effect=NotImplementedError):
            with self.assertRaises(PrivateStorageError): inspect(FileSystemStorage(), name)

    def test_local_identity_changed_file_and_hard_link_are_not_deleted_or_read(self):
        import os
        with tempfile.TemporaryDirectory() as folder:
            storage = FileSystemStorage(location=folder)
            name = save_unique(storage, 'private/example.pdf', b'synthetic')
            reference = inspect(storage, name)
            path = Path(storage.path(name)); path.write_bytes(b'replaced')
            with self.assertRaises(PrivateStorageError): delete_exact(storage, reference)
            self.assertEqual(path.read_bytes(), b'replaced')
            try:
                os.link(path, Path(folder)/'hardlink')
            except OSError:
                self.skipTest('Platform does not permit a synthetic hard link.')
            with self.assertRaises(PrivateStorageError): inspect(storage, name)

    def test_interrupted_copy_reuses_verified_objects_and_rejects_conflicts_without_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source = FileSystemStorage(location=folder)
            for index in range(3):
                save_unique(source, f'private/{index}.pdf', f'synthetic-{index}'.encode())
            references = inventory(source)
            with self.assertRaises(CopyInterrupted):
                resume_copy(source, self.storage, references, fail_after=1)
            result = resume_copy(source, self.storage, references)
            self.assertEqual((result['copied'], result['reused']), (2, 1))
            name = references[0]['key']
            self.storage.objects[name] = (str(uuid.uuid4()), b'changed')
            before = dict(self.storage.objects)
            with self.assertRaises(PrivateStorageError): resume_copy(source, self.storage, references)
            self.assertEqual(self.storage.objects, before)

    def test_copy_rejects_extra_destination_objects_and_invalid_programmatic_arguments(self):
        with tempfile.TemporaryDirectory() as folder:
            source = FileSystemStorage(location=folder)
            save_unique(source, 'private/source.pdf', b'synthetic')
            references = inventory(source)
            save_unique(self.storage, 'private/unexpected.pdf', b'other')
            with self.assertRaises(PrivateStorageError): resume_copy(source, self.storage, references)
            for limit in (0, True, '1', -1):
                with self.assertRaises(PrivateStorageError):
                    resume_copy(source, self.storage, references, fail_after=limit)

    def test_copy_rejects_nested_roots_and_changed_source_identity_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            source = FileSystemStorage(location=folder)
            nested = FileSystemStorage(location=str(Path(folder)/'nested'))
            with self.assertRaises(PrivateStorageError): resume_copy(source, nested, [])
            save_unique(source, 'private/source.pdf', b'synthetic')
            references = inventory(source)
            Path(source.path('private/source.pdf')).write_bytes(b'changed')
            with self.assertRaises(PrivateStorageError): resume_copy(source, self.storage, references)
            self.assertEqual(self.storage.objects, {})


@override_settings(STORAGES={'default': workflow_storage(),
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}},
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    CERTIFICATE_EVIDENCE_ENABLED=True, MALWARE_SCANNING_ENABLED=False,
    EMAIL_PLATFORM_FROM='platform@example.invalid')
class PathlessDocumentWorkflowTests(TransactionTestCase):
    def setUp(self):
        PathlessPrivateStorage.objects.clear()
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        media = self.root/'unused-media'; media.mkdir()
        state = self.root/'state'; state.mkdir()
        self.ledger = self.root/'ledger'
        settings = override_settings(MEDIA_ROOT=media, ERASURE_LEDGER_DIR=self.ledger)
        settings.enable(); self.addCleanup(settings.disable)
        self.owner = get_user_model().objects.create_user(email='pathless@example.invalid')
        self.other = get_user_model().objects.create_user(email='other-pathless@example.invalid')
        self.client = APIClient(); self.client.force_authenticate(self.owner)
        self.approval = approved_cv(self.owner)
        self.owner.profile.cv_file.save('uploaded.pdf', ContentFile(pdf_bytes()), save=True)
        self.other.profile.cv_file.save('other.pdf', ContentFile(pdf_bytes()), save=True)
        self.certificate_id = uuid.uuid4()
        self.workspace = CVWorkspace.objects.create(profile=self.owner.profile, content=validate_content({
            'schema_version': 1, 'contact': {'name': 'Synthetic'}, 'certifications': [
                {'id': str(self.certificate_id), 'name': 'Synthetic training', 'issuer': 'Synthetic'}]}))

    def certificate(self):
        from .certificates import put
        return put(self.owner.profile, self.certificate_id, 1,
            SimpleUploadedFile('certificate.pdf', pdf_bytes(), content_type='application/pdf'))

    def erase(self, mode, request_id, **extra):
        options = dict(user_id=self.owner.pk, request_id=request_id, journal_dir=str(self.ledger),
            mode=mode, verified_request=True, writers_paused=True, legal_hold_cleared=True,
            journal_copied=True, stdout=StringIO())
        options.update(extra)
        call_command('erase_account_data', **options)

    def test_private_download_export_and_immutable_application_package_work_without_paths(self):
        from jobs.models import Application, Job
        from jobs.application_packages import context, save_package
        from jobs.application_drafting import prepare_application
        from jobs.package_review import verified_documents
        before = document_bytes(self.approval)
        profile = self.client.get('/api/profiles/me/')
        self.assertEqual(profile.status_code, 200)
        self.assertTrue(profile.data['cv_file'].endswith('/api/profiles/me/cv/'))
        response = self.client.get('/api/profiles/me/cv/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), pdf_bytes()); response.close()
        job = Job.objects.create(title='Synthetic', company_name='Synthetic',
            source_url='https://example.invalid/pathless', source_name='synthetic')
        with override_settings(JOB_FRESHNESS_ENFORCED=False):
            application, created = prepare_application(self.owner, job, self.approval)
        self.assertTrue(created)
        applications = self.client.get('/api/jobs/applications/')
        self.assertEqual(applications.status_code, 200)
        self.assertTrue(applications.data['results'][0]['generated_cv'].endswith(
            f'/api/jobs/applications/{application.pk}/documents/cv/'))
        legacy = self.client.get(f'/api/jobs/applications/{application.pk}/documents/cv/')
        self.assertEqual(legacy.status_code, 200)
        self.assertEqual(b''.join(legacy.streaming_content), before); legacy.close()
        package = save_package(self.owner, application.pk, {'cv_version': self.approval.pk,
            'expected_revision': 0, 'context_sha256': content_hash(context(application)),
            'letter_text': 'Synthetic letter', 'email_subject': '', 'email_body': ''})
        self.assertEqual(verified_documents(package)['cv'], before)
        certificate = self.certificate()
        destination = self.root/'export'
        call_command('export_account_data', user_id=self.owner.pk, destination=str(destination),
            verified_request=True, writers_paused=True, stdout=StringIO())
        manifest = json.loads((destination/'manifest.json').read_text())
        self.assertTrue(manifest['complete'])
        for name, expected in manifest['sha256'].items():
            self.assertEqual(hashlib.sha256((destination/name).read_bytes()).hexdigest(), expected)
        self.assertEqual(len(list((destination/'documents').iterdir())), 7)
        self.assertEqual(read_field(certificate.document), pdf_bytes())
        self.assertEqual(document_bytes(self.approval), before)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f'/api/profiles/me/cv-versions/{self.approval.pk}/download/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/profiles/me/certificates/{self.certificate_id}/').status_code, 404)

    def test_versioned_erasure_is_owner_scoped_and_replacement_blocks_before_database_changes(self):
        self.certificate()
        request = str(uuid.uuid4()); self.erase('prepare', request)
        path = self.ledger/(request+'.signed')
        journal = read_journal(path)
        self.assertEqual(journal['format'], 2)
        from accounts.erasure import write_journal
        oversized = self.ledger/(str(uuid.uuid4())+'.signed')
        with patch('accounts.erasure.signing.dumps', return_value='x'*(1024*1024+1)):
            with self.assertRaises(CommandError): write_journal(oversized, journal)
        self.assertFalse(oversized.exists())
        name = self.owner.profile.cv_file.name
        data = read_field(self.owner.profile.cv_file)
        default_storage.replace_synthetic(name, data)
        with self.assertRaises(CommandError): self.erase('execute', request)
        self.owner.refresh_from_db(); self.assertTrue(self.owner.is_active)
        request = str(uuid.uuid4()); self.erase('prepare', request)
        path = self.ledger/(request+'.signed')
        other_name = self.other.profile.cv_file.name
        self.erase('execute', request)
        self.assertFalse(get_user_model().objects.filter(pk=self.owner.pk).exists())
        self.assertTrue(default_storage.exists(other_name))
        self.assertEqual(read_journal(path)['state'], 'complete')
        self.assertEqual(read_journal(path)['objects'], [])

    def test_failed_conditional_cleanup_is_resumable_and_keeps_private_journal(self):
        request = str(uuid.uuid4()); self.erase('prepare', request)
        backend = type(default_storage._wrapped)
        original = backend.private_delete
        def failed(storage, reference):
            if reference['key'] == self.owner.profile.cv_file.name:
                raise OSError('Synthetic outage')
            return original(storage, reference)
        with patch.object(backend, 'private_delete', failed):
            with self.assertRaises(CommandError): self.erase('execute', request)
        self.assertFalse(get_user_model().objects.filter(pk=self.owner.pk).exists())
        self.assertEqual(read_journal(self.ledger/(request+'.signed'))['state'], 'db_erased')
        self.erase('execute', request)
        self.assertEqual(read_journal(self.ledger/(request+'.signed'))['state'], 'complete')

    def test_commit_acknowledgement_failure_preserves_cv_and_application_document_pointers(self):
        from django.db import transaction
        from .cv_builder import approve_workspace
        from .models import CVApproval
        from jobs.models import Job, Application, ApplicationPackage
        from jobs.application_packages import save_package, context
        from jobs.package_review import verified_documents
        real_atomic = transaction.atomic
        @contextmanager
        def committed_then_unavailable(*args, **kwargs):
            with real_atomic(*args, **kwargs):
                yield
            raise OSError('Synthetic lost commit acknowledgement')
        self.workspace.revision = 2
        self.workspace.save(update_fields=['revision'])
        with patch('profiles.cv_builder.transaction.atomic', committed_then_unavailable):
            with self.assertRaises(OSError):
                approve_workspace(self.workspace, 2, content_hash(self.workspace.content))
        approval = CVApproval.objects.get(profile=self.owner.profile, revision=2)
        self.assertTrue(document_bytes(approval))
        job = Job.objects.create(title='Synthetic', company_name='Synthetic',
            source_url='https://example.invalid/commit-outcome', source_name='synthetic')
        application = Application.objects.create(user=self.owner, job=job, application_method='external_link')
        with patch('jobs.application_packages.transaction.atomic', committed_then_unavailable):
            with self.assertRaises(OSError):
                save_package(self.owner, application.pk, {'cv_version': approval.pk, 'expected_revision': 0,
                    'context_sha256': content_hash(context(application)), 'letter_text': 'Synthetic',
                    'email_subject': '', 'email_body': ''})
        package = ApplicationPackage.objects.get(application=application)
        self.assertEqual(verified_documents(package)['cv'], document_bytes(approval))
