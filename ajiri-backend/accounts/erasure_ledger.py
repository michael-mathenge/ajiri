"""Private erasure ledger snapshots; credentials are never copied into recovery bundles."""
import hashlib
import json
from pathlib import Path
import re
import zipfile
from django.core import signing
from django.core.management.base import CommandError
from .erasure import journal_root, read_journal, SALT

LIMIT = 16 * 1024 * 1024
NAME = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.signed')


def snapshot(source, target):
    root = journal_root(source)
    payloads = {}
    total = 0
    for path in sorted(root.iterdir()):
        if path.is_symlink() or not path.is_file() or path.stat().st_nlink > 1 or not NAME.fullmatch(path.name):
            raise CommandError('Unexpected erasure ledger entry; backup refused.')
        data = read_journal(path)
        if path.stem != data['request_id'] or data['state'] == 'db_erased':
            raise CommandError('Erasure cleanup is unresolved; finish it before a routine backup.')
        value = path.read_bytes()
        if signing.loads(value.decode('utf-8'), salt=SALT) != data:
            raise CommandError('Erasure journal changed during snapshot; backup refused.')
        total += len(value)
        if len(payloads) >= 1000 or total > LIMIT:
            raise CommandError('Erasure ledger exceeds backup review limits.')
        payloads[path.name] = value
    manifest = {'format': 1, 'complete': True, 'sha256': {
        name: hashlib.sha256(value).hexdigest() for name, value in payloads.items()}}
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, value in payloads.items():
            archive.writestr(name, value)
        archive.writestr('manifest.json', json.dumps(manifest))
    Path(target).chmod(0o600)
    return len(payloads)


def verify(source, restore_to=None):
    # Independent off-server verification uses hashes; signature checking requires the live key.
    with zipfile.ZipFile(source) as archive:
        members = archive.infolist()
        names = [member.filename for member in members]
        if (len(names) != len(set(names)) or len(names) > 1001
                or sum(m.file_size for m in members) > LIMIT + 1024 * 1024
                or any(n != 'manifest.json' and not NAME.fullmatch(n) for n in names)):
            raise CommandError('Unsafe erasure ledger archive.')
        manifest = json.loads(archive.read('manifest.json'))
        if manifest.get('format') != 1 or manifest.get('complete') is not True:
            raise CommandError('Incomplete erasure ledger archive.')
        if set(names) != {'manifest.json', *manifest['sha256']}:
            raise CommandError('Erasure ledger member mismatch.')
        payloads = {}
        for name, expected in manifest['sha256'].items():
            value = archive.read(name)
            if hashlib.sha256(value).hexdigest() != expected:
                raise CommandError('Erasure ledger checksum mismatch.')
            payloads[name] = value
    if restore_to:
        target = Path(restore_to)
        target.mkdir(mode=0o700, exist_ok=False)
        for name, value in payloads.items():
            with (target/name).open('xb') as stream:
                (target/name).chmod(0o600)
                stream.write(value)
    return len(payloads)
