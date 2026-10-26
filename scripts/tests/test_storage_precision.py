from datetime import datetime, timezone
import importlib.util
import json
import tempfile
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('storage_rehearsal',
    Path(__file__).resolve().parents[1]/'storage_rehearsal.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FixturePrecisionTests(unittest.TestCase):
    def test_authorization_instant_keeps_all_microseconds(self):
        instant = datetime(2026, 10, 24, 12, 0, 0, 870680, tzinfo=timezone.utc)
        restored = json.loads(MODULE.fixture_json({'authorized_at': instant}))
        self.assertEqual(datetime.fromisoformat(restored['authorized_at']), instant)


class InterruptedMediaTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='ajiri-synthetic-copy-')
        self.addCleanup(folder.cleanup)
        self.source = Path(folder.name) / 'source'
        self.target = Path(folder.name) / 'target'
        self.source.mkdir()
        (self.source / 'first.bin').write_bytes(b'harmless first fixture')
        (self.source / 'second.bin').write_bytes(b'harmless second fixture')

    def test_interrupted_copy_reuses_verified_bytes_and_finishes(self):
        before = MODULE.file_hashes(self.source)
        with self.assertRaises(MODULE.CopyInterrupted):
            MODULE.resume_media_copy(self.source, self.target, fail_after=1)
        self.assertEqual(len(MODULE.file_hashes(self.target)), 1)
        self.assertEqual(MODULE.resume_media_copy(self.source, self.target), {'copied': 1, 'reused': 1})
        self.assertEqual(MODULE.file_hashes(self.target), before)
        self.assertEqual(MODULE.file_hashes(self.source), before)

    def test_changed_destination_blocks_without_overwrite_or_new_copy(self):
        with self.assertRaises(MODULE.CopyInterrupted):
            MODULE.resume_media_copy(self.source, self.target, fail_after=1)
        changed = self.target / 'first.bin'
        changed.write_bytes(b'changed synthetic destination')
        with self.assertRaisesRegex(ValueError, 'differs'):
            MODULE.resume_media_copy(self.source, self.target)
        self.assertEqual(changed.read_bytes(), b'changed synthetic destination')
        self.assertFalse((self.target / 'second.bin').exists())

    def test_nested_destination_cannot_modify_source_tree(self):
        nested = self.source / 'nested'
        with self.assertRaisesRegex(ValueError, 'Independent'):
            MODULE.resume_media_copy(self.source, nested)
        self.assertFalse(nested.exists())
