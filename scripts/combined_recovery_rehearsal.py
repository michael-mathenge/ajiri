"""Fresh-stack synthetic recovery; never a production cutover or hosted durability claim.

see docs/CONCEPTS.md#combined-recovery-rehearsal
"""
from datetime import timedelta
from io import StringIO
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from unittest.mock import patch


ROOT = Path('/tmp/combined-state')
PHASES = ('source', 'database', 'copy', 'ready', 'worker')


def require_lab(phase):
    if (phase not in (*PHASES, 'consume') or os.name != 'posix'
            or os.environ.get('AJIRI_COMBINED_REHEARSAL') != 'synthetic-only'
            or not Path('/app/manage.py').is_file()):
        raise RuntimeError('Use an explicit phase in the isolated synthetic combined-recovery lab.')


def setup(phase):
    require_lab(phase)  # Refuse ordinary execution before importing Django or opening IO.
    sys.path[:0] = ['/app', '/tmp', str(ROOT)]
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    from django.conf import settings
    settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres', 'USER': 'postgres', 'HOST': '127.0.0.1', 'PORT': '5432'}}
    settings.SECRET_KEY = 'public-synthetic-combined-recovery-only'
    settings.STORAGES = {'default': {'BACKEND': 's3_lab_backend.SyntheticS3Storage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
    settings.MEDIA_ROOT = ROOT/'unused-media'
    settings.ERASURE_LEDGER_DIR = ROOT/'ledger'
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    settings.ALLOWED_HOSTS = ['testserver']
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
    settings.EMAIL_DELIVERY_MODE = 'account_security'
    settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    settings.EMAIL_PLATFORM_FROM = 'platform@example.invalid'
    settings.ACCOUNT_LINK_ORIGIN = 'https://example.invalid'
    settings.BREVO_API_KEY = 'synthetic-only-not-a-credential'
    settings.BREVO_TIMEOUT_SECONDS = 10
    settings.ACCOUNT_EMAIL_TEST_CAPTURE = False
    writer = phase in ('source', 'consume') or (phase == 'worker' and (ROOT/'writer-ready').is_file())
    for key in ('DELIVERY_QUEUE_ENABLED', 'REAL_EMAIL_ENABLED', 'ACCOUNT_SECURITY_EMAIL_ENABLED',
            'APPLICATION_EMAIL_ENABLED', 'GENERAL_APPLICATION_EMAIL_ENABLED', 'GENERAL_ALERT_EMAIL_ENABLED',
            'SAVED_SEARCH_EMAIL_ENABLED', 'SAVED_SEARCHES_ENABLED', 'ALERT_EMAIL_ENABLED'):
        setattr(settings, key, writer)
    settings.JOB_FRESHNESS_ENFORCED = True
    settings.CERTIFICATE_EVIDENCE_ENABLED = False
    settings.MALWARE_SCANNING_ENABLED = False
    settings.PUBLIC_JOBS_ENABLED = False
    settings.EMPLOYER_POSTING_ENABLED = False
    modules = {label: 'combined_migrations.'+label for label in ('accounts', 'profiles', 'jobs')}
    if (ROOT/'combined_migrations').exists():
        settings.MIGRATION_MODULES = modules
    import django
    django.setup()
    from config.celery import app
    app.conf.update(broker_url='redis://127.0.0.1:6379/0', result_backend=None,
        task_ignore_result=True, task_serializer='json', accept_content=['json'],
        task_default_queue='ajiri.delivery', task_acks_late=True, worker_prefetch_multiplier=1,
        broker_transport_options={'visibility_timeout': 2, 'polling_interval': 0.2},
        beat_schedule={}, worker_send_task_events=False, task_send_sent_event=False)
    import current_outbox_rehearsal as outbox
    outbox.ROOT = ROOT
    outbox.setup = lambda restored=False: app
    return app, outbox


def digest(value):
    return hashlib.sha256(json.dumps(value, default=str, sort_keys=True).encode()).hexdigest()


def versions(storage, name):
    return storage.client.list_object_versions(Bucket=storage.bucket, Prefix=name).get('Versions', [])


def rows():
    from django.apps import apps
    return {m._meta.label_lower: digest(list(m._base_manager.order_by(m._meta.pk.name).values()))
        for m in apps.get_models(include_auto_created=True) if m._meta.managed and not m._meta.proxy}


def database_evidence():
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('SELECT app,name,applied FROM django_migrations ORDER BY app,name')
        recorder = digest(cursor.fetchall())
        cursor.execute('SELECT sequencename,last_value FROM pg_sequences WHERE schemaname=%s ORDER BY sequencename', ['public'])
        sequences = cursor.fetchall()
        # last_value does not distinguish a never-used sequence from is_called=False.
        states = []
        for name, _value in sequences:
            cursor.execute('SELECT last_value,is_called FROM '+connection.ops.quote_name(name))
            states.append((name, *cursor.fetchone()))
    return {'models': rows(), 'recorder': recorder, 'sequences': digest(states)}


class Workers:
    def __init__(self):
        self.processes, self.logs = [], []

    def start(self):
        if not (ROOT/'writer-ready').is_file():
            raise RuntimeError('Recovery prerequisites are not settled; worker refused.')
        log = (ROOT/f'worker-{uuid.uuid4().hex}.log').open('w')
        process = subprocess.Popen([sys.executable, __file__, 'consume'], stdout=log, stderr=log)
        self.processes.append(process); self.logs.append(log)
        return process

    def stop(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=5)
        for log in self.logs:
            log.close()


def succeeded(outbox, identity):
    from jobs.models import DeliveryTask
    def settled():
        task = DeliveryTask.objects.get(pk=identity)
        if task.state in ('blocked', 'dead', 'needs_reconciliation'):
            raise AssertionError('Synthetic worker settled as '+task.state+': '+task.last_error)
        return task.state == 'succeeded'
    outbox.until(settled)


def source(app, outbox):
    from django.conf import settings
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage, FileSystemStorage
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import connection
    from django.db.migrations import Migration, RunSQL
    from django.db.migrations.loader import MigrationLoader
    from django.db.migrations.writer import MigrationWriter
    from django.utils import timezone
    from jobs.delivery_queue import publish, recover_leases
    from jobs.models import DeliveryAttempt, DeliveryTask
    from jobs.postgres_search import SCHEMA_SQL
    from profiles.models import CVWorkspace
    from profiles.cv_validation import validate_content
    from profiles.certificates import put
    from profiles.upload_fixtures import pdf_bytes
    from profiles.private_copy import inventory, resume_copy
    from postgres_bootstrap_rehearsal import prepare_target_graph
    from accounts.erasure import read_journal
    from accounts.erasure_ledger import snapshot
    assert not ROOT.exists() and not connection.introspection.table_names()
    for name in ('calls', 'modes', 'objects'):
        (ROOT/name).mkdir(parents=True)
    # This package parent did not exist during Django imports; clear the negative finder cache.
    importlib.invalidate_caches()
    settings.MIGRATION_MODULES = prepare_target_graph(ROOT/'combined_migrations')
    call_command('migrate', interactive=False, verbosity=0)
    migration = Migration('9000_search_contract', 'jobs')
    migration.dependencies = [n for n in MigrationLoader(connection).graph.leaf_nodes() if n[0] == 'jobs']
    migration.operations = [RunSQL(SCHEMA_SQL)]
    writer = MigrationWriter(migration)
    path = Path(writer.path).resolve()
    assert path.is_relative_to(ROOT/'combined_migrations') and not path.exists()
    path.write_text(writer.as_string()); importlib.invalidate_caches()
    call_command('migrate', interactive=False, verbosity=0)
    (ROOT/'writer-ready').write_text('source')
    workers = Workers(); targets = []
    try:
        for kind in ('application', 'alert', 'saved_search'):
            task = outbox.fixture(kind); targets.append(str(task.pk))
            assert publish(task.pk) == 'published'
            workers.start()
            succeeded(outbox, task.pk)
            assert outbox.calls(task.pk) == 1
            workers.stop(); workers = Workers()
        owner = DeliveryTask.objects.get(pk=targets[0]).owner
        owner.profile.cv_file.save('synthetic.pdf', ContentFile(pdf_bytes()), save=True)
        cid = uuid.uuid4()
        CVWorkspace.objects.update_or_create(profile=owner.profile, defaults={'revision': 1,
            'content': validate_content({'schema_version': 1, 'contact': {'name': 'Synthetic'},
                'certifications': [{'id': str(cid), 'name': 'Synthetic', 'issuer': 'Synthetic'}]})})
        put(owner.profile, cid, 1, SimpleUploadedFile('synthetic.pdf', pdf_bytes(), content_type='application/pdf'))
        uncertain = outbox.fixture('alert'); targets.append(str(uncertain.pk))
        (ROOT/'modes'/str(uncertain.pk)).write_text('during')
        assert publish(uncertain.pk) == 'published'
        process = workers.start(); outbox.until(lambda: process.poll() is not None)
        assert process.returncode == 74 and outbox.calls(uncertain.pk) == 1
        DeliveryTask.objects.filter(pk=uncertain.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
        assert recover_leases() == 1
        assert DeliveryTask.objects.get(pk=uncertain.pk).state == 'needs_reconciliation'
        workers.stop(); workers = Workers()
        pending = outbox.fixture('alert')
        send = app.send_task
        def lost(*args, **kwargs):
            send(*args, **kwargs)
            raise TimeoutError('Synthetic lost publication confirmation')
        with patch.object(app, 'send_task', side_effect=lost) as transport:
            assert publish(pending.pk) == 'publication_unknown'
            assert publish(pending.pk) == 'unchanged' and transport.call_count == 1
        for identity in targets:
            app.send_task('jobs.run_delivery_task', args=[identity], queue='ajiri.delivery', retry=False)
        # Only this separately created synthetic owner is erased; no real request is inferred.
        erased = get_user_model().objects.create_user(email='erased-recovery@example.invalid')
        erased.profile.cv_file.save('erased.pdf', ContentFile(pdf_bytes()), save=True)
        erased_id, erased_key = erased.pk, erased.profile.cv_file.name
        default_storage.replace_synthetic(erased_key, pdf_bytes())
        request = str(uuid.uuid4())
        options = dict(user_id=erased_id, request_id=request, journal_dir=str(ROOT/'ledger'),
            verified_request=True, writers_paused=True, legal_hold_cleared=True,
            journal_copied=True, stdout=StringIO())
        call_command('erase_account_data', mode='prepare', **options)
        journal_path = ROOT/'ledger'/(request+'.signed')
        (ROOT/'prepared-journal.signed').write_bytes(journal_path.read_bytes())
        call_command('erase_account_data', mode='execute', **options)
        assert read_journal(journal_path)['state'] == 'complete'
        assert not get_user_model().objects.filter(pk=erased_id).exists()
        assert not versions(default_storage, erased_key)
        assert snapshot(ROOT/'ledger', ROOT/'ledger.zip') == 1
        copied = resume_copy(default_storage, FileSystemStorage(ROOT/'objects'), inventory(default_storage))
        assert len(copied['objects']) == 5
        expected = {'database': database_evidence(), 'targets': targets, 'uncertain': str(uncertain.pk),
            'pending': str(pending.pk), 'receipts': digest(list(DeliveryAttempt.objects.order_by('pk').values())),
            'receipt_ids': list(map(str, DeliveryAttempt.objects.order_by('pk').values_list('pk', flat=True))),
            'objects': copied['objects'], 'source_versions': inventory(default_storage),
            'erased_id': erased_id, 'erased_key': erased_key, 'owner_id': owner.pk,
            'journal_name': journal_path.name, 'journal_sha256': hashlib.sha256(journal_path.read_bytes()).hexdigest()}
        (ROOT/'expectations.json').write_text(json.dumps(expected, default=str, sort_keys=True))
        (ROOT/'writer-ready').unlink()
        print('AJIRI_COMBINED_SOURCE_READY='+json.dumps({'models': len(expected['database']['models']),
            'private_objects': 5, 'receipts': 4, 'pending_publication': 1, 'writers_stopped': True}))
    finally:
        workers.stop()


def assert_database(expected):
    assert database_evidence() == expected['database'], 'Database rows/recorder/sequences changed.'


def assert_ledger(expected):
    from accounts.erasure import read_journal
    from django.contrib.auth import get_user_model
    from django.core.files.storage import default_storage
    path = ROOT/'ledger'/expected['journal_name']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected['journal_sha256']
    journal = read_journal(path)
    assert journal['format'] == 2 and journal['state'] == 'complete'
    assert not get_user_model().objects.filter(pk=expected['erased_id']).exists()
    assert not versions(default_storage, expected['erased_key'])


def restored_references(origin, expected):
    from profiles.private_copy import inventory
    # A restored filesystem has new inodes/timestamps. Authorize new read identities
    # only after matching the independently retained exact key/size/hash inventory.
    current = inventory(origin)
    def content(rows):
        assert len({row['key'] for row in rows}) == len(rows), 'Duplicate inventory key.'
        return {row['key']: (row['size'], row['sha256']) for row in rows}
    assert content(current) == content(expected['objects'])
    return current


def restore(phase, app, outbox):
    from django.conf import settings
    from django.core.files.storage import default_storage, FileSystemStorage
    from django.contrib.auth import get_user_model
    from django.db.models import Sum
    from django.test import override_settings
    from rest_framework.test import APIClient
    from profiles.private_copy import resume_copy, CopyInterrupted, inventory
    from accounts.erasure_ledger import verify
    from jobs.models import DeliveryAttempt, DeliveryTask, DeliveryDailyBudget, ApplicationPackage
    from jobs.delivery_queue import execute, publish
    expected = json.loads((ROOT/'expectations.json').read_text())
    if phase in ('database', 'copy', 'ready'):
        assert_database(expected)
        assert not settings.DELIVERY_QUEUE_ENABLED and not (ROOT/'writer-ready').exists()
        try:
            Workers().start()
            raise AssertionError('Premature worker started.')
        except RuntimeError:
            pass
        assert execute(expected['targets'][0]) == 'disabled'
    if phase == 'database':
        assert not inventory(default_storage)
        print('AJIRI_COMBINED_BOUNDARY=database'); return 72
    origin = FileSystemStorage(ROOT/'objects')
    references = restored_references(origin, expected)
    if phase == 'copy':
        assert not inventory(default_storage)
        try:
            resume_copy(origin, default_storage, references, fail_after=1)
            raise AssertionError('Copy did not stop.')
        except CopyInterrupted:
            assert len(inventory(default_storage)) == 1
        print('AJIRI_COMBINED_BOUNDARY=copy'); return 73
    if phase == 'ready':
        copied = resume_copy(origin, default_storage, references)
        assert copied['reused'] == 1 and copied['copied'] == 4
        assert verify(ROOT/'ledger.zip', ROOT/'ledger') == 1
        assert_ledger(expected)
        journal_path = ROOT/'ledger'/expected['journal_name']
        complete_bytes = journal_path.read_bytes()
        try:
            journal_path.write_bytes((ROOT/'prepared-journal.signed').read_bytes())
            try:
                assert_ledger(expected)
                raise RuntimeError('Unresolved erasure journal was accepted.')
            except AssertionError:
                pass
        finally:
            journal_path.write_bytes(complete_bytes)
        assert_ledger(expected)
        from profiles.private_storage import read_exact, PrivateStorageError
        for reference in expected['source_versions']:
            try:
                read_exact(default_storage, reference)
                raise AssertionError('Old source version was accepted by the fresh store.')
            except PrivateStorageError:
                pass
        (ROOT/'restored-object-identities.json').write_text(json.dumps(copied['objects'], sort_keys=True))
        # Owner-only private routes are checked against fresh pathless objects.
        client = APIClient(); owner = get_user_model().objects.get(pk=expected['owner_id'])
        client.force_authenticate(owner)
        package = ApplicationPackage.objects.get(application__user=owner)
        urls = [('/api/profiles/me/cv/', owner.profile.cv_file.name),
            (f'/api/profiles/me/cv-versions/{package.cv_approval_id}/download/', package.cv_approval.document.name),
            (f'/api/jobs/applications/{package.application_id}/packages/{package.pk}/documents/cv/', package.cv_document.name),
            (f'/api/jobs/applications/{package.application_id}/packages/{package.pk}/documents/cover-letter/', package.letter_document.name)]
        expected_hashes = {row['key']: row['sha256'] for row in expected['objects']}
        for url, name in urls:
            response = client.get(url)
            assert response.status_code == 200
            payload = b''.join(response.streaming_content) if response.streaming else response.content
            assert hashlib.sha256(payload).hexdigest() == expected_hashes[name]
            response.close()
        client.force_authenticate(get_user_model().objects.exclude(pk=owner.pk).first())
        for url, _name in urls[1:]:
            assert client.get(url).status_code == 404
        assert_database(expected)
        (ROOT/'restore-ready').write_text('database+objects+ledger')
        print('AJIRI_COMBINED_BOUNDARY=ready'); return 74
    assert phase == 'worker' and (ROOT/'restore-ready').read_text() == 'database+objects+ledger'
    assert (ROOT/'source-stopped').read_text() == 'verified-by-host'
    assert_database(expected); assert_ledger(expected)
    copied = resume_copy(origin, default_storage, references)
    assert copied['reused'] == 5 and copied['copied'] == 0
    assert publish(expected['pending']) == 'disabled'
    (ROOT/'writer-ready').write_text('target')
    gates = {name: True for name in ('DELIVERY_QUEUE_ENABLED', 'REAL_EMAIL_ENABLED',
        'ACCOUNT_SECURITY_EMAIL_ENABLED', 'APPLICATION_EMAIL_ENABLED', 'GENERAL_APPLICATION_EMAIL_ENABLED',
        'GENERAL_ALERT_EMAIL_ENABLED', 'ALERT_EMAIL_ENABLED', 'SAVED_SEARCH_EMAIL_ENABLED', 'SAVED_SEARCHES_ENABLED')}
    workers = Workers()
    try:
        with override_settings(**gates):
            assert publish(expected['pending']) == 'unchanged'
            sentinel = outbox.fixture('alert'); assert publish(sentinel.pk) == 'published'
            workers.start()
            outbox.until(lambda: DeliveryTask.objects.get(pk=sentinel.pk).state == 'succeeded')
            outbox.until(lambda: DeliveryTask.objects.get(pk=expected['pending']).state == 'succeeded')
            from redis import Redis
            broker = Redis(host='127.0.0.1', port=6379, db=0)
            outbox.until(lambda: broker.llen('ajiri.delivery') == 0 and broker.hlen('unacked') == 0)
        assert all(outbox.calls(identity) == 1 for identity in expected['targets'])
        assert outbox.calls(expected['pending']) == 1 and outbox.calls(sentinel.pk) == 1
        assert outbox.calls() == 6 and DeliveryAttempt.objects.count() == 6
        assert digest(list(DeliveryAttempt.objects.filter(pk__in=expected['receipt_ids']).order_by('pk').values())) == expected['receipts']
        assert DeliveryTask.objects.get(pk=expected['uncertain']).state == 'needs_reconciliation'
        budgets = DeliveryDailyBudget.objects.filter(scope='global').aggregate(
            applications=Sum('application_reserved'), alerts=Sum('alert_reserved'))
        assert (budgets['applications'] or 0)+(budgets['alerts'] or 0) == 6
        assert_ledger(expected)
        print('AJIRI_COMBINED_RECOVERY_RESULT='+json.dumps({'synthetic_only': True,
            'fresh_database_objects_broker_worker': True, 'interrupted_restore_boundaries': 3,
            'private_objects': 5, 'completed_signed_erasure_ledger_preserved': True,
            'old_receipts_unchanged': 4, 'captured_handoffs': 6, 'shared_reservations': 6,
            'uncertain_handoff_still_requires_reconciliation': True,
            'blind_republications': 0, 'duplicate_handoffs': 0, 'real_provider_calls': 0,
            'physical_host_loss_verified': False, 'production_activation': False}, sort_keys=True))
    finally:
        workers.stop()
        (ROOT/'writer-ready').unlink(missing_ok=True)
    return 0


def main():
    phase = sys.argv[1] if len(sys.argv) == 2 else ''
    require_lab(phase)
    if phase == 'consume' and not (ROOT/'writer-ready').is_file():
        raise RuntimeError('Recovery prerequisites are not settled; worker refused.')
    app, outbox = setup(phase)
    if phase == 'consume':
        from jobs import delivery_queue
        original = delivery_queue._run
        def traced(task):
            try:
                return original(task)
            except Exception:
                import traceback
                traceback.print_exc()
                raise
        delivery_queue._run = traced
        outbox.worker(); return 0
    if phase == 'source':
        source(app, outbox); return 0
    return restore(phase, app, outbox)


if __name__ == '__main__':
    sys.exit(main())
