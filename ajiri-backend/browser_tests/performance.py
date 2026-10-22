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



def trace_diagnostic(paths, browser_version):
    """Only counts of fixed event names; never trace args, URLs, IDs or source."""
    names = ('navigationStart', 'TracingStartedInPage', 'TracingStartedInBrowser',
             'thread_name', 'process_name', 'firstContentfulPaint', 'largestContentfulPaint::Candidate')
    result = {'browser': browser_version, 'trace_found': False,
              'events': {name: 0 for name in names}}
    for path in paths:
        if path.stat().st_size > 100 * 1024 * 1024:
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            events = data.get('traceEvents', [])
            if not isinstance(events, list):
                continue
            result['trace_found'] = True
            for event in events:
                name = event.get('name') if isinstance(event, dict) else None
                if name in result['events']:
                    result['events'][name] += 1
        except (OSError, ValueError, AttributeError):
            continue
    return result


def trace_retry_allowed(returncode, stderr, used):
    return returncode != 0 and 'NO_NAVSTART' in stderr and used == 0


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
        browser_version = 'unavailable'
        output = settings.BASE_DIR.parent / '.verification' / 'performance'
        output.mkdir(parents=True, exist_ok=True)
        summary = {}
        trace_retries = 0
        for route in ('login', 'register'):
            retries_before = trace_retries
            runs = []
            for number in range(3):
                report = output / f'{route}-{number}.json'
                command = [node, str(cli), self.live_server_url + '/' + route,
                    '--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage',
                    '--save-assets', '--only-categories=performance', '--output=json', '--output-path=' + str(report), '--quiet']
                result = subprocess.run(command,
                    env=env, capture_output=True, text=True, timeout=100)
                # Chromium can lose its navigation trace (upstream lighthouse#15382).
                # One fresh-process retry TOTAL; never retry a metric/budget failure.
                if trace_retry_allowed(result.returncode, result.stderr, trace_retries):
                    trace_retries += 1
                    print('Lighthouse NO_NAVSTART: one fresh-browser trace retry.')
                    result = subprocess.run(command,
                        env=env, capture_output=True, text=True, timeout=100)
                if report.is_file():
                    try:
                        user_agent = json.loads(report.read_text(encoding='utf-8')).get('environment', {}).get('hostUserAgent', '')
                        version_match = re.search(r'(?:HeadlessChrome|Chrome)/[0-9.]+', user_agent)
                        browser_version = version_match.group(0) if version_match else 'unavailable'
                    except (OSError, ValueError, AttributeError):
                        browser_version = 'unavailable'
                if result.returncode:
                    # Existing CI uploads summary.json only. Keep raw trace/assets local
                    # and emit fixed-name counts, never URLs, trace args or page source.
                    diagnostic = trace_diagnostic(output.glob(f'{route}-{number}*.trace.json'), browser_version)
                    (output / 'summary.json').write_text(json.dumps({'runner_failure': diagnostic}, indent=2) + '\n', encoding='utf-8')
                    print('Lighthouse trace diagnostic:', json.dumps(diagnostic, sort_keys=True))
                    (output / 'runner-errors.txt').write_text((result.stdout + result.stderr)[-10000:], encoding='utf-8')
                self.assertEqual(result.returncode, 0,
                    'Lighthouse execution failed: ' + runner_diagnostic(result.stderr))
                runs.append(metrics(json.loads(report.read_text(encoding='utf-8'))))
            summary[route] = {key: statistics.median(row[key] for row in runs) for key in runs[0]}
            summary[route]['trace_retries'] = trace_retries - retries_before
        (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        if os.environ.get('AJIRI_LIGHTHOUSE_MEASURE_ONLY') == '1':
            self.skipTest('Measurement only: no performance budget asserted.')
        budgets = json.loads((settings.BASE_DIR.parent / 'lighthouse-budgets.json').read_text())
        for route, measured in summary.items():
            self.assertEqual(budget_failures(measured, budgets), [], f'{route}: performance budget exceeded')
