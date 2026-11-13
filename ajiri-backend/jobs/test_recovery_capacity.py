from contextlib import closing
import gzip
import hashlib
from io import StringIO
import json
from pathlib import Path
import random
import sqlite3
import tarfile
import tempfile
from unittest import TestCase
import zipfile

from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, override_settings

from .recovery_capacity import capacity_plan, compressed_bound, MIB, zip_bound


class CapacityArithmeticTests(TestCase):
    def plan(self, **changes):
        values = dict(quota_bytes=512 * MIB, used_bytes=430 * MIB,
                      database_bytes=10 * MIB, media_sizes=[300000, 35905])
        values.update(changes)
        return capacity_plan(**values)

    def test_accounts_for_snapshot_transfer_and_reserve(self):
        plan = self.plan()
        self.assertTrue(plan['sufficient'])
        self.assertEqual(plan['required_additional_bytes'],
                         plan['snapshot_upper_bound_bytes'] + plan['transfer_bundle_upper_bound_bytes'] + 16 * MIB)
        self.assertEqual(plan['remaining_after_plan_bytes'], 82 * MIB - plan['required_additional_bytes'])
        self.assertFalse(plan['runtime_recovery_included'])

    def test_insufficient_and_overquota_never_become_free_space(self):
        self.assertFalse(self.plan(used_bytes=511 * MIB)['sufficient'])
        plan = self.plan(used_bytes=513 * MIB)
        self.assertEqual(plan['available_bytes'], -MIB)
        self.assertFalse(plan['sufficient'])

    def test_exact_boundary_and_additional_artifacts(self):
        plan = self.plan(ledger_present=True, ledger_sizes=[1024], extra_snapshot_bytes=MIB)
        required = plan['required_additional_bytes']
        self.assertTrue(self.plan(quota_bytes=430 * MIB + required, ledger_present=True,
                                  ledger_sizes=[1024], extra_snapshot_bytes=MIB)['sufficient'])
        self.assertFalse(self.plan(quota_bytes=430 * MIB + required - 1, ledger_present=True,
                                   ledger_sizes=[1024], extra_snapshot_bytes=MIB)['sufficient'])

    def test_rejects_invalid_byte_measurements(self):
        for change in [{'quota_bytes': 0}, {'used_bytes': -1}, {'media_sizes': [-1]},
                       {'reserve_bytes': -1}, {'database_bytes': True}, {'ledger_sizes': [1.5]}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.plan(**change)

    def test_incompressible_archives_fit_the_bounds(self):
        payload = random.Random(87).randbytes(32769)
        self.assertGreater(len(gzip.compress(payload)), len(payload))
        self.assertLessEqual(len(gzip.compress(payload)), compressed_bound(len(payload)))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'fixture.bin'
            source.write_bytes(payload)
            archive = root / 'private-media.tar.gz'
            with tarfile.open(archive, 'w:gz') as stream:
                stream.add(source, arcname='private/' + 'é' * 100 + '.bin')
            plan = self.plan(database_bytes=0, media_sizes=[len(payload)], reserve_bytes=0)
            self.assertLessEqual(archive.stat().st_size, plan['snapshot_upper_bound_bytes'] - 65536)
            bundle = root / 'transfer.zip'
            with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_DEFLATED) as stream:
                stream.writestr('fixture.bin', payload)
            self.assertLessEqual(bundle.stat().st_size, zip_bound(len(payload), 1, len('fixture.bin')))


class RecoveryPlanCommandTests(SimpleTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.database = self.root / 'source.sqlite3'
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute('CREATE TABLE fixture(value TEXT)')
            connection.execute("INSERT INTO fixture VALUES ('synthetic')")
            connection.commit()
        self.media = self.root / 'media'
        self.media.mkdir()
        (self.media / 'fixture.bin').write_bytes(b'synthetic private bytes')
        self.ledger = self.root / 'ledger'
        self.settings = override_settings(
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(self.database)}},
            MEDIA_ROOT=self.media, ERASURE_LEDGER_DIR=str(self.ledger))
        self.settings.enable()
        self.addCleanup(self.settings.disable)

    def run_plan(self, **changes):
        output = StringIO()
        values = dict(quota_bytes=512 * MIB, used_bytes=430 * MIB, stdout=output)
        values.update(changes)
        call_command('private_recovery_plan', **values)
        return json.loads(output.getvalue())

    def test_reads_sizes_without_copying_or_changing_private_data(self):
        before = {p.relative_to(self.root): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob('*') if p.is_file()}
        plan = self.run_plan()
        after = {p.relative_to(self.root): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(plan['media_files'], 1)
        self.assertTrue(plan['dry_run'])
        self.assertEqual(plan['retention'], 'report_only_no_deletion')
        self.assertNotIn(str(self.media), json.dumps(plan))

    def test_includes_ledger_without_printing_paths_or_contents(self):
        self.ledger.mkdir()
        (self.ledger / 'journal.json').write_text('synthetic ledger')
        plan = self.run_plan()
        self.assertEqual(plan['ledger_files_measured'], 1)
        self.assertNotIn('journal.json', json.dumps(plan))
        self.assertNotIn('synthetic', json.dumps(plan))

    def test_refuses_low_quota_without_creating_backup_or_pruning(self):
        before = set(self.root.rglob('*'))
        output = StringIO()
        with self.assertRaisesMessage(CommandError, 'Insufficient account-quota reserve'):
            self.run_plan(used_bytes=512 * MIB - 1, stdout=output)
        self.assertFalse(json.loads(output.getvalue())['sufficient'])
        self.assertEqual(before, set(self.root.rglob('*')))

    def test_refuses_missing_database_and_credential_named_media(self):
        with override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                                     'NAME': str(self.root / 'missing.sqlite3')}}):
            with self.assertRaises(CommandError):
                self.run_plan()
        (self.media / '.env').write_text('synthetic marker')
        with self.assertRaisesMessage(CommandError, 'credential-file name'):
            self.run_plan()

    def test_accounts_for_journals_without_opening_sqlite_or_creating_shared_memory(self):
        wal = Path(str(self.database) + '-wal')
        journal = Path(str(self.database) + '-journal')
        wal.write_bytes(b'synthetic WAL bytes')
        journal.write_bytes(b'synthetic rollback journal')
        plan = self.run_plan()
        self.assertEqual(plan['database_bytes'],
                         self.database.stat().st_size + wal.stat().st_size + journal.stat().st_size)
        self.assertFalse(Path(str(self.database) + '-shm').exists())

    def test_refuses_nonfile_journal_and_relative_private_media(self):
        Path(str(self.database) + '-wal').mkdir()
        with self.assertRaisesMessage(CommandError, 'journals must be regular files'):
            self.run_plan()
        Path(str(self.database) + '-wal').rmdir()
        with override_settings(MEDIA_ROOT='relative-media'):
            with self.assertRaisesMessage(CommandError, 'absolute directory'):
                self.run_plan()
