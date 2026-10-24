"""Synthetic model-state/data portability check, NOT a production migration.

Runs only inside the dedicated no-host-mount rehearsal image and empty PostgreSQL.
No historical migration is modified or marked applied on PostgreSQL.
see docs/CONCEPTS.md#isolated-postgres-data-rehearsal
"""
import hashlib
from datetime import datetime, timezone as datetime_timezone
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import sys
import uuid


def fixture_json(records):
    """Keep full datetime precision; default Django JSON fixtures truncate it."""
    return json.dumps(records, default=lambda item: item.isoformat()
        if isinstance(item, datetime) else str(item))


def main():
    if (os.environ.get('AJIRI_STORAGE_REHEARSAL') != 'synthetic-only'
            or os.name != 'posix' or not Path('/app/manage.py').is_file()):
        raise SystemExit('Use the dedicated synthetic rehearsal container; never point this at production.')
    sys.path.insert(0, '/app')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    from django.conf import settings
    settings.DATABASES = {
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': '/tmp/source.sqlite3'},
        'rehearsal': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'postgres',
                      'USER': 'postgres', 'HOST': '127.0.0.1', 'PORT': '5432'},
    }
    settings.MEDIA_ROOT = '/tmp/source-media'
    settings.ALLOWED_HOSTS = ['testserver']
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.SECRET_KEY = 'synthetic-rehearsal-only-not-a-production-key'
    settings.REAL_EMAIL_ENABLED = False
    settings.APPLICATION_EMAIL_ENABLED = False
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
    assert not Path('/tmp/source.sqlite3').exists()
    import django
    django.setup()
    from django.apps import apps
    from django.contrib.auth import get_user_model
    from django.core import serializers, mail
    from django.core.files.base import ContentFile
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.core.management import call_command
    from django.db import connections, IntegrityError, transaction
    from django.test import override_settings
    from django.utils import timezone
    from rest_framework.test import APIClient
    from jobs.models import DeliveryAttempt, DeliveryDailyBudget
    from jobs.pilot_test_helpers import pilot_settings, prepared_pilot
    from jobs.send_authorization import authorize, plan_response
    from profiles.models import Skill
    from profiles.upload_fixtures import pdf_bytes
    from profiles.upload_validation import validate_cv_upload

    call_command('migrate', database='default', interactive=False, verbosity=0)
    User = get_user_model()
    owner = User.objects.create_user(email='storage-owner@example.invalid', full_name='Synthetic Applicant')
    other = User.objects.create_user(email='storage-other@example.invalid')
    profile = owner.profile
    profile.email_verified_at = timezone.now()
    profile.verified_email = owner.email
    profile.save()
    skills = [Skill.objects.create(name=name) for name in ('Synthetic Python', 'Synthetic delivery')]
    profile.skills.add(*skills)
    upload = validate_cv_upload(SimpleUploadedFile('synthetic.pdf', pdf_bytes()))
    profile.cv_file.save(upload.name, ContentFile(upload.read()), save=True)
    policy = pilot_settings(owner)
    policy.update(APPLICATION_EMAIL_ENABLED=False, APPLICATION_PILOT_PREPARATION_ENABLED=True)
    with override_settings(**policy):
        app, package = prepared_pilot(owner)
        app.job.skills_required.add(*skills)
        plan = plan_response(owner, app)
        authorization = authorize(owner, app.pk, {'request_key': uuid.uuid4(), 'package_id': package.pk,
            'expected_revision': 1, 'plan_sha256': plan['plan_sha256'], 'authorization': True})[0]

    models = [model for model in apps.get_models(include_auto_created=True)
              if model._meta.managed and not model._meta.proxy]

    def canonical(alias):
        return {model._meta.label_lower: list(model._base_manager.using(alias).order_by(model._meta.pk.name).values())
                for model in models}

    def digest(value):
        def encoded(item):
            # Backends may return the same instant in different session timezones.
            if isinstance(item, datetime) and item.tzinfo is not None:
                return item.astimezone(datetime_timezone.utc).isoformat()
            return str(item)
        return hashlib.sha256(json.dumps(value, default=encoded, sort_keys=True).encode()).hexdigest()

    before = canonical('default')
    records = []
    for model in models:
        # Django's JSON encoder truncates datetimes to milliseconds. Preserve all
        # microseconds explicitly, including approval/authorization timestamps.
        records.extend(serializers.serialize('python', model._base_manager.using('default').all(),
            fields=[field.name for field in model._meta.local_fields]))
    fixture = Path('/tmp/synthetic-source.json')
    fixture.write_text(fixture_json(records), encoding='utf-8')
    target = connections['rehearsal']
    assert target.vendor == 'postgresql' and not target.introspection.table_names()
    # Current-model schema only. We deliberately do not run/fake the SQLite history.
    with target.schema_editor() as editor:
        for model in apps.get_models():
            if model._meta.managed and not model._meta.proxy:
                editor.create_model(model)
    call_command('loaddata', str(fixture), database='rehearsal', verbosity=0, stdout=StringIO())
    target.check_constraints()
    imported = canonical('rehearsal')
    differing = [label for label in before if digest(before[label]) != digest(imported[label])]
    assert not differing, 'Different model values: '+', '.join(differing)
    assert digest(before) == digest(canonical('default'))
    assert 'django_migrations' not in target.introspection.table_names()

    source_media = Path('/tmp/source-media')
    target_media = Path('/tmp/target-media')
    shutil.copytree(source_media, target_media)

    def file_hashes(root):
        files = [path for path in root.rglob('*') if path.is_file()]
        assert not any(path.is_symlink() for path in root.rglob('*'))
        return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}

    media_hashes = file_hashes(source_media)
    assert media_hashes == file_hashes(target_media)
    urls = [f'/api/profiles/me/cv-versions/{package.cv_approval_id}/download/',
            f'/api/jobs/applications/{app.pk}/packages/{package.pk}/documents/cv/',
            f'/api/jobs/applications/{app.pk}/packages/{package.pk}/documents/cover-letter/']

    def downloads(user):
        client = APIClient(); client.force_authenticate(user)
        values = []
        for url in urls:
            response = client.get(url)
            assert response.status_code == 200, response.status_code
            assert 'no-store' in response['Cache-Control']
            values.append(b''.join(response.streaming_content) if response.streaming else response.content)
            response.close()
        return values

    original_downloads = downloads(owner)

    class TargetRouter:
        def db_for_read(self, model, **hints):
            return 'rehearsal'

        db_for_write = db_for_read

    with override_settings(DATABASE_ROUTERS=[TargetRouter()], MEDIA_ROOT=str(target_media)):
        migrated_owner = User.objects.using('rehearsal').get(pk=owner.pk)
        assert downloads(migrated_owner) == original_downloads
        assert original_downloads[0] == original_downloads[1]
        client = APIClient(); client.force_authenticate(User.objects.using('rehearsal').get(pk=other.pk))
        assert all(client.get(url).status_code == 404 for url in urls)
        retained = type(authorization).objects.using('rehearsal').get(pk=authorization.pk)
        assert retained.plan_sha256 == authorization.plan_sha256
        assert not DeliveryAttempt.objects.using('rehearsal').exists()
        assert not DeliveryDailyBudget.objects.using('rehearsal').exists()

    # Constraint failures must roll back, and imported explicit IDs must reset sequences.
    try:
        with transaction.atomic(using='rehearsal'):
            type(profile).objects.using('rehearsal').create(user_id=99999999)
    except IntegrityError:
        pass
    else:
        raise AssertionError('Missing target FK enforcement.')
    next_user = User.objects.db_manager('rehearsal').create_user(email='storage-next@example.invalid')
    assert next_user.pk > max(owner.pk, other.pk)
    assert type(profile).objects.using('rehearsal').filter(user_id=next_user.pk).count() == 1
    assert digest(before) == digest(canonical('default'))
    assert not getattr(mail, 'outbox', [])
    print('AJIRI_STORAGE_REHEARSAL_RESULT='+json.dumps({
        'synthetic_only': True, 'model_count': len(models),
        'row_count': sum(len(rows) for rows in before.values()),
        'canonical_sha256': digest(before), 'media_files': len(media_hashes),
        'private_downloads_equal': True, 'cross_owner_denied': True,
        'foreign_keys_checked': True, 'sequence_and_signal_alias_checked': True,
        'historical_postgres_migrations_applied': False, 'production_cutover': False,
        'object_storage_verified': False, 'email_or_provider_calls': 0,
    }, sort_keys=True))


if __name__ == '__main__':
    main()
