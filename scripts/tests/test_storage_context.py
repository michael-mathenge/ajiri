import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1]/'prepare_storage_rehearsal.py'
SPEC = importlib.util.spec_from_file_location('prepare_storage_rehearsal', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StorageContextTests(unittest.TestCase):
    def test_only_backend_source_and_nonsecret_example_are_allowed(self):
        self.assertTrue(MODULE.allowed_source('ajiri-backend/config/settings.py'))
        self.assertTrue(MODULE.allowed_source('ajiri-backend/.env.example'))
        for name in ['../secret', '/ajiri-backend/private.py', 'ajiri-backend/../secret',
                     'ajiri-backend\\secret', 'other/file.py', 'ajiri-backend/.env',
                     'ajiri-backend/db.SQLITE3', 'ajiri-backend/private.key',
                     'ajiri-backend/private.pdf', 'ajiri-backend/cv.docx']:
            self.assertFalse(MODULE.allowed_source(name), name)

    def test_untracked_private_files_never_enter_the_build_context(self):
        with tempfile.TemporaryDirectory(prefix='ajiri-context-unit-') as folder:
            root=Path(folder)
            for name in ['ajiri-backend/config/settings.py', 'ajiri-backend/.env.example',
                         'ajiri-backend/.env', 'ajiri-backend/db.sqlite3',
                         'scripts/storage_rehearsal.py', 'scripts/storage-rehearsal/Dockerfile']:
                path=root/name; path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('Synthetic fixture content',encoding='utf-8')
            with patch.object(MODULE.subprocess,'check_output',side_effect=[
                b'ajiri-backend/config/settings.py\0ajiri-backend/.env.example\0',b'0'*40]):
                context=MODULE.prepare(root)
            self.assertFalse((context/'backend/.env').exists())
            self.assertFalse((context/'backend/db.sqlite3').exists())
            manifest=json.loads((context/'source-manifest.json').read_text())
            self.assertEqual(set(manifest['backend_sha256']),{'config/settings.py','.env.example'})
            self.assertTrue(manifest['synthetic_only'])

    def test_tracked_private_data_is_rejected_before_export(self):
        with tempfile.TemporaryDirectory(prefix='ajiri-context-unit-') as folder:
            with patch.object(MODULE.subprocess,'check_output',return_value=b'ajiri-backend/.env\0'):
                with self.assertRaises(ValueError): MODULE.prepare(Path(folder))
