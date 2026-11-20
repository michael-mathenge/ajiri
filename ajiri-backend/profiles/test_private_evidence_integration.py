"""Synthetic private files only; never contacts an engine or provider."""
import hashlib
from io import StringIO
import json
from pathlib import Path
from unittest.mock import patch
import uuid
import tempfile
from datetime import timedelta
from contextlib import contextmanager

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase, override_settings
from django.db import OperationalError, transaction
from django.utils import timezone

from .certificate_scanning import scan_certificate
from .certificates import put
from .models import CertificateEvidence
from .scanner import Verdict
from . import test_certificates as fixtures


@override_settings(CERTIFICATE_EVIDENCE_ENABLED=True, MALWARE_SCANNING_ENABLED=True,
    CLAMD_HOST_UTC_CONFIRMED=True, CLAMD_LIMITS_REVIEW='clamd-bounds-v1',
    CLAMD_ALLOWED_ENGINE_VERSIONS=['1.4.3'],
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PrivateEvidenceIntegrationTests(TransactionTestCase):
    setUp = fixtures.CertificateTests.setUp
    upload = fixtures.CertificateTests.upload
    create = fixtures.CertificateTests.create
    url = fixtures.CertificateTests.url

    def test_unavailable_infected_disabled_and_mismatched_hash_never_release(self):
        row = self.create()
        with override_settings(MALWARE_SCANNING_ENABLED=False), patch('profiles.certificate_scanning.scan_bytes') as scan:
            self.assertFalse(scan_certificate(row.pk))
            scan.assert_not_called()
        for result in (Verdict('unavailable', row.sha256), Verdict('infected', row.sha256, 'fixture'),
                       Verdict('clean', '0'*64, 'fixture')):
            with self.subTest(state=result.state), patch('profiles.certificate_scanning.scan_bytes', return_value=result):
                self.assertTrue(scan_certificate(row.pk))
                self.assertEqual(self.client.get(self.url()).status_code, 409)

    def test_stalled_claim_requires_explicit_recovery_and_old_claim_cannot_settle(self):
        row = self.create()
        CertificateEvidence.objects.filter(pk=row.pk).update(scan_state='scanning', scanned_at=timezone.now()-timedelta(minutes=2))
        with patch('profiles.certificate_scanning.scan_bytes', return_value=Verdict('unavailable', row.sha256)) as scan:
            self.assertFalse(scan_certificate(row.pk))
            scan.assert_not_called()
            self.assertTrue(scan_certificate(row.pk, recover_stalled=True))
        def newer_claim(data):
            CertificateEvidence.objects.filter(pk=row.pk).update(scanned_at=timezone.now()+timedelta(seconds=1))
            return Verdict('clean', row.sha256, 'fixture')
        with patch('profiles.certificate_scanning.scan_bytes', side_effect=newer_claim):
            self.assertFalse(scan_certificate(row.pk))
        row.refresh_from_db()
        self.assertEqual(row.scan_state, 'scanning')

    def test_verified_export_includes_only_owned_quarantine_and_exact_hash(self):
        row = self.create()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        destination = Path(temporary.name)/'export'
        with override_settings(BASE_DIR=self.folder/'application'):
            call_command('export_account_data', user_id=self.user.pk, destination=str(destination),
                         verified_request=True, writers_paused=True, stdout=StringIO())
        records = json.loads((destination/'account.json').read_text())['records']['certificate_evidence']
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['id'], str(row.pk))
        self.assertEqual(hashlib.sha256((destination/records[0]['document']).read_bytes()).hexdigest(), row.sha256)
        self.assertNotIn(row.document.name, json.dumps(records))

    def test_confirmed_synthetic_account_erasure_inventories_and_removes_evidence(self):
        row = self.create()
        path = Path(row.document.path)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        journal = Path(temporary.name)/'journal'
        with override_settings(BASE_DIR=self.folder/'application', ERASURE_LEDGER_DIR=str(journal)):
            options = dict(user_id=self.user.pk, request_id=str(uuid.uuid4()), journal_dir=str(journal),
                verified_request=True, writers_paused=True, legal_hold_cleared=True,
                journal_copied=True, stdout=StringIO())
            call_command('erase_account_data', mode='prepare', **options)
            call_command('erase_account_data', mode='execute', **options)
        self.assertFalse(path.exists())
        self.assertFalse(CertificateEvidence.objects.filter(pk=row.pk).exists())
        self.assertTrue(type(self.other).objects.filter(pk=self.other.pk).exists())

    def test_readiness_reports_aggregates_without_paths_hashes_or_socket_by_default(self):
        row = self.create()
        output = StringIO()
        with patch('profiles.scanner._connect') as connect:
            call_command('private_upload_readiness', stdout=output)
        connect.assert_not_called()
        report = json.loads(output.getvalue())
        self.assertEqual(report['evidence_counts'], {'pending': 1})
        self.assertEqual(report['evidence_bytes'], row.size_bytes)
        self.assertFalse(report['changes'])
        for private in (row.document.name, row.sha256, self.user.email, str(row.pk)):
            self.assertNotIn(private, output.getvalue())

    def test_commands_validate_programmatic_inputs_before_any_claim_or_probe(self):
        for name, options in [('scan_certificate_evidence', {'evidence_id': 'not-a-uuid'}),
                              ('scan_certificate_evidence', {'evidence_id': uuid.uuid4(), 'recover_stalled': 'yes'}),
                              ('private_upload_readiness', {'probe': 'yes'})]:
            with self.subTest(command=name), self.assertRaises(CommandError):
                call_command(name, stdout=StringIO(), **options)

    def test_suspended_upload_keeps_existing_evidence_and_draft(self):
        row = self.create()
        with override_settings(PRIVATE_UPLOADS_SUSPENDED=True):
            response = self.client.put(self.url(1), {'expected_revision': '1', 'document': self.upload()}, format='multipart')
        self.assertEqual(response.status_code, 503)
        self.assertTrue(Path(row.document.path).exists())
        self.workspace.refresh_from_db()
        self.assertEqual(self.workspace.revision, 1)

    def test_private_relocation_rejects_missing_certificate_before_creating_destination(self):
        row = self.create()
        Path(row.document.path).unlink()  # Disposable synthetic file, not a production operation.
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        destination = Path(temporary.name)/'copy'
        with self.assertRaises(CommandError):
            call_command('relocate_private_media', source=str(self.folder), destination=str(destination),
                         apply=True, stdout=StringIO())
        self.assertFalse(destination.exists())

    def test_cleanup_failure_after_committed_replacement_never_removes_new_bytes(self):
        old = self.create()
        with patch('profiles.signals.delete_exact', side_effect=RuntimeError('synthetic cleanup failure')):
            with self.assertRaises(RuntimeError):
                put(self.user.profile, self.ids[0], 1, self.upload(), expected_id=old.pk, expected_hash=old.sha256)
        current = CertificateEvidence.objects.get()
        self.assertNotEqual(current.pk, old.pk)
        self.assertTrue(Path(current.document.path).is_file())
        self.assertTrue(Path(old.document.path).is_file())  # Report-only orphan remains recoverable.

    def test_failed_writer_claim_cleans_only_request_file_without_another_database_read(self):
        old = self.create()
        with patch('profiles.certificates.claim', side_effect=OperationalError('synthetic locked writer')):
            with patch('django.db.models.query.QuerySet.exists', side_effect=AssertionError('unsafe extra read')):
                with self.assertRaises(OperationalError):
                    put(self.user.profile, self.ids[1], 1, self.upload())
        self.assertEqual(CertificateEvidence.objects.count(), 1)
        self.assertEqual(list(self.folder.rglob('*.pdf')), [Path(old.document.path)])

    def test_unknown_commit_and_failed_verification_preserve_potentially_referenced_bytes(self):
        atomic = transaction.atomic
        @contextmanager
        def uncertain_commit():
            with atomic():
                yield
            raise OperationalError('synthetic lost commit response')
        with patch('profiles.certificates.transaction.atomic', side_effect=uncertain_commit):
            with patch('django.db.models.query.QuerySet.exists', side_effect=OperationalError('synthetic unavailable verification')):
                with self.assertRaises(OperationalError):
                    self.create()
        row = CertificateEvidence.objects.get()
        self.assertTrue(Path(row.document.path).is_file())
        self.assertEqual(hashlib.sha256(Path(row.document.path).read_bytes()).hexdigest(), row.sha256)
