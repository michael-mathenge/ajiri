"""Alternate target graph, native search and current synthetic data; no real cutover.

see docs/CONCEPTS.md#postgres-bootstrap-candidate
"""
from datetime import datetime, timedelta, timezone as dt_timezone
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import sys
import time
import uuid
from unittest.mock import patch


def require_lab():
    if (os.name != 'posix' or os.environ.get('AJIRI_STORAGE_REHEARSAL') != 'synthetic-only'
            or not Path('/app/manage.py').is_file()):
        raise RuntimeError('Use only the isolated synthetic PostgreSQL bootstrap container.')


def digest(value):
    def encode(item):
        if isinstance(item, datetime) and item.tzinfo is not None:
            return item.astimezone(dt_timezone.utc).isoformat()
        return str(item)
    return hashlib.sha256(json.dumps(value, default=encode, sort_keys=True).encode()).hexdigest()


def prepare_target_graph(root):
    """Generate only alternate modules in a new disposable root; no database IO."""
    from django.apps import apps
    from django.conf import settings
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.loader import MigrationLoader
    from django.db.migrations.state import ProjectState
    from django.db.migrations.writer import MigrationWriter
    from django.test import override_settings
    from config.paths import application_tree
    import importlib
    import re
    root = Path(root).resolve()
    if (root.exists() or not root.parent.is_dir() or not re.fullmatch('[A-Za-z_][A-Za-z_0-9]*', root.name)
            or root.is_relative_to(application_tree(settings.BASE_DIR))):
        raise RuntimeError('Use a new independent disposable migration package.')
    root.mkdir(); (root/'__init__.py').touch()
    modules = {}
    for label in ('accounts', 'profiles', 'jobs'):
        folder = root/label; folder.mkdir(); (folder/'__init__.py').touch()
        modules[label] = root.name+'.'+label
    sys.path.insert(0, str(root.parent))
    try:
        with override_settings(MIGRATION_MODULES=modules):
            loader = MigrationLoader(None, ignore_no_migrations=True)
            changes = MigrationAutodetector(loader.project_state(), ProjectState.from_apps(apps)).changes(
                graph=loader.graph, convert_apps=set(modules))
            if set(changes) != set(modules):
                raise RuntimeError('Unexpected bootstrap model-state changes require review.')
            for migrations in changes.values():
                for migration in migrations:
                    writer = MigrationWriter(migration)
                    destination = Path(writer.path).resolve()
                    if not destination.is_relative_to(root) or destination.exists():
                        raise RuntimeError('Bootstrap writer escaped its new disposable package.')
                    with destination.open('x', encoding='utf-8') as stream:
                        stream.write(writer.as_string())
            importlib.invalidate_caches()
            loader = MigrationLoader(None)
            if MigrationAutodetector(loader.project_state(), ProjectState.from_apps(apps)).changes(graph=loader.graph):
                raise RuntimeError('Generated bootstrap state differs from current models.')
    finally:
        sys.path.remove(str(root.parent))
    return modules


def main():
    require_lab()
    sys.path[:0] = ['/app', '/tmp']
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    from django.conf import settings
    settings.DATABASES = {
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': '/tmp/bootstrap-source.sqlite3'},
        'rehearsal': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'postgres',
            'USER': 'postgres', 'HOST': '127.0.0.1', 'PORT': '5432'},
    }
    settings.MEDIA_ROOT = '/tmp/bootstrap-source-media'
    settings.ALLOWED_HOSTS = ['testserver']
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.SECRET_KEY = 'public-synthetic-postgres-bootstrap-only'
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
    settings.REAL_EMAIL_ENABLED = False
    settings.APPLICATION_EMAIL_ENABLED = False
    import django
    django.setup()
    from django.apps import apps
    from django.contrib.auth import get_user_model
    from django.core import serializers
    from django.core.files.base import ContentFile
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.core.management import call_command
    from django.db import connections, IntegrityError, transaction, models as db_models
    from django.db.migrations import Migration, RunSQL, AddField
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.executor import MigrationExecutor
    from django.db.migrations.loader import MigrationLoader
    from django.db.migrations.state import ProjectState
    from django.db.migrations.writer import MigrationWriter
    from django.test import override_settings
    from django.utils import timezone
    from rest_framework.test import APIClient
    from jobs.models import Job, JobPublication, DeliveryAttempt, DeliveryDailyBudget
    from jobs.delivery_queue import enqueue
    from jobs.pilot_test_helpers import pilot_settings, prepared_pilot
    from jobs.send_authorization import authorize, plan_response
    from jobs.application_dispatch import dispatch
    from jobs.brevo_transport import BrevoTransport, Result
    from profiles.alert_consent import record_choice
    from profiles.certificates import put
    from profiles.cv_validation import validate_content
    from profiles.models import Skill, CVWorkspace
    from profiles.upload_fixtures import pdf_bytes
    from jobs.search import search_jobs
    from jobs.filters import JobFilter
    from jobs.freshness import eligible_jobs
    from jobs.postgres_search import SCHEMA_SQL
    from storage_helpers import fixture_json, resume_media_copy, file_hashes

    originals = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for label in ('accounts', 'profiles', 'jobs') for p in Path('/app', label, 'migrations').glob('*.py')}
    target = connections['rehearsal']
    assert target.vendor == 'postgresql' and not target.introspection.table_names()
    assert not Path('/tmp/bootstrap-source.sqlite3').exists()
    call_command('migrate', database='default', interactive=False, verbosity=0)
    User = get_user_model()
    owner = User.objects.create_user(email='bootstrap@example.invalid', full_name='Synthetic')
    other = User.objects.create_user(email='other-bootstrap@example.invalid')
    profile = owner.profile
    profile.email_verified_at = timezone.now(); profile.verified_email = owner.email; profile.save()
    skill = Skill.objects.create(name='Synthetic Python'); profile.skills.add(skill)
    record_choice(owner, True, uuid.uuid4())
    profile.cv_file.save('synthetic.pdf', ContentFile(pdf_bytes()), save=True)
    with override_settings(**pilot_settings(owner)):
        application, package = prepared_pilot(owner)
        plan = plan_response(owner, application)
        authorization = authorize(owner, application.pk, {'request_key': uuid.uuid4(), 'package_id': package.pk,
            'expected_revision': 1, 'plan_sha256': plan['plan_sha256'], 'authorization': True})[0]
    certificate_id = uuid.uuid4()
    CVWorkspace.objects.create(profile=profile, content=validate_content({'schema_version': 1,
        'contact': {'name': 'Synthetic'}, 'certifications': [
            {'id': str(certificate_id), 'name': 'Synthetic training', 'issuer': 'Synthetic'}]}))
    put(profile, certificate_id, 1, SimpleUploadedFile('synthetic.pdf', pdf_bytes(), content_type='application/pdf'))
    with override_settings(DELIVERY_QUEUE_ENABLED=True):
        task = enqueue('application', authorization.pk, owner=owner)
    with override_settings(**pilot_settings(owner)), patch.object(BrevoTransport, 'send',
            return_value=Result('accepted', '<synthetic-bootstrap@example.invalid>')) as transport:
        receipt = dispatch(owner, authorization)
        assert receipt.state == 'accepted' and transport.call_count == 1

    corpus = ['Python developer', 'Support officer', 'Café manager', 'Kiswahili coordinator',
        'C++ and C# engineer', 'SQL OR NOT analyst', 'v1.2 release manager', "O'Reilly editor",
        '工程 coordinator', 'Résumé reviewer', 'E\u0301cole manager', 'Fullwidth １２３ developer',
        'Æther Straße Łódź Cœur coordinator']
    search_ids = []
    for index, title in enumerate(corpus+['Python support position']*200):
        job = Job.objects.create(title=title, company_name='Synthetic', description='Python data science',
            requirements='Kiswahili', location='Nairobi' if index % 2 else 'Mombasa',
            source_url=f'https://example.invalid/bootstrap/{index}', source_name='synthetic')
        JobPublication.objects.create(job=job, origin='rss', status='published', confirmed_at=timezone.now(),
            closes_at=timezone.now()+timedelta(days=1))
        search_ids.append(job.pk)
    for mode in ('inactive', 'scam', 'expired'):
        job = Job.objects.create(title='Python hidden', company_name='Synthetic',
            is_active=mode != 'inactive', is_flagged_scam=mode == 'scam',
            source_url=f'https://example.invalid/hidden/{mode}', source_name='synthetic')
        JobPublication.objects.create(job=job, origin='rss', status='published', confirmed_at=timezone.now(),
            closes_at=timezone.now()+timedelta(days=-1 if mode == 'expired' else 1))
    tracked_models = [m for m in apps.get_models(include_auto_created=True) if m._meta.managed and not m._meta.proxy]
    def canonical(alias):
        return {m._meta.label_lower: list(m._base_manager.using(alias).order_by(m._meta.pk.name).values())
            for m in tracked_models}
    before = canonical('default')
    with connections['default'].cursor() as cursor:
        cursor.execute('SELECT app,name,applied FROM django_migrations ORDER BY app,name')
        source_migrations = digest(cursor.fetchall())
    records = []
    for model in tracked_models:
        records.extend(serializers.serialize('python', model._base_manager.using('default').all(),
            fields=[field.name for field in model._meta.local_fields]))
    fixture = Path('/tmp/bootstrap-source.json'); fixture.write_text(fixture_json(records))

    # Generate a new graph in the disposable container, never rewrite/copy fake
    # application markers into the original history or production's recorder.
    root = Path('/tmp/bootstrap_migrations')
    modules = prepare_target_graph(root)
    settings.MIGRATION_MODULES = modules
    loader = MigrationLoader(None)
    assert not MigrationAutodetector(loader.project_state(), ProjectState.from_apps(apps)).changes(graph=loader.graph)
    call_command('migrate', database='rehearsal', interactive=False, verbosity=0)
    executor = MigrationExecutor(target)
    assert not executor.migration_plan(executor.loader.graph.leaf_nodes())

    def add_migration(name, operations):
        loader = MigrationLoader(target)
        migration = Migration(name, 'jobs')
        migration.dependencies = [node for node in loader.graph.leaf_nodes() if node[0] == 'jobs']
        migration.operations = operations
        writer = MigrationWriter(migration)
        destination = Path(writer.path).resolve()
        assert destination.is_relative_to(root)
        with destination.open('x', encoding='utf-8') as stream:
            stream.write(writer.as_string())
        import importlib
        importlib.invalidate_caches()
        call_command('migrate', database='rehearsal', interactive=False, verbosity=0)
    add_migration('9000_search_contract', [RunSQL(SCHEMA_SQL)])
    with target.cursor() as cursor:
        names = ','.join(target.ops.quote_name(m._meta.db_table) for m in tracked_models)
        cursor.execute('TRUNCATE '+names+' RESTART IDENTITY CASCADE')

    original_save = db_models.Model.save_base
    writes = 0
    def interrupted_save(instance, *args, **kwargs):
        nonlocal writes
        result = original_save(instance, *args, **kwargs)
        if kwargs.get('using') == 'rehearsal':
            writes += 1
            if writes == 10:
                raise RuntimeError('SYNTHETIC_IMPORT_INTERRUPTED')
        return result
    try:
        with patch.object(db_models.Model, 'save_base', interrupted_save):
            call_command('loaddata', str(fixture), database='rehearsal', verbosity=0, stdout=StringIO())
    except RuntimeError as error:
        assert str(error) == 'SYNTHETIC_IMPORT_INTERRUPTED'
    else:
        raise AssertionError('Import interruption missing.')
    assert writes == 10 and all(not rows for rows in canonical('rehearsal').values())
    call_command('loaddata', str(fixture), database='rehearsal', verbosity=0, stdout=StringIO())
    target.check_constraints()
    assert digest(before) == digest(canonical('rehearsal')) == digest(canonical('default'))
    assert DeliveryAttempt.objects.using('rehearsal').get(pk=receipt.pk).idempotency_key == authorization.pk
    assert DeliveryDailyBudget.objects.using('rehearsal').get(scope='global').application_reserved == 1

    samples, rank_differences = [], 0
    queries = ['', '!!!', 'python', 'pyth', 'café', 'cafe man', 'C++', 'C#', 'SQL OR NOT',
        "'; DROP TABLE jobs_job;--", 'nair', 'Kiswah', '１２３', 'data science', '工程', 'v1.2', "O'Reilly", 'résumé', 'école',
        'Aether', 'Æther', 'straße', 'strasse', 'łódź', 'lodz', 'cœur', 'coeur']
    with override_settings(JOB_FRESHNESS_ENFORCED=True):
        for query in queries:
            orders = []
            for alias in ('default', 'rehearsal'):
                qs = JobFilter({'q': query}, queryset=eligible_jobs(Job.objects.using(alias).all())).qs
                start = time.monotonic(); order = list(qs.values_list('pk', flat=True)); elapsed = time.monotonic()-start
                assert order == list(qs.values_list('pk', flat=True))
                assert len(order) == len(set(order))
                orders.append(order)
                samples.append({'backend': alias, 'case': len(samples)//2, 'matches': len(order),
                    'elapsed_ms': round(elapsed*1000, 3)})
            assert set(orders[0]) == set(orders[1]), 'Search membership divergence in case '+str(queries.index(query))
            rank_differences += orders[0] != orders[1]
        for alias in ('default', 'rehearsal'):
            qs = JobFilter({'q': 'pyth', 'location': 'Nairobi'}, queryset=eligible_jobs(Job.objects.using(alias).all())).qs
            assert all(row.location == 'Nairobi' for row in qs)
            page1, page2 = list(qs.values_list('pk', flat=True)[:20]), list(qs.values_list('pk', flat=True)[20:40])
            assert page1 and page2 and not set(page1) & set(page2)
            with transaction.atomic(using=alias):
                Job.objects.using(alias).filter(pk=search_ids[0]).update(title='Uniqueupdatedtoken')
                assert list(search_jobs(Job.objects.using(alias).all(), 'Uniqueupdatedtoken').values_list('pk', flat=True)) == [search_ids[0]]
                Job.objects.using(alias).filter(pk=search_ids[0]).delete()
                assert not search_jobs(Job.objects.using(alias).all(), 'Uniqueupdatedtoken').exists()
                transaction.set_rollback(True, using=alias)

    source_media, copied_media = Path(settings.MEDIA_ROOT), Path('/tmp/bootstrap-target-media')
    try:
        resume_media_copy(source_media, copied_media, fail_after=1)
    except OSError:
        pass
    copied = resume_media_copy(source_media, copied_media)
    assert copied['reused'] == 1 and file_hashes(source_media) == file_hashes(copied_media)
    urls = [f'/api/profiles/me/cv-versions/{package.cv_approval_id}/download/',
        f'/api/jobs/applications/{application.pk}/packages/{package.pk}/documents/cv/']
    def downloads(user):
        client = APIClient(); client.force_authenticate(user)
        result = []
        for url in urls:
            response = client.get(url); assert response.status_code == 200
            assert 'no-store' in response['Cache-Control']
            result.append(b''.join(response.streaming_content) if response.streaming else response.content)
            response.close()
        return result
    original_documents = downloads(owner)
    class TargetRouter:
        def db_for_read(self, model, **hints): return 'rehearsal'
        db_for_write = db_for_read
    with override_settings(DATABASE_ROUTERS=[TargetRouter()], MEDIA_ROOT=str(copied_media)):
        assert downloads(User.objects.using('rehearsal').get(pk=owner.pk)) == original_documents
        client = APIClient(); client.force_authenticate(User.objects.using('rehearsal').get(pk=other.pk))
        assert all(client.get(url).status_code == 404 for url in urls)
    assert digest(before) == digest(canonical('default')) == digest(canonical('rehearsal'))
    add_migration('9001_forward_probe', [AddField('job', 'migration_probe', db_models.IntegerField(null=True))])
    with target.cursor() as cursor:
        cursor.execute('SELECT count(*) FROM jobs_job WHERE migration_probe IS NULL')
        assert cursor.fetchone()[0] == len(before['jobs.job'])
    executor = MigrationExecutor(target)
    executor.migrate([('jobs', '9000_search_contract')])
    assert digest(before) == digest(canonical('rehearsal'))
    try:
        with transaction.atomic(using='rehearsal'):
            type(profile).objects.using('rehearsal').create(user_id=99999999)
    except IntegrityError:
        pass
    else:
        raise AssertionError('Target FK enforcement missing.')
    next_user = User.objects.db_manager('rehearsal').create_user(email='next-bootstrap@example.invalid')
    assert next_user.pk > max(owner.pk, other.pk)
    assert type(profile).objects.using('rehearsal').filter(user_id=next_user.pk).count() == 1
    assert originals == {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in originals}
    with connections['default'].cursor() as cursor:
        cursor.execute('SELECT app,name,applied FROM django_migrations ORDER BY app,name')
        assert source_migrations == digest(cursor.fetchall())
    with target.cursor() as cursor:
        cursor.execute('SHOW server_version'); version = cursor.fetchone()[0]
    print('AJIRI_POSTGRES_BOOTSTRAP_RESULT='+json.dumps({'synthetic_only': True,
        'postgres_version': version, 'alternate_graph_migrated': True,
        'model_state_equivalent': True, 'source_history_unchanged': True,
        'model_count': len(tracked_models), 'row_count': sum(len(rows) for rows in before.values()),
        'certificate_and_outbox_retained': True, 'receipt_id_retained': True,
        'canonical_sha256': digest(before), 'search_cases': len(queries),
        'membership_divergences': 0, 'ranking_differences': rank_differences, 'search_samples': samples,
        'private_files': len(file_hashes(source_media)), 'private_downloads_equal': True,
        'cross_owner_denied': True, 'interrupted_import_rolled_back': True,
        'future_additive_migration_verified': True, 'sequence_and_fk_checked': True,
        'real_email_calls': 0, 'production_cutover': False}, sort_keys=True))


if __name__ == '__main__':
    main()
