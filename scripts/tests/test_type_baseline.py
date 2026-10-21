from pathlib import Path
import importlib.util
from subprocess import CompletedProcess
import unittest

spec = importlib.util.spec_from_file_location('type_baseline', Path(__file__).parents[1] / 'type_baseline.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BaselineResultTests(unittest.TestCase):
    def test_legacy_errors_are_counted_and_explicitly_nonblocking(self):
        report, code = module.classify(CompletedProcess([], 1, 'jobs/example.py:4: error: wrong type [arg-type]\n', ''))
        self.assertEqual(report, {'status': 'legacy_findings', 'errors': 1, 'blocking': False})
        self.assertEqual(code, 0)

    def test_missing_checker_or_internal_failure_cannot_pass_as_legacy(self):
        for status in (1, 2):
            report, code = module.classify(CompletedProcess([], status, '', 'No module named mypy'))
            self.assertEqual(report['status'], 'execution_failed')
            self.assertNotEqual(code, 0)

    def test_clean_result_is_distinct_from_findings(self):
        report, code = module.classify(CompletedProcess([], 0, 'Success: no issues found\n', ''))
        self.assertEqual(report['status'], 'clean')
        self.assertEqual(report['errors'], 0)
        self.assertEqual(code, 0)
