"""Synthetic pathless backend; never selected by production settings."""
from io import BytesIO
import hashlib
import uuid
import os
from pathlib import Path
from django.core.files.base import File
from .private_storage import VersionedPrivateStorage, PrivateStorageError, key


class PathlessPrivateStorage(VersionedPrivateStorage):
    private_namespace = 'synthetic-pathless'
    objects = {}

    def _save(self, name, content):
        key(name)
        if name in self.objects:
            raise PrivateStorageError('Conditional creation failed.')
        data = content.read(5*1024*1024+1)
        if not 0 < len(data) <= 5*1024*1024:
            raise PrivateStorageError('Synthetic object exceeds bound.')
        self.objects[name] = (str(uuid.uuid4()), data)
        return name

    def _open(self, name, mode='rb'):
        if mode != 'rb':
            raise PrivateStorageError('Private objects are immutable.')
        return File(BytesIO(self.objects[name][1]), name=name)

    def exists(self, name):
        return key(name) in self.objects

    def size(self, name):
        return len(self.objects[key(name)][1])

    def listdir(self, path):
        prefix = key(path)+'/' if path else ''
        tails = [name[len(prefix):] for name in self.objects if name.startswith(prefix)]
        return (sorted({tail.split('/')[0] for tail in tails if '/' in tail}),
            sorted(tail for tail in tails if '/' not in tail))

    def private_identity(self, name):
        if not self.exists(name):
            raise FileNotFoundError
        version, data = self.objects[name]
        return {'format': 1, 'backend': 'synthetic-pathless', 'key': name,
            'version': version, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def private_read(self, identity, limit):
        if self.private_identity(identity['key']) != identity:
            raise PrivateStorageError('Synthetic object version changed.')
        return self.objects[identity['key']][1][:limit]

    def private_delete(self, identity):
        if not self.exists(identity['key']):
            return
        if self.private_identity(identity['key']) != identity:
            raise PrivateStorageError('Conditional deletion refused.')
        del self.objects[identity['key']]

    def replace_synthetic(self, name, data):
        self.objects[key(name)] = (str(uuid.uuid4()), data)


def workflow_storage():
    if os.environ.get('AJIRI_PRIVATE_STORAGE_REHEARSAL') == 'synthetic-only':
        if os.name != 'posix' or not Path('/app/manage.py').is_file():
            raise RuntimeError('S3 emulator workflow tests require the isolated container.')
        return {'BACKEND': 's3_lab_backend.SyntheticS3Storage'}
    return {'BACKEND': 'profiles.private_storage_test_helpers.PathlessPrivateStorage'}
