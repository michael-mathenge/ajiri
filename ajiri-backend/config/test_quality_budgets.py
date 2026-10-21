from copy import deepcopy
from django.test import SimpleTestCase
from browser_tests.performance import metrics, budget_failures, runner_diagnostic, trace_retry_allowed


class LighthouseGuardTests(SimpleTestCase):
    def test_runner_diagnostics_strip_urls_and_filesystem_paths(self):
        message = runner_diagnostic('Error at https://example.invalid/private?token=synthetic /home/test/report.json')
        self.assertNotIn('token', message)
        self.assertNotIn('/home', message)
        self.assertIn('Error at', message)
        self.assertTrue(trace_retry_allowed(1, 'NO_NAVSTART', 0))
        self.assertFalse(trace_retry_allowed(1, 'NO_NAVSTART', 1))
        self.assertFalse(trace_retry_allowed(1, 'NO_FCP', 0))
        self.assertFalse(trace_retry_allowed(0, 'NO_NAVSTART', 0))

    def report(self):
        return {'configSettings': {'formFactor': 'mobile'},
            'categories': {'performance': {'score': 0.99}},
            'audits': {name: {'numericValue': value} for name, value in [
                ('largest-contentful-paint', 1000), ('total-blocking-time', 10),
                ('cumulative-layout-shift', 0.01), ('total-byte-weight', 100000)]}}

    def test_strong_score_cannot_hide_payload_or_timing_regression(self):
        measured = metrics(self.report())
        budget = {'minimum_performance': 80,
            'maximum': {'lcp_ms': 900, 'tbt_ms': 100, 'cls': 0.1, 'transfer_bytes': 90000}}
        self.assertEqual(budget_failures(measured, budget), ['lcp_ms', 'transfer_bytes'])

    def test_desktop_and_failed_audit_cannot_count_as_mobile_pass(self):
        for change in ('desktop', 'error'):
            report = self.report()
            if change == 'desktop':
                report['configSettings']['formFactor'] = 'desktop'
            else:
                report['runtimeError'] = {'code': 'NO_FCP'}
            with self.assertRaises(ValueError):
                metrics(report)

    def test_missing_and_nonfinite_metrics_fail_closed(self):
        for value in (None, float('nan'), float('inf'), -1):
            report = deepcopy(self.report())
            report['audits']['total-blocking-time']['numericValue'] = value
            with self.assertRaises(ValueError):
                metrics(report)
