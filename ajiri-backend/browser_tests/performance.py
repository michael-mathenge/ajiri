"""Mobile Lighthouse budgets against disposable local public pages, never production."""
import json
import math
import os
import re
from pathlib import Path
import shutil
import statistics
import subprocess

from django.conf import settings
from django.test import LiveServerTestCase, override_settings
from .accessibility import tools_root


def metrics(report):
    if report.get('runtimeError') or report['configSettings']['formFactor'] != 'mobile':
        raise ValueError('A successful mobile audit is required.')
    audits = report['audits']
    score = report['categories']['performance']['score']
    if type(score) not in (int, float) or not 0 <= score <= 1:
        raise ValueError('Missing performance score.')
    result = {'performance': score * 100,
        'lcp_ms': audits['largest-contentful-paint']['numericValue'],
        'tbt_ms': audits['total-blocking-time']['numericValue'],
        'cls': audits['cumulative-layout-shift']['numericValue'],
        'transfer_bytes': audits['total-byte-weight']['numericValue']}
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in result.values()):
        raise ValueError('Finite nonnegative measurements are required.')
    return result


def budget_failures(measured, budgets):
    failed = ['performance'] if measured['performance'] < budgets['minimum_performance'] else []
    failed.extend(key for key, limit in budgets['maximum'].items() if measured[key] > limit)
    return failed


def runner_diagnostic(stderr):
    # Only synthetic local pages run here; still strip URLs/paths before CI logs.
    message = re.sub(r'https?://\S+|(?:[A-Za-z]:)?[/\\][^\s]+', '<redacted>', stderr)
    return message[-1500:]


@override_settings(DEBUG=False, ALLOWED_HOSTS=['localhost', '127.0.0.1'],
    SECURE_SSL_REDIRECT=False, SECURE_HSTS_SECONDS=0, REFRESH_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False, SESSION_COOKIE_SECURE=False,
    REAL_EMAIL_ENABLED=False, ALERT_EMAIL_ENABLED=False, BREVO_API_KEY='', INGEST_API_KEY='')
class MobilePerformance(LiveServerTestCase):
    host = '127.0.0.1'

    def test_public_mobile_budgets(self):
        # see docs/CONCEPTS.md#accessibility-performance-budgets
        node = os.environ.get('NODE_BINARY') or shutil.which('node')
        self.assertIsNotNone(node, 'Node24.19 is required for Lighthouse.')
        version = subprocess.check_output([node, '--version'], text=True).strip()
        self.assertTrue(version.startswith('v24.19.'), 'Use Node24.19 explicitly.')
        cli = tools_root() / 'node_modules' / 'lighthouse' / 'cli' / 'index.js'
        self.assertTrue(cli.is_file(), 'Run the locked frontend installation before Lighthouse.')
        env = os.environ.copy()
        if not env.get('CHROME_PATH'):
            from playwright.sync_api import sync_playwright
            with sync_playwright() as playwright:
                env['CHROME_PATH'] = playwright.chromium.executable_path
        self.assertTrue(Path(env['CHROME_PATH']).is_file(), 'Install the supported test Chromium.')
        output = settings.BASE_DIR.parent / '.verification' / 'performance'
        output.mkdir(parents=True, exist_ok=True)
        summary = {}
        for route in ('login', 'register'):
            runs = []
            for number in range(3):
                report = output / f'{route}-{number}.json'
                result = subprocess.run([node, str(cli), self.live_server_url + '/' + route,
                    '--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage',
                    '--only-categories=performance', '--output=json', '--output-path=' + str(report), '--quiet'],
                    env=env, capture_output=True, text=True, timeout=100)
                if result.returncode:
                    (output / 'runner-errors.txt').write_text((result.stdout + result.stderr)[-10000:], encoding='utf-8')
                self.assertEqual(result.returncode, 0,
                    'Lighthouse execution failed: ' + runner_diagnostic(result.stderr))
                runs.append(metrics(json.loads(report.read_text(encoding='utf-8'))))
            summary[route] = {key: statistics.median(row[key] for row in runs) for key in runs[0]}
        (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        if os.environ.get('AJIRI_LIGHTHOUSE_MEASURE_ONLY') == '1':
            self.skipTest('Measurement only: no performance budget asserted.')
        budgets = json.loads((settings.BASE_DIR.parent / 'lighthouse-budgets.json').read_text())
        for route, measured in summary.items():
            self.assertEqual(budget_failures(measured, budgets), [], f'{route}: performance budget exceeded')
