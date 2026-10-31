import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.test import SimpleTestCase
from .storage_copy import StorageCopyBlocked, copy_private_storage, _exclusive


class StorageCopyTests(SimpleTestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.source = FileSystemStorage(location=self.root/'source')
        self.target = FileSystemStorage(location=self.root/'target')
        self.journal = self.root/'private-journal.json'
        self.names = ['quarantine/certificates/test.pdf', 'approved-cvs/test.docx']
        for index, name in enumerate(self.names):
            self.source.save(name, ContentFile(b'synthetic private bytes '+bytes([index])))

    def copy(self):
        return copy_private_storage(self.source, self.target, self.names, self.journal,
            writers_paused=True, target_private=True)

    def test_exact_private_copy_and_isolated_restore_verify_bytes_without_source_changes(self):
        result = self.copy()
        self.assertEqual(result['copied'], 2)
        self.assertFalse(result['changed_source'])
        self.assertFalse(result['cutover'])
        restored = FileSystemStorage(location=self.root/'restored')
        copy_private_storage(self.target, restored, self.names, self.root/'restore-journal.json',
            writers_paused=True, target_private=True)
        for name in self.names:
            with self.source.open(name) as left, restored.open(name) as right:
                self.assertEqual(left.read(), right.read())
        self.assertEqual(self.copy()['reused'], 2)

    def test_absent_attestations_unsafe_names_and_overlapping_roots_transfer_nothing(self):
        with self.assertRaises(StorageCopyBlocked):
            copy_private_storage(self.source, self.target, self.names, self.journal)
        for names, target in [(['../outside'], self.target), (self.names, self.source)]:
            with self.assertRaises(StorageCopyBlocked):
                copy_private_storage(self.source, target, names, self.journal, writers_paused=True, target_private=True)
        self.assertFalse(self.journal.exists())

    def test_unknown_write_after_complete_bytes_resolves_by_read_without_second_write(self):
        original = self.target.save
        count = 0

        def uncertain(name, content, **kwargs):
            nonlocal count
            count += 1
            original(name, content, **kwargs)
            raise TimeoutError

        with patch.object(self.target, 'save', uncertain):
            with self.assertRaises(StorageCopyBlocked):
                self.copy()
        self.assertEqual(count, 1)
        with patch.object(self.target, 'save', wraps=original) as save:
            result = self.copy()
        self.assertEqual(result['reused'], 1)
        self.assertEqual(save.call_count, 1)  # Only the other, never-attempted entry.

    def test_unknown_missing_write_and_partial_bytes_are_never_overwritten_on_resume(self):
        with patch.object(self.target, 'save', side_effect=TimeoutError) as save:
            with self.assertRaises(StorageCopyBlocked):
                self.copy()
            with self.assertRaises(StorageCopyBlocked):
                self.copy()
            save.assert_called_once()
        name = sorted(self.names)[0]
        self.target.save(name, ContentFile(b'partial'))
        with patch.object(self.target, 'save') as save:
            with self.assertRaises(StorageCopyBlocked):
                self.copy()
            save.assert_not_called()
        with self.target.open(name) as stream:
            self.assertEqual(stream.read(), b'partial')

    def test_corrupt_journal_and_different_existing_target_are_preserved(self):
        self.copy()
        data = json.loads(self.journal.read_text())
        data['body']['complete'] = False
        self.journal.write_text(json.dumps(data))
        with self.assertRaises(StorageCopyBlocked):
            self.copy()
        self.assertTrue(self.source.exists(self.names[0]))

    def test_source_mutation_during_transfer_prevents_completion(self):
        original = self.target.save

        def mutate(name, content, **kwargs):
            result = original(name, content, **kwargs)
            Path(self.source.path(name)).write_bytes(b'synthetic changed source')
            return result

        with patch.object(self.target, 'save', mutate):
            with self.assertRaises(StorageCopyBlocked):
                self.copy()
        self.assertFalse(json.loads(self.journal.read_text())['body']['complete'])

    def test_concurrent_journal_owner_cannot_start_a_second_handoff(self):
        with _exclusive(self.journal), patch.object(self.target, 'save') as save:
            with self.assertRaises(StorageCopyBlocked):
                self.copy()
            save.assert_not_called()
