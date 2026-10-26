import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('scanner_engine_rehearsal',
    Path(__file__).resolve().parents[1]/'scanner_engine_rehearsal.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ScannerLabGuardTests(unittest.TestCase):
    def test_default_closed_before_docker_or_files(self):
        with patch.object(MODULE.subprocess, 'run') as process:
            with self.assertRaises(RuntimeError):
                MODULE.run()
        process.assert_not_called()

    def test_unknown_and_signal_exit_never_claims_clean(self):
        for code in [2, 9, -9, 124, 137, None]:
            self.assertEqual(MODULE.verdict(code), 'unavailable')

    def test_linux_shell_input_preserves_lf_bytes_on_windows(self):
        scan = MODULE.subprocess.CompletedProcess([], 0,
            stdout=b'ClamAV synthetic-test\nmatched=1\nclean=0\nunavailable=2\n')
        empty = MODULE.subprocess.CompletedProcess([], 0, stdout='')
        with patch.object(MODULE.subprocess, 'run', side_effect=[scan, empty]) as process:
            result = MODULE.run(synthetic_only=True)
        options = process.call_args_list[0].kwargs
        self.assertIsInstance(options['input'], bytes)
        self.assertNotIn(b'\r\n', options['input'])
        self.assertNotIn('text', options)
        self.assertFalse(result['production_scanning'])

    def test_timeout_still_cleans_only_exact_labelled_container(self):
        finished = MODULE.subprocess.CompletedProcess([], 0, stdout='abc123\n')
        with patch.object(MODULE.subprocess, 'run', side_effect=[
                MODULE.subprocess.TimeoutExpired('synthetic-test', 45), finished, finished]) as process:
            with self.assertRaises(MODULE.subprocess.TimeoutExpired):
                MODULE.run(synthetic_only=True)
        query = process.call_args_list[1].args[0]
        self.assertIn('label=ajiri.rehearsal=ajiri-scanner-', ' '.join(query))
        self.assertEqual(process.call_args_list[2].args[0][-3:], ['rm', '-f', 'abc123'])
