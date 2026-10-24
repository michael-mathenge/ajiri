import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings


class AccountExportTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.media = self.root / 'media'
        self.media.mkdir()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.owner = get_user_model().objects.create_user(email='export@example.invalid', password='Synthetic-only-123')
        self.other = get_user_model().objects.create_user(email='other@example.invalid', password='Synthetic-only-456')
        self.owner.profile.cv_file.save('resume.pdf', ContentFile(b'%PDF-synthetic'), save=True)
        self.other.profile.cv_file.save('other.pdf', ContentFile(b'private-other'), save=True)

    def run_export(self, **extra):
        options = {'user_id': self.owner.pk, 'destination': str(self.root / 'export'),
                   'verified_request': True, 'writers_paused': True, 'stdout': StringIO()}
        options.update(extra)
        call_command('export_account_data', **options)
        return options['stdout'].getvalue()

    def test_dry_run_does_not_create_destination_or_change_account(self):
        self.assertIn('no writes', self.run_export(dry_run=True, verified_request=False, writers_paused=False))
        self.assertFalse((self.root / 'export').exists())
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_active)

    def test_export_contains_owned_bytes_and_no_other_owner_or_secrets(self):
        self.run_export()
        root = self.root / 'export'
        data = json.loads((root / 'account.json').read_text(encoding='utf-8'))
        self.assertEqual(data['account']['email'], self.owner.email)
        self.assertNotIn('password', data['account'])
        self.assertNotIn(self.other.email, (root / 'account.json').read_text())
        document = data['records']['profile'][0]['cv_file']
        self.assertEqual((root / document).read_bytes(), b'%PDF-synthetic')
        manifest = json.loads((root / 'manifest.json').read_text())
        self.assertTrue(manifest['complete'])
        for name, digest in manifest['sha256'].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
        self.assertEqual(len(list((root / 'documents').iterdir())), 1)

    def test_execution_requires_verified_request_and_writer_window(self):
        for options in ({'verified_request': False}, {'writers_paused': False}):
            with self.assertRaises(CommandError):
                self.run_export(**options)
        self.assertFalse((self.root / 'export').exists())

    def test_saved_search_export_is_owner_scoped_and_includes_match_job_context(self):
        from django.utils import timezone
        from jobs.models import SavedSearch, SavedSearchMatch, Job
        from jobs.saved_searches import reset_windows
        search = SavedSearch(owner=self.owner, name='Owned synthetic query', q='Python')
        reset_windows(search, timezone.now())
        search.save()
        other = SavedSearch(owner=self.other, name='Other private query')
        reset_windows(other, timezone.now())
        other.save()
        job = Job.objects.create(title='Synthetic export job', company_name='Synthetic',
            source_url='https://example.invalid/saved-export', source_name='synthetic')
        SavedSearchMatch.objects.create(search=search, revision=1, channel='in_app', job=job,
            window_start=timezone.now(), window_end=timezone.now())
        self.run_export()
        data = json.loads((self.root / 'export' / 'account.json').read_text())
        self.assertEqual([row['name'] for row in data['records']['saved_search']], ['Owned synthetic query'])
        self.assertEqual(len(data['records']['saved_search_match']), 1)
        self.assertNotIn('email_attempt', data['records']['saved_search_match'][0])
        self.assertEqual([row['title'] for row in data['records']['job']], ['Synthetic export job'])
        self.assertNotIn('Other private query', json.dumps(data))

    def test_unsafe_or_existing_destination_rejected_without_overwrite(self):
        for destination in (str(self.media / 'export'), str(self.root), 'relative'):
            with self.assertRaises(CommandError):
                self.run_export(destination=destination)
        self.assertTrue(self.media.is_dir())

    def test_missing_private_file_fails_before_creating_export(self):
        Path(self.owner.profile.cv_file.path).unlink()
        with self.assertRaises(CommandError):
            self.run_export()
        self.assertFalse((self.root / 'export').exists())

    def test_interrupted_copy_never_writes_completion(self):
        with patch('accounts.management.commands.export_account_data.hashlib.file_digest', side_effect=OSError):
            with self.assertRaises(CommandError):
                self.run_export()
        self.assertFalse((self.root / 'export' / 'manifest.json').exists())
