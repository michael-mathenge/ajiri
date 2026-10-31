"""Verified private Storage copy with a durable, conservative write journal.

No runtime storage switch, deletion, credential discovery or provider selection.
see docs/CONCEPTS.md#verified-private-storage-copy
"""
import hashlib
import json
import os
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from django.core.files.storage import FileSystemStorage
from .management.commands.backup_private_data import no_links

MAX_FILE_BYTES = 20*1024*1024
MAX_TOTAL_BYTES = 512*1024*1024


class StorageCopyBlocked(Exception):
    pass


def _name(value):
    if (not isinstance(value, str) or not value or len(value.encode('utf-8')) > 1024
            or '\\' in value or ':' in value or any(ord(char) < 32 for char in value)
            or value.startswith('/') or any(part in ('', '.', '..') for part in value.split('/'))):
        raise StorageCopyBlocked('Unsafe private storage reference; no transfer.')
    parts = value.split('/')
    if parts[0] not in ('cvs', 'approved-cvs', 'application-packages', 'applications', 'quarantine') or any(
            part == '.env' or part.startswith('.env.') for part in parts):
        raise StorageCopyBlocked('Reference is outside the reviewed private document roots.')
    return str(PurePosixPath(value))


def _identity(storage):
    if isinstance(storage, FileSystemStorage):
        path = Path(storage.location)
        no_links(path)
        return str(path.resolve())
    identity = getattr(storage, 'ajiri_private_namespace_identity', '')
    if (not isinstance(identity, str) or not identity
            or getattr(storage, 'ajiri_single_attempt_writes', False) is not True):
        raise StorageCopyBlocked('Remote driver/private namespace and single-attempt writes require review.')
    return identity


def _digest(storage, name):
    if isinstance(storage, FileSystemStorage):
        path = Path(storage.path(name))
        no_links(path)
        if not path.is_file() or path.stat().st_nlink != 1:
            raise StorageCopyBlocked('Unsupported private file entry.')
    digest, size = hashlib.sha256(), 0
    with storage.open(name, 'rb') as stream:
        while chunk := stream.read(65536):
            size += len(chunk)
            if size > MAX_FILE_BYTES:
                raise StorageCopyBlocked('Private file exceeds bounded copy review limit.')
            digest.update(chunk)
    return {'size': size, 'sha256': digest.hexdigest()}


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _write(path, body):
    no_links(path)
    envelope = {'body': body, 'sha256': _hash(body)}
    temporary = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(envelope, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()  # Only this invocation's uncommitted UUID journal file.


@contextmanager
def _exclusive(journal):
    lock_path = journal.with_name(journal.name+'.lock')
    no_links(lock_path)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    locked = False
    try:
        if os.fstat(descriptor).st_size == 0:
            os.write(descriptor, b'0')
        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise StorageCopyBlocked('Another copy owns this journal; no concurrent handoff.') from None
        locked = True
        yield
    finally:
        if locked:
            if os.name == 'nt':
                import msvcrt
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def copy_private_storage(source, target, names, journal, *, writers_paused=False, target_private=False):
    if writers_paused is not True or target_private is not True:
        raise StorageCopyBlocked('Paused writers and an explicitly private/exclusive target are required.')
    journal = Path(journal).absolute()
    no_links(journal)
    with _exclusive(journal):
        return _copy_private_storage(source, target, names, journal,
            writers_paused=writers_paused, target_private=target_private)


def _copy_private_storage(source, target, names, journal, *, writers_paused=False, target_private=False):
    if writers_paused is not True or target_private is not True:
        raise StorageCopyBlocked('Paused writers and an explicitly private/exclusive target are required.')
    names = sorted({_name(name) for name in names})
    if len(names) > 10000:
        raise StorageCopyBlocked('Private inventory exceeds bounded review limit.')
    source_identity, target_identity = _identity(source), _identity(target)
    if source is target or source_identity == target_identity:
        raise StorageCopyBlocked('Source and target must be independent.')
    if isinstance(source, FileSystemStorage) and isinstance(target, FileSystemStorage):
        left, right = Path(source_identity), Path(target_identity)
        if left.is_relative_to(right) or right.is_relative_to(left):
            raise StorageCopyBlocked('Source/target trees must not overlap.')
    journal = Path(journal)
    no_links(journal)
    if not journal.parent.is_dir():
        raise StorageCopyBlocked('Use an existing private journal directory.')
    for storage in (source, target):
        if isinstance(storage, FileSystemStorage) and journal.resolve().is_relative_to(Path(storage.location).resolve()):
            raise StorageCopyBlocked('Keep the journal outside both data trees.')
    snapshot = {name: _digest(source, name) for name in names}
    if sum(row['size'] for row in snapshot.values()) > MAX_TOTAL_BYTES:
        raise StorageCopyBlocked('Snapshot exceeds bounded copy review limit.')
    identity = {'source': _hash(source_identity), 'target': _hash(target_identity), 'snapshot': snapshot}
    if journal.exists():
        try:
            if journal.stat().st_size > 64*1024*1024:
                raise ValueError
            envelope = json.loads(journal.read_text(encoding='utf-8'))
            body = envelope['body']
            if envelope['sha256'] != _hash(body) or body['identity'] != identity or body['format'] != 1:
                raise ValueError
            if set(body['entries']) != set(snapshot):
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise StorageCopyBlocked('Journal is corrupt or belongs to a different snapshot/namespace.') from None
    else:
        body = {'format': 1, 'identity': identity, 'entries': {name: 'pending' for name in names}, 'complete': False}
        _write(journal, body)
    reused, copied = 0, 0
    for name, expected in snapshot.items():
        if target.exists(name):
            if _digest(target, name) != expected:
                raise StorageCopyBlocked('Existing target bytes differ; preserve source, target and journal.')
            body['entries'][name] = 'verified'
            reused += 1
            _write(journal, body)
            continue
        if body['entries'][name] != 'pending':
            raise StorageCopyBlocked('An uncertain or disappeared target cannot be automatically written again.')
        body['entries'][name] = 'writing'
        _write(journal, body)  # Durable claim BEFORE any target write/handoff.
        try:
            with source.open(name, 'rb') as stream:
                returned = target.save(name, stream)
            if returned != name or _digest(target, name) != expected:
                raise StorageCopyBlocked('Exact target name/bytes were not verified; no cutover.')
        except Exception:
            body['entries'][name] = 'unknown'
            _write(journal, body)
            raise StorageCopyBlocked('Target write is unconfirmed. Preserve the journal; do not automatically retry.') from None
        body['entries'][name] = 'verified'
        copied += 1
        _write(journal, body)
    if {name: _digest(source, name) for name in names} != snapshot:
        raise StorageCopyBlocked('Source changed during copy; no completion or cutover.')
    body['complete'] = True
    _write(journal, body)
    return {'complete': True, 'files': len(names), 'copied': copied, 'reused': reused,
        'snapshot_sha256': _hash(identity), 'changed_source': False, 'cutover': False}
