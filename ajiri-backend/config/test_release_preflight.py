from pathlib import Path
import tempfile
from unittest.mock import patch
from django.test import SimpleTestCase
from scripts.release_preflight import inspect_release


class ReleasePreflightTests(SimpleTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        build = self.repo/'ajiri-backend'/'frontend_build'
        (build/'assets').mkdir(parents=True)
        (build/'index.html').write_text('<script src="/assets/main.js"></script>')
        (build/'assets'/'main.js').write_text('synthetic')
        self.revision, self.previous = 'a'*40, 'b'*40

    def fake_git(self, repo, *args):
        if args[:2] == ('rev-parse', '--verify'):
            return args[2].split('^')[0]
        if args == ('rev-parse', 'HEAD'):
            return self.revision
        return ''

    def test_clean_plan_is_read_only_and_uses_exact_reviewed_source(self):
        with patch('scripts.release_preflight.git', side_effect=self.fake_git):
            result = inspect_release(self.repo, self.revision, self.previous)
        self.assertTrue(result['dry_run'])
        self.assertFalse(result['pip_install_required'])
        self.assertEqual(result['expected_migrations'], [])
        self.assertFalse((self.repo/'ajiri-backend'/'db.sqlite3').exists())

    def test_dirty_checkout_and_unreviewed_migration_stop(self):
        def dirty(repo, *args):
            return ' M private-local-file' if args == ('status', '--porcelain') else self.fake_git(repo, *args)
        with patch('scripts.release_preflight.git', side_effect=dirty), self.assertRaisesMessage(ValueError, 'uncommitted'):
            inspect_release(self.repo, self.revision, self.previous)
        def migration(repo, *args):
            return 'A\tajiri-backend/profiles/migrations/0006_privacy_notice.py' if args[0] == 'diff' else self.fake_git(repo, *args)
        with patch('scripts.release_preflight.git', side_effect=migration), self.assertRaisesMessage(ValueError, 'reviewed list'):
            inspect_release(self.repo, self.revision, self.previous)

    def test_unsafe_asset_and_abbreviated_revision_stop(self):
        with self.assertRaisesMessage(ValueError, '40-character'):
            inspect_release(self.repo, 'short', self.previous)
        (self.repo/'ajiri-backend'/'frontend_build'/'index.html').write_text('<script src="/assets/../../.env"></script>')
        with patch('scripts.release_preflight.git', side_effect=self.fake_git), self.assertRaisesMessage(ValueError, 'unsafe'):
            inspect_release(self.repo, self.revision, self.previous)
