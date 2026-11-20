"""Bounded private objects; no URLs and no unverified pathless backend fallback.

see docs/CONCEPTS.md#private-storage-boundary
"""
import hashlib
from pathlib import Path, PurePosixPath
import re

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.core.management.base import CommandError
from jobs.management.commands.backup_private_data import no_links

MAX_BYTES = 5*1024*1024


class PrivateStorageError(OSError):
    pass


class VersionedPrivateStorage(Storage):
    """Pathless implementations must read/delete exact immutable object versions."""
    private_namespace = ''
    def private_identity(self, name):
        raise NotImplementedError

    def private_read(self, identity, limit):
        raise NotImplementedError

    def private_delete(self, identity):
        raise NotImplementedError

    def url(self, name):
        raise PrivateStorageError('Private objects have no public download URL.')


def key(name):
    path = PurePosixPath(name) if isinstance(name, str) else None
    if (not name or path is None or path.is_absolute() or str(path) != name
            or any(part in ('..', '.', '') for part in name.split('/'))
            or '\\' in name or ':' in name or any(ord(c) < 32 for c in name)
            or len(name) > 512):
        raise PrivateStorageError('Unsafe private object reference.')
    return name


def validate(identity):
    if (not isinstance(identity, dict) or set(identity) != {'format', 'backend', 'key', 'version', 'size', 'sha256'}
            or identity['format'] != 1 or not isinstance(identity['backend'], str)
            or not 0 < len(identity['backend']) <= 256 or not isinstance(identity['version'], str)
            or not 0 < len(identity['version']) <= 512
            or type(identity['size']) is not int or not 0 < identity['size'] <= MAX_BYTES
            or not isinstance(identity['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', identity['sha256'])):
        raise PrivateStorageError('Invalid private object identity.')
    key(identity['key'])
    return identity


def local_path(storage, name):
    key(name)
    try:
        path = Path(storage.path(name))
    except (NotImplementedError, AttributeError):
        raise PrivateStorageError('Unreviewed pathless private storage.') from None
    try:
        no_links(path)
    except CommandError:
        raise PrivateStorageError('Private links and junctions are unsupported.') from None
    root = Path(storage.path('')).resolve()
    if not path.resolve().is_relative_to(root):
        raise PrivateStorageError('Private object escaped its storage root.')
    if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
        raise PrivateStorageError('Private links and special files are unsupported.')
    return path


def inspect(storage, name):
    key(name)
    if isinstance(storage, VersionedPrivateStorage):
        ref = validate(storage.private_identity(name))
        if (ref['key'] != name or ref['backend'] == 'filesystem'
                or ref['backend'] != storage.private_namespace):
            raise PrivateStorageError('Private storage identity mismatch.')
        return ref
    path = local_path(storage, name)
    before = path.stat()
    if not 0 < before.st_size <= MAX_BYTES:
        raise PrivateStorageError('Private object exceeds its bounded size.')
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES+1)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) or len(data) != before.st_size:
        raise PrivateStorageError('Private object changed during inspection.')
    return {'format': 1, 'backend': 'filesystem', 'key': name,
        'version': f'{before.st_dev}:{before.st_ino}:{before.st_mtime_ns}',
        'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def read_exact(storage, identity, *, limit=MAX_BYTES):
    ref = validate(identity)
    if type(limit) is not int or not 0 < limit <= MAX_BYTES or ref['size'] > limit:
        raise PrivateStorageError('Invalid private read bound.')
    if isinstance(storage, VersionedPrivateStorage):
        if storage.private_identity(ref['key']) != ref:
            raise PrivateStorageError('Private object version changed.')
        data = storage.private_read(ref, limit+1)
        if storage.private_identity(ref['key']) != ref:
            raise PrivateStorageError('Private object changed during read.')
    else:
        if inspect(storage, ref['key']) != ref:
            raise PrivateStorageError('Private object identity changed.')
        with local_path(storage, ref['key']).open('rb') as stream:
            data = stream.read(limit+1)
        if inspect(storage, ref['key']) != ref:
            raise PrivateStorageError('Private object changed during read.')
    if (not isinstance(data, bytes) or len(data) != ref['size']
            or hashlib.sha256(data).hexdigest() != ref['sha256']):
        raise PrivateStorageError('Private object integrity failed.')
    return data


def read_field(field, *, limit=MAX_BYTES, sha256=None, size=None):
    ref = inspect(field.storage, field.name)
    if (sha256 is not None and ref['sha256'] != sha256) or (size is not None and ref['size'] != size):
        raise PrivateStorageError('Private approved object does not match.')
    return read_exact(field.storage, ref, limit=limit)


def save_unique(storage, name, data, *, max_length=None):
    key(name)
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES:
        raise PrivateStorageError('Invalid private write bound.')
    # FileSystemStorage atomically chooses an unused name; pathless implementations
    # must implement conditional creation, never overwrite an existing object.
    if not isinstance(storage, VersionedPrivateStorage):
        local_path(storage, name)
        if getattr(storage, '_allow_overwrite', False):
            raise PrivateStorageError('Private writes require non-overwriting storage.')
    saved = storage.save(name, ContentFile(data), max_length=max_length)
    ref = inspect(storage, saved)
    if ref['size'] != len(data) or ref['sha256'] != hashlib.sha256(data).hexdigest():
        # Unknown write outcomes retain bytes for report-only reconciliation.
        raise PrivateStorageError('Private write outcome needs reconciliation.')
    read_exact(storage, ref)
    return saved


def save_field(field, filename, data):
    # Django's trusted filename generator can use Windows separators; normalize
    # that generated value only, without accepting backslashes in external keys.
    generated = field.field.generate_filename(field.instance, filename).replace('\\', '/')
    field.name = save_unique(field.storage, generated, data, max_length=field.field.max_length)
    field._committed = True


def delete_exact(storage, identity):
    ref = validate(identity)
    if isinstance(storage, VersionedPrivateStorage):
        if storage.private_namespace != ref['backend']:
            raise PrivateStorageError('Private storage namespace changed; deletion refused.')
        # The backend must permit only remaining captured immutable versions and
        # reject every replacement. This also makes partial version cleanup resumable.
        storage.private_delete(ref)
        return
    if not storage.exists(ref['key']):
        return  # Completed cleanup is idempotent; never invent a replacement.
    if inspect(storage, ref['key']) != ref:
        raise PrivateStorageError('Private object changed; deletion refused.')
    local_path(storage, ref['key']).unlink(missing_ok=True)


def cleanup_owned(storage, name):
    """Only for a fresh UUID staged by the current request, before pointer commit."""
    if storage.exists(key(name)):
        delete_exact(storage, inspect(storage, name))
