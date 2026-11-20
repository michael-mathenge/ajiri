"""Loopback Moto adapter only. Not a provider integration or production dependency."""
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path

from django.core.files.base import File
from profiles.private_storage import VersionedPrivateStorage, PrivateStorageError, key, MAX_BYTES


def require_lab():
    if (os.name != 'posix' or os.environ.get('AJIRI_PRIVATE_STORAGE_REHEARSAL') != 'synthetic-only'
            or not Path('/app/manage.py').is_file()):
        raise RuntimeError('Use only the isolated synthetic S3 emulator container.')


class SyntheticS3Storage(VersionedPrivateStorage):
    def __init__(self, bucket='ajiri-workflow-synthetic'):
        require_lab()
        if bucket not in ('ajiri-workflow-synthetic', 'ajiri-copy-synthetic'):
            raise RuntimeError('Only dedicated synthetic buckets are allowed.')
        import boto3
        from botocore.config import Config
        self.client = boto3.client('s3', endpoint_url='http://127.0.0.1:5000', region_name='us-east-1',
            aws_access_key_id='synthetic', aws_secret_access_key='synthetic',
            config=Config(retries={'total_max_attempts': 1}, connect_timeout=2, read_timeout=5))
        self.bucket = bucket
        self.private_namespace = 'synthetic-loopback-s3:'+bucket
        if bucket not in {row['Name'] for row in self.client.list_buckets()['Buckets']}:
            self.client.create_bucket(Bucket=bucket, ACL='private')
            self.client.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={'Status': 'Enabled'})

    def _save(self, name, content):
        key(name)
        data = content.read(MAX_BYTES+1)
        if not 0 < len(data) <= MAX_BYTES:
            raise PrivateStorageError('Synthetic private object exceeds bounds.')
        try:
            self.client.put_object(Bucket=self.bucket, Key=name, Body=data, ACL='private',
                IfNoneMatch='*', Metadata={'sha256': hashlib.sha256(data).hexdigest()})
        except Exception:
            raise PrivateStorageError('Synthetic object write needs reconciliation.') from None
        return name

    def exists(self, name):
        key(name)
        from botocore.exceptions import ClientError
        try:
            self.client.head_object(Bucket=self.bucket, Key=name)
            return True
        except ClientError as error:
            if error.response['ResponseMetadata']['HTTPStatusCode'] == 404:
                return False
            raise PrivateStorageError('Synthetic object state unavailable.') from None

    def size(self, name):
        return self.private_identity(name)['size']

    def _open(self, name, mode='rb'):
        if mode != 'rb':
            raise PrivateStorageError('Synthetic private objects are immutable.')
        reference = self.private_identity(name)
        return File(BytesIO(self.private_read(reference, MAX_BYTES+1)), name=name)

    def private_identity(self, name):
        if not self.exists(name):
            raise FileNotFoundError
        try:
            head = self.client.head_object(Bucket=self.bucket, Key=name)
            listing = self.client.list_object_versions(Bucket=self.bucket, Prefix=name, MaxKeys=100)
            versions = [row['VersionId'] for row in listing.get('Versions', []) if row['Key'] == name]
            if (listing.get('IsTruncated') or not 1 <= len(versions) <= 8
                    or any(row['Key'] == name for row in listing.get('DeleteMarkers', []))):
                raise PrivateStorageError('Synthetic version inventory needs review.')
            token = json.dumps([head['VersionId'], sorted(versions)], separators=(',', ':'))
            return {'format': 1, 'backend': self.private_namespace, 'key': name, 'version': token,
                'size': head['ContentLength'], 'sha256': head['Metadata']['sha256']}
        except Exception:
            raise PrivateStorageError('Synthetic object identity unavailable.') from None

    def private_read(self, reference, limit):
        if self.private_identity(reference['key']) != reference:
            raise PrivateStorageError('Synthetic private version changed.')
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=reference['key'],
                VersionId=json.loads(reference['version'])[0])
            with response['Body'] as body:
                return body.read(limit)
        except Exception:
            raise PrivateStorageError('Synthetic private read failed.') from None

    def private_delete(self, reference):
        # The signed identity binds the entire bounded version inventory. Removing
        # only the current version would resurrect retained private historical bytes.
        try:
            captured = set(json.loads(reference['version'])[1])
            listing = self.client.list_object_versions(Bucket=self.bucket, Prefix=reference['key'], MaxKeys=100)
            remaining = {row['VersionId'] for row in listing.get('Versions', []) if row['Key'] == reference['key']}
            if (reference['backend'] != self.private_namespace or listing.get('IsTruncated')
                    or not remaining <= captured
                    or any(row['Key'] == reference['key'] for row in listing.get('DeleteMarkers', []))):
                raise PrivateStorageError('Synthetic conditional deletion refused.')
            for version in sorted(remaining):
                self.client.delete_object(Bucket=self.bucket, Key=reference['key'], VersionId=version)
            if self.exists(reference['key']):
                raise PrivateStorageError('Synthetic concurrent replacement retained; reconcile cleanup.')
        except Exception:
            raise PrivateStorageError('Synthetic private cleanup needs reconciliation.') from None

    def listdir(self, path):
        prefix = key(path)+'/' if path else ''
        response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix, Delimiter='/', MaxKeys=1000)
        if response.get('IsTruncated'):
            raise PrivateStorageError('Synthetic listing exceeds review bounds.')
        return ([row['Prefix'][len(prefix):-1] for row in response.get('CommonPrefixes', [])],
            [row['Key'][len(prefix):] for row in response.get('Contents', [])])

    def replace_synthetic(self, name, data):
        require_lab()  # Controlled adversarial fixture, not a normal write operation.
        self.client.put_object(Bucket=self.bucket, Key=key(name), Body=data, ACL='private',
            Metadata={'sha256': hashlib.sha256(data).hexdigest()})
