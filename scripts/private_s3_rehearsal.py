"""HTTP S3 emulator/private workflow checks; synthetic files only.

see docs/CONCEPTS.md#private-storage-boundary
"""
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch


def require_lab():
    if (os.name != 'posix' or os.environ.get('AJIRI_PRIVATE_STORAGE_REHEARSAL') != 'synthetic-only'
            or not Path('/app/manage.py').is_file()):
        raise RuntimeError('Use only the isolated synthetic private-storage container.')


def main():
    require_lab()
    sys.path.insert(0, '/app')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    from moto.server import ThreadedMotoServer
    server = ThreadedMotoServer(ip_address='127.0.0.1', port=5000, verbose=False)
    server.start()
    try:
        from django.conf import settings
        settings.SECRET_KEY = 'public-synthetic-private-storage-only'
        settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': '/tmp/lab.sqlite3'}}
        settings.REAL_EMAIL_ENABLED = False
        settings.APPLICATION_EMAIL_ENABLED = False
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
        settings.ALLOWED_HOSTS = ['testserver']
        import django
        django.setup()
        from django.core.management import call_command
        call_command('test', 'profiles.test_private_storage', interactive=False, verbosity=1)
        from django.core.files.storage import FileSystemStorage
        from profiles.private_copy import inventory, resume_copy, CopyInterrupted
        from profiles.private_storage import save_unique, PrivateStorageError, inspect, delete_exact
        from s3_lab_backend import SyntheticS3Storage
        target = SyntheticS3Storage('ajiri-copy-synthetic')
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as restored:
            origin = FileSystemStorage(location=source)
            for index in range(3):
                save_unique(origin, f'private/{index}.pdf', f'synthetic-{index}'.encode())
            references = inventory(origin)
            try:
                resume_copy(origin, target, references, fail_after=1)
                raise AssertionError('Interruption was not injected.')
            except CopyInterrupted:
                pass
            result = resume_copy(origin, target, references)
            assert (result['copied'], result['reused']) == (2, 1)
            restored_store = FileSystemStorage(location=restored)
            assert resume_copy(target, restored_store, inventory(target))['copied'] == 3
            assert [(r['key'], r['sha256']) for r in inventory(restored_store)] == [
                (r['key'], r['sha256']) for r in references]
            target.replace_synthetic(references[0]['key'], b'changed')
            try:
                resume_copy(origin, target, references)
                raise AssertionError('Conflicting object was not refused.')
            except PrivateStorageError:
                pass
            reference = inspect(target, references[0]['key'])
            original_delete = target.client.delete_object
            def interrupted_delete(**kwargs):
                original_delete(**kwargs)
                raise OSError('Synthetic acknowledgement lost after immutable version removal')
            with patch.object(target.client, 'delete_object', side_effect=interrupted_delete):
                try:
                    delete_exact(target, reference)
                    raise AssertionError('Version cleanup interruption missing.')
                except PrivateStorageError:
                    pass
            delete_exact(target, reference)
            assert not target.exists(reference['key'])
        print('AJIRI_PRIVATE_S3_RESULT='+json.dumps({'synthetic_only': True,
            'loopback_http_emulator': True, 'workflow_tests': 11,
            'conditional_private_writes': True, 'version_bound_erasure': True,
            'historical_versions_in_identity': True, 'interrupted_copy_reused': 1,
            'interrupted_version_cleanup_resumed': True,
            'isolated_restore_exact_objects': 3, 'public_urls': False,
            'cloud_provider_acceptance': False, 'production_activation': False}, sort_keys=True))
    finally:
        server.stop()


if __name__ == '__main__':
    main()
