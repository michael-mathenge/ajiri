"""Real scanner, harmless fixtures only; no uploads or production integration.

see docs/CONCEPTS.md#isolated-scanner-engine-rehearsal
"""
import argparse
import base64
import hashlib
import json
import subprocess
import uuid

IMAGE = 'clamav/clamav@sha256:751df8dc649cc977696f107c80db4960b6317a7cb511aebc8066f3b91db6b631'
DOCKER = ['docker', '--context', 'desktop-linux']


def verdict(code):
    return {0: 'clean', 1: 'infected'}.get(code, 'unavailable')


def fixture_script():
    target = b'\x00\x01AJIRI HARMLESS SYNTHETIC FIXTURE\x02' * 8
    encoded = base64.b64encode(target).decode('ascii')
    signature = f'{hashlib.sha256(target).hexdigest()}:{len(target)}:Ajiri.SyntheticOnly'
    # Inputs are constants generated here, never user files or shell fragments.
    return f'''set -u
printf '%s' '{encoded}' | base64 -d > /tmp/target.bin
printf 'harmless unmatched fixture' > /tmp/clean.bin
printf '%s\\n' '{signature}' > /tmp/synthetic.hsb
clamscan --version
clamscan --no-summary -d /tmp/synthetic.hsb /tmp/target.bin > /tmp/matched.out 2>&1
matched=$?
grep -q 'Ajiri.SyntheticOnly' /tmp/matched.out || exit 9
clamscan --no-summary -d /tmp/synthetic.hsb /tmp/clean.bin > /tmp/clean.out 2>&1
clean=$?
clamscan --no-summary -d /tmp/missing.hsb /tmp/clean.bin > /tmp/unavailable.out 2>&1
unavailable=$?
printf 'matched=%s\\nclean=%s\\nunavailable=%s\\n' "$matched" "$clean" "$unavailable"
test "$matched" = 1 && test "$clean" = 0 && test "$unavailable" = 2
'''


def run(*, synthetic_only=False):
    if synthetic_only is not True:
        raise RuntimeError('Explicit synthetic-only rehearsal required; no files accepted.')
    identity = 'ajiri-scanner-' + uuid.uuid4().hex
    label = f'ajiri.rehearsal={identity}'
    try:
        result = subprocess.run(DOCKER + ['run', '--rm', '-i', '--pull=never',
            '--name', identity, '--label', label, '--network', 'none', '--read-only',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--user', '10001:10001',
            '--memory', '256m', '--cpus', '1', '--pids-limit', '32',
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m', '--entrypoint', 'sh', IMAGE, '-s'],
            # Windows text mode translates LF to CRLF, which changes shell options.
            input=fixture_script().encode('utf-8'), capture_output=True, timeout=45, check=True)
        lines = result.stdout.decode('utf-8').splitlines()
        assert 'matched=1' in lines and 'clean=0' in lines and 'unavailable=2' in lines
        engine = next(line for line in lines if line.startswith('ClamAV '))
        return {'synthetic_only': True, 'engine': engine, 'image': IMAGE,
            'matched_fixture': verdict(1), 'unmatched_fixture': verdict(0),
            'missing_database': verdict(2), 'vendor_signature_database': False,
            'network': False, 'private_files': False, 'production_scanning': False}
    finally:
        # Timeouts must not leave this exact labelled synthetic container behind.
        remaining = subprocess.run(DOCKER + ['ps', '-aq', '--filter', f'label={label}',
            '--filter', f'name=^/{identity}$'], capture_output=True, text=True, timeout=15)
        ids = remaining.stdout.split()
        if remaining.returncode == 0 and len(ids) == 1:
            subprocess.run(DOCKER + ['rm', '-f', ids[0]], check=True,
                capture_output=True, timeout=15)
        elif ids or remaining.returncode:
            raise RuntimeError('Could not verify synthetic scanner cleanup.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synthetic-only', action='store_true')
    arguments = parser.parse_args()
    print('AJIRI_SCANNER_REHEARSAL_RESULT=' + json.dumps(
        run(synthetic_only=arguments.synthetic_only), sort_keys=True))
