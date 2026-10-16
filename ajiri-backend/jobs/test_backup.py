from datetime import datetime, timedelta, timezone
from contextlib import closing
from io import StringIO
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
        self.options = self.settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': self.db}}, MEDIA_ROOT=self.media)
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
