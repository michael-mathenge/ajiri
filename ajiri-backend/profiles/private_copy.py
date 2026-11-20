"""Explicit bounded private copying; no settings switch or automatic pruning.

see docs/CONCEPTS.md#private-storage-boundary
"""
from pathlib import Path
from .private_storage import (VersionedPrivateStorage, PrivateStorageError, inspect,
    key, read_exact, save_unique, validate)
from jobs.management.commands.backup_private_data import no_links

MAX_OBJECTS = 1000
MAX_TOTAL_BYTES = 200*1024*1024


class CopyInterrupted(OSError):
    pass


def inventory(storage):
    pending, visited, result = [''], set(), []
    while pending:
        prefix = pending.pop()
        if prefix in visited or len(visited) >= MAX_OBJECTS:
            raise PrivateStorageError('Private directory inventory exceeds review bounds.')
        visited.add(prefix)
        if not isinstance(storage, VersionedPrivateStorage):
            no_links(Path(storage.path(prefix)))
        directories, files = storage.listdir(prefix)
        for directory in directories:
            name = key(prefix+'/'+directory if prefix else directory)
            if len(name.split('/')) > 32:
                raise PrivateStorageError('Private directory depth exceeds review bounds.')
            pending.append(name)
        for filename in files:
            name = key(prefix+'/'+filename if prefix else filename)
            if filename == '.env' or filename.startswith('.env.') or filename == 'environment.backup':
                raise PrivateStorageError('Credential-file names are excluded from private copying.')
            result.append(inspect(storage, name))
            if len(result) > MAX_OBJECTS or sum(row['size'] for row in result) > MAX_TOTAL_BYTES:
                raise PrivateStorageError('Private object inventory exceeds review bounds.')
    return sorted(result, key=lambda row: row['key'])


def resume_copy(source, target, references, *, fail_after=None):
    if (source is target or not isinstance(references, list) or len(references) > MAX_OBJECTS
            or (fail_after is not None and (type(fail_after) is not int or not 1 <= fail_after <= MAX_OBJECTS))):
        raise PrivateStorageError('Independent private stores and valid bounded inputs are required.')
    if isinstance(source, VersionedPrivateStorage) and isinstance(target, VersionedPrivateStorage):
        if not source.private_namespace or source.private_namespace == target.private_namespace:
            raise PrivateStorageError('Independent private storage namespaces are required.')
    elif not isinstance(source, VersionedPrivateStorage) and not isinstance(target, VersionedPrivateStorage):
        a, b = Path(source.path('')).resolve(), Path(target.path('')).resolve()
        if a.is_relative_to(b) or b.is_relative_to(a):
            raise PrivateStorageError('Private source/destination roots must not overlap.')
    expected = {}
    for row in references:
        validate(row)
        if row['key'] in expected:
            raise PrivateStorageError('Duplicate source object identity.')
        expected[row['key']] = row
    if sum(row['size'] for row in references) > MAX_TOTAL_BYTES:
        raise PrivateStorageError('Private copy byte limit exceeded.')
    # Check every conflict before the first write; never overwrite or delete a destination.
    existing = {row['key']: row for row in inventory(target)}
    if any(name not in expected or (row['size'], row['sha256']) != (
            expected[name]['size'], expected[name]['sha256']) for name, row in existing.items()):
        raise PrivateStorageError('Destination differs; no private object was overwritten.')
    copied = reused = 0
    for name, reference in sorted(expected.items()):
        payload = read_exact(source, reference)
        if name in existing:
            read_exact(target, existing[name])
            reused += 1
            continue
        actual = save_unique(target, name, payload)
        if actual != name:
            raise PrivateStorageError('Destination changed during copy; reconcile the retained object.')
        read_exact(target, inspect(target, name))
        copied += 1
        if copied == fail_after:
            raise CopyInterrupted('Controlled private copy interruption.')
    final = inventory(target)
    if {r['key']: (r['size'], r['sha256']) for r in final} != {
            r['key']: (r['size'], r['sha256']) for r in references}:
        raise PrivateStorageError('Private copy verification failed.')
    return {'copied': copied, 'reused': reused, 'objects': final}
