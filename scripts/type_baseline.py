"""Report legacy findings without masking a broken type-checker invocation.

see ../ajiri-backend/docs/CONCEPTS.md#incremental-quality
"""
import json
from pathlib import Path
import subprocess
import sys


def classify(result):
    errors = sum(': error:' in line for line in result.stdout.splitlines())
    if result.returncode == 0:
        return {'status': 'clean', 'errors': errors, 'blocking': False}, 0
    if result.returncode == 1 and errors:
        return {'status': 'legacy_findings', 'errors': errors, 'blocking': False}, 0
    return {'status': 'execution_failed', 'errors': errors, 'blocking': True}, 2


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / '.verification' / 'quality'
    output.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, '-m', 'mypy', '--config-file=mypy.ini'],
        cwd=root, capture_output=True, text=True)
    report, code = classify(result)
    (output / 'mypy.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
    (output / 'mypy-summary.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    if report['status'] == 'legacy_findings':
        print('Type findings are NONBLOCKING legacy baseline evidence, not a clean type check.')
    if code:
        print('Type checker did not execute normally; inspect the private verification report.')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
