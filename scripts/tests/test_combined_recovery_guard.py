"""The combined lab must reject ordinary/programmatic misuse before any service IO."""
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
import sys
from unittest.mock import patch


class CombinedRecoveryGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1]/'combined_recovery_rehearsal.py'
        spec = importlib.util.spec_from_file_location('combined_lab', path)
        cls.lab = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.lab)

    def test_invalid_phases_fail_before_importing_django(self):
        for value in ('', None, 1, 'production', 'SOURCE'):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                self.lab.setup(value)

    def test_explicit_flag_and_container_source_are_required(self):
        with patch.object(self.lab.os, 'name', 'posix'), patch.dict(self.lab.os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                self.lab.require_lab('source')
        with patch.object(self.lab.os, 'name', 'posix'), patch.dict(self.lab.os.environ,
                {'AJIRI_COMBINED_REHEARSAL': 'synthetic-only'}), patch.object(self.lab.Path, 'is_file', return_value=False):
            with self.assertRaises(RuntimeError):
                self.lab.require_lab('source')

    def test_unready_worker_never_starts_process(self):
        with patch.object(self.lab.Path, 'is_file', return_value=False), patch.object(self.lab.subprocess, 'Popen') as start:
            with self.assertRaises(RuntimeError):
                self.lab.Workers().start()
            start.assert_not_called()

    def test_restored_identity_is_rebound_only_after_exact_content_check(self):
        old = {'key': 'private/synthetic.pdf', 'size': 3, 'sha256': 'a'*64, 'version': 'old-inode'}
        new = dict(old, version='new-inode')
        backend = SimpleNamespace(inventory=lambda origin: [new])
        with patch.dict(sys.modules, {'profiles.private_copy': backend}):
            self.assertEqual(self.lab.restored_references(None, {'objects': [old]}), [new])
        for rows in ([dict(new, sha256='b'*64)], [dict(new, size=4)],
                [dict(new, key='private/other.pdf')], [new, new], []):
            with self.subTest(rows=rows), patch.dict(sys.modules,
                    {'profiles.private_copy': SimpleNamespace(inventory=lambda origin: rows)}):
                with self.assertRaises(AssertionError):
                    self.lab.restored_references(None, {'objects': [old]})

    def test_operator_refuses_to_stop_foreign_containers(self):
        path = Path(__file__).resolve().parents[1]/'run_combined_recovery.py'
        spec = importlib.util.spec_from_file_location('combined_operator', path)
        operator = importlib.util.module_from_spec(spec); spec.loader.exec_module(operator)
        lab = operator.Lab(None)
        with patch.object(operator, 'docker', return_value=b'[{"Config":{"Labels":{}},"State":{"Running":true}}]') as command:
            with self.assertRaises(RuntimeError):
                lab.stop(['foreign'])
            command.assert_called_once_with('inspect', 'foreign')
