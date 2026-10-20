"""Read-only release plan. Never fetches, installs, migrates or activates code."""
# see docs/CONCEPTS.md#release-preflight
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def git(repo, *args):
    return subprocess.run(['git', *args], cwd=repo, capture_output=True,
                          text=True, check=True).stdout.strip()


def inspect_release(repo, revision, previous, expected=()):
    for sha in (revision, previous):
        if not re.fullmatch(r'[0-9a-f]{40}', sha):
            raise ValueError('Use full lowercase 40-character reviewed commit SHAs.')
        if git(repo, 'rev-parse', '--verify', sha+'^{commit}') != sha:
            raise ValueError('Reviewed commit is unavailable locally.')
    if git(repo, 'rev-parse', 'HEAD') != revision:
        raise ValueError('Checkout must match the reviewed release SHA.')
    if git(repo, 'status', '--porcelain'):
        raise ValueError('Checkout has uncommitted changes; preserve them and use a clean checkout.')
    changes = git(repo, 'diff', '--name-status', previous, revision).splitlines()
    migrations, dependencies = [], False
    for line in changes:
        state, path = line.split('\t', 1)
        if '/migrations/' in path and path.endswith('.py') and not path.endswith('/__init__.py'):
            if state != 'A':
                raise ValueError('Historical migration changes require separate investigation.')
            parts = Path(path).parts
            migrations.append(parts[parts.index('migrations')-1]+'.'+Path(path).stem)
        dependencies |= path == 'ajiri-backend/requirements-prod.txt'
    if set(migrations) != set(expected):
        raise ValueError('Changed migrations do not match the explicitly reviewed list.')
    build = repo/'ajiri-backend'/'frontend_build'
    index = (build/'index.html').read_text(encoding='utf-8')
    assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', index)
    if not assets:
        raise ValueError('Committed frontend asset references are missing.')
    for name in assets:
        asset = (build/name.lstrip('/')).resolve()
        if not asset.is_relative_to(build.resolve()) or not asset.is_file():
            raise ValueError('Committed frontend asset is missing or unsafe.')
    return {'dry_run': True, 'revision': revision, 'previous_revision': previous,
        'expected_migrations': sorted(migrations), 'pip_install_required': dependencies,
        'frontend_index_sha256': hashlib.sha256((build/'index.html').read_bytes()).hexdigest(),
        'ordered_steps': [
            'Confirm required CI, quota, private rollback and writer pause.',
            'Take backup before staging code; independently verify off-server copy and isolated restore.',
            'Stage this exact reviewed SHA; install requirements-prod.txt in the existing virtualenv only if changed.',
            'Run check, migration drift and actual migrate --plan; stop on any unexpected operation.',
            'Apply only the reviewed migrations while requests remain paused, then activate code.',
            'Verify HTTPS, auth, private downloads and normal ingestion; restore prior writer states.',
            'Rollback code/configuration with additive schema/new writes retained; never routinely restore old data.',
        ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--previous', required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--expected-migration', action='append', default=[])
    args = parser.parse_args()
    try:
        plan = inspect_release(args.repo.resolve(), args.revision, args.previous, args.expected_migration)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(2, 'STOP: '+(str(error) if isinstance(error, ValueError) else 'Release preflight could not complete.')+'\n')
    print(json.dumps(plan, indent=2))


if __name__ == '__main__':
    main()
