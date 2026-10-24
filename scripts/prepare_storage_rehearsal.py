"""Export only tracked backend code into a private-free Docker build context.

see docs/CONCEPTS.md#isolated-postgres-data-rehearsal
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile


def allowed_source(name):
    path = PurePosixPath(name)
    return (not path.is_absolute() and '..' not in path.parts and '\\' not in name
        and len(path.parts) > 1 and path.parts[0] == 'ajiri-backend'
        and path.name != '.env' and path.suffix.lower() not in
        ('.sqlite3', '.db', '.pem', '.key', '.p12', '.doc', '.docx', '.pdf'))


def prepare(root):
    root = root.resolve()
    names = subprocess.check_output(['git', 'ls-files', '-z', '--', 'ajiri-backend'], cwd=root).decode().split('\0')
    names = [name for name in names if name]
    if not names or not all(allowed_source(name) for name in names):
        raise ValueError('Build context must contain tracked backend source only, without private data.')
    area = root/'.verification'
    area.mkdir(exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix='storage-context-', dir=area))
    hashes = {}
    for name in names:
        source = root/name
        if source.is_symlink() or not source.is_file():
            raise ValueError('Only regular tracked source files are accepted.')
        relative = PurePosixPath(name).relative_to('ajiri-backend')
        destination = target/'backend'/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        hashes[str(relative)] = hashlib.sha256(source.read_bytes()).hexdigest()
    shutil.copy2(root/'scripts/storage_rehearsal.py', target/'rehearsal.py')
    shutil.copy2(root/'scripts/storage-rehearsal/Dockerfile', target/'Dockerfile')
    manifest = {'base_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip(),
                'backend_sha256': hashes, 'synthetic_only': True}
    (target/'source-manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    return target


if __name__ == '__main__':
    print(prepare(Path(__file__).resolve().parents[1]))
