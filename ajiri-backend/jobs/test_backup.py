from datetime import datetime, timedelta, timezone
from contextlib import closing
from io import StringIO, BytesIO
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import tarfile
import tempfile
from unittest.mock import patch, MagicMock
from django.conf import settings
from django.core.management import call_command, CommandError
from django.test import SimpleTestCase
from .management.commands.backup_private_data import digest
from accounts.erasure import write_journal


class BackupTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = self.root / 'source'
        source.mkdir()
        self.db = source / 'db.sqlite3'
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute('CREATE TABLE sample (value TEXT)')
            connection.execute("INSERT INTO sample VALUES ('synthetic')")
        self.media = self.root / 'media'
        self.media.mkdir()
        (self.media / 'synthetic.pdf').write_bytes(b'%PDF-synthetic')
        self.destination = self.root / 'backups'
        self.options = self.settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': self.db}}, MEDIA_ROOT=self.media,
                                     ERASURE_LEDGER_DIR=str(self.root/'ledger'))
        self.options.enable()
        self.addCleanup(self.options.disable)

    def run_backup(self, *args):
        output = StringIO()
        call_command('backup_private_data', '--destination', str(self.destination), *args, stdout=output)
        return output.getvalue()

    def completed(self):
        return list(self.destination.glob('backup-*'))

    def test_dry_run_does_not_create_any_files_or_change_source(self):
        before = digest(self.db)
        result = self.run_backup('--dry-run', '--include-media')
        self.assertIn('no writes', result)
        self.assertFalse(self.destination.exists())
        self.assertEqual(digest(self.db), before)

    def test_erasure_journal_is_included_verified_and_restored_without_credentials(self):
        import uuid
        root = self.root/'ledger'; root.mkdir(mode=0o700)
        request = str(uuid.uuid4())
        write_journal(root/(request+'.signed'), {'format':1,'state':'complete','request_id':request,
            'user_id':123,'identity':'a'*64,'files':[]})
        self.run_backup('--include-media','--writers-paused')
        backup=self.completed()[0]
        manifest=json.loads((backup/'manifest.json').read_text())
        self.assertTrue(manifest['erasure_ledger_included']);self.assertEqual(manifest['erasure_journals'],1)
        target=self.root/'isolated-ledger-restore'
        call_command('verify_private_backup',backup=str(backup),restore_to=str(target),stdout=StringIO())
        self.assertEqual((target/'erasure-ledger'/(request+'.signed')).read_bytes(),(root/(request+'.signed')).read_bytes())
        self.assertFalse((target/'.env').exists())

    def test_unresolved_cleanup_or_unknown_ledger_files_never_publish_complete_backup(self):
        import uuid
        root=self.root/'ledger';root.mkdir(mode=0o700);request=str(uuid.uuid4())
        path=root/(request+'.signed')
        write_journal(path,{'format':1,'state':'db_erased','request_id':request,'files':['private.pdf']})
        with self.assertRaises(CommandError):self.run_backup()
        self.assertEqual(self.completed(),[])
        path.unlink();(root/'.env').write_text('synthetic-not-a-credential')
        with self.assertRaises(CommandError):self.run_backup()
        self.assertEqual(self.completed(),[])

    def test_packaged_app_without_git_can_back_up_with_explicit_unverified_revision(self):
        app = self.root / 'container-app'
        app.mkdir()
        with self.settings(BASE_DIR=app), patch(
                'jobs.management.commands.backup_private_data.subprocess.run', side_effect=FileNotFoundError):
            self.run_backup()
        manifest = json.loads((self.completed()[0] / 'manifest.json').read_text())
        self.assertEqual(manifest['revision'], 'unverified')
        self.assertTrue(manifest['complete'])

    def test_git_checkout_sibling_trees_are_not_backup_destinations(self):
        repo = self.root / 'repo'
        backend = repo / 'backend'
        backend.mkdir(parents=True)
        (repo / '.git').mkdir()
        with self.settings(BASE_DIR=backend), self.assertRaisesMessage(CommandError, 'outside application'):
            call_command('backup_private_data', '--destination', str(repo / 'frontend' / 'backups'), '--dry-run')

    def test_independent_verify_and_isolated_restore_never_overwrite_existing_folder(self):
        self.run_backup('--include-media', '--writers-paused')
        folder = self.completed()[0]
        restored = self.root / 'restored'
        output = StringIO()
        call_command('verify_private_backup', '--backup', str(folder), stdout=output)
        self.assertIn('no writes', output.getvalue())
        self.assertFalse(restored.exists())
        call_command('verify_private_backup', '--backup', str(folder), '--restore-to', str(restored), stdout=StringIO())
        self.assertEqual((restored/'media'/'synthetic.pdf').read_bytes(), b'%PDF-synthetic')
        self.assertTrue(json.loads((restored/'restore-verification.json').read_text())['complete'])
        with self.assertRaisesMessage(CommandError, 'new isolated'):
            call_command('verify_private_backup', '--backup', str(folder), '--restore-to', str(restored))

    def test_independent_verify_rejects_corruption_before_restore(self):
        self.run_backup()
        folder = self.completed()[0]
        (folder/'db.sqlite3').write_bytes(b'corrupt')
        restored = self.root/'must-not-exist'
        with self.assertRaisesMessage(CommandError, 'checksum mismatch'):
            call_command('verify_private_backup', '--backup', str(folder), '--restore-to', str(restored))
        self.assertFalse(restored.exists())

    def test_independent_verify_rejects_incomplete_manifest(self):
        self.run_backup()
        folder = self.completed()[0]
        manifest = folder/'manifest.json'
        data = json.loads(manifest.read_text()); data['complete'] = False
        manifest.write_text(json.dumps(data))
        with self.assertRaisesMessage(CommandError, 'completed format-1'):
            call_command('verify_private_backup', '--backup', str(folder))

    def test_independent_verify_rejects_traversal_even_with_matching_checksums(self):
        self.run_backup('--include-media', '--writers-paused')
        folder = self.completed()[0]
        archive = folder/'private-media.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            item = tarfile.TarInfo('../outside'); item.size = 1
            tar.addfile(item, BytesIO(b'x'))
        manifest = folder/'manifest.json'; data = json.loads(manifest.read_text())
        data['sha256']['private-media.tar.gz'] = digest(archive)
        with gzip.open(archive, 'rb') as stream:
            data['sha256']['media_uncompressed'] = hashlib.file_digest(stream, 'sha256').hexdigest()
        manifest.write_text(json.dumps(data))
        with self.assertRaisesMessage(CommandError, 'Unsafe archive'):
            call_command('verify_private_backup', '--backup', str(folder), '--restore-to', str(self.root/'unsafe'))
        self.assertFalse((self.root/'unsafe').exists())

    def test_database_snapshot_integrity_hash_and_unique_runs(self):
        before = digest(self.db)
        self.run_backup()
        self.run_backup()
        self.assertEqual(len(self.completed()), 2)
        for folder in self.completed():
            data = json.loads((folder / 'manifest.json').read_text())
            self.assertTrue(data['complete'])
            self.assertEqual(digest(folder / 'db.sqlite3'), data['sha256']['db.sqlite3'])
            with closing(sqlite3.connect((folder / 'db.sqlite3').as_uri()+'?mode=ro', uri=True)) as db:
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(db.execute('SELECT value FROM sample').fetchone()[0], 'synthetic')
        self.assertEqual(digest(self.db), before)

    def test_media_requires_paused_writers_and_archives_only_regular_data(self):
        with self.assertRaisesMessage(CommandError, '--writers-paused'):
            self.run_backup('--include-media')
        self.run_backup('--include-media', '--writers-paused')
        folder = self.completed()[0]
        data = json.loads((folder / 'manifest.json').read_text())
        self.assertEqual(data['media_files'], 1)
        with tarfile.open(folder / 'private-media.tar.gz') as archive:
            self.assertTrue(all(item.isfile() for item in archive))
            self.assertEqual(archive.extractfile('synthetic.pdf').read(), b'%PDF-synthetic')

    def test_interruption_leaves_partial_and_no_completion_marker(self):
        with patch('jobs.management.commands.backup_private_data.backup_sqlite', side_effect=OSError('private error')):
            with self.assertRaisesMessage(CommandError, 'incomplete'):
                self.run_backup()
        self.assertEqual(self.completed(), [])
        partials = list(self.destination.glob('.partial-*'))
        self.assertEqual(len(partials), 1)
        self.assertFalse((partials[0] / 'manifest.json').exists())

    def test_corrupt_database_is_never_published(self):
        self.db.write_bytes(b'not a SQLite database')
        with self.assertRaisesMessage(CommandError, 'incomplete'):
            self.run_backup()
        self.assertEqual(self.completed(), [])

    def test_unsafe_destinations_and_bad_retention(self):
        for destination in ['relative', str(self.media / 'backups'), str(self.db.parent / 'backups'), str(settings.BASE_DIR / 'backups')]:
            with self.assertRaises(CommandError):
                call_command('backup_private_data', '--destination', destination, '--dry-run')
        with self.assertRaises(CommandError):
            self.run_backup('--retention-days', '0')

    def test_retention_is_report_only_even_after_new_backup(self):
        self.run_backup()
        folder = self.completed()[0]
        manifest = folder / 'manifest.json'
        data = json.loads(manifest.read_text())
        data['created_at'] = (datetime.now(timezone.utc)-timedelta(days=50)).isoformat()
        manifest.write_text(json.dumps(data))
        original = digest(folder / 'db.sqlite3')
        result = self.run_backup()
        self.assertIn('1 candidates; no deletion', result)
        self.assertTrue(folder.exists())
        self.assertEqual(digest(folder / 'db.sqlite3'), original)

    def test_credential_names_in_media_are_rejected(self):
        (self.media / '.env').write_text('synthetic-only')
        with self.assertRaisesMessage(CommandError, 'credential-file'):
            self.run_backup('--include-media', '--writers-paused')
        self.assertFalse(self.destination.exists())

    def test_changed_media_aborts_without_completion(self):
        from .management.commands.backup_private_data import media_inventory
        initial = media_inventory(self.media)
        with patch('jobs.management.commands.backup_private_data.media_inventory', side_effect=[initial, {}]):
            with self.assertRaisesMessage(CommandError, 'incomplete'):
                self.run_backup('--include-media', '--writers-paused')
        self.assertEqual(self.completed(), [])

    def test_integrity_failure_never_publishes_completion(self):
        source, destination = MagicMock(), MagicMock()
        destination.execute.return_value.fetchone.return_value = ('corrupt',)
        with patch('jobs.management.commands.backup_private_data.sqlite3.connect', side_effect=[source, destination]):
            with self.assertRaisesMessage(CommandError, 'incomplete'):
                self.run_backup()
        self.assertEqual(self.completed(), [])
        self.assertFalse(any(self.destination.glob('.partial-*/manifest.json')))

    def test_linked_media_is_refused_without_extraction(self):
        with patch('jobs.management.commands.backup_private_data.Path.is_symlink', return_value=True):
            with self.assertRaisesMessage(CommandError, 'links'):
                self.run_backup('--include-media', '--dry-run')
        self.assertFalse(self.destination.exists())
