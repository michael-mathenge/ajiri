"""Real current-outbox workers with synthetic inputs and captured provider IO only.

see docs/CONCEPTS.md#current-outbox-rehearsal
"""
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid
from unittest.mock import patch


ROOT = Path('/tmp/current-outbox')


def require_lab():
    if (os.name != 'posix' or os.environ.get('AJIRI_QUEUE_REHEARSAL') != 'synthetic-only'
            or not Path('/app/manage.py').is_file()):
        raise RuntimeError('Use only the isolated synthetic current-outbox container.')
    host = os.environ.get('AJIRI_QUEUE_LAB_HOST', '127.0.0.1')
    if host not in ('127.0.0.1', 'broker'):
        raise RuntimeError('Only the isolated rehearsal broker is allowed.')


def setup(restored=False):
    require_lab()  # Refuse ordinary execution before importing Django or opening a connection.
    sys.path.insert(0, '/app')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    from django.conf import settings
    area = ROOT/('restored' if restored else 'state')
    settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(area/'db.sqlite3'), 'OPTIONS': {'timeout': 20}}}
    settings.MEDIA_ROOT = area/'media'
    settings.SECRET_KEY = 'public-synthetic-current-outbox-only'
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
    for key in ('DELIVERY_QUEUE_ENABLED', 'REAL_EMAIL_ENABLED', 'ACCOUNT_SECURITY_EMAIL_ENABLED',
            'APPLICATION_EMAIL_ENABLED', 'GENERAL_APPLICATION_EMAIL_ENABLED', 'GENERAL_ALERT_EMAIL_ENABLED',
            'SAVED_SEARCH_EMAIL_ENABLED', 'SAVED_SEARCHES_ENABLED', 'ALERT_EMAIL_ENABLED', 'JOB_FRESHNESS_ENFORCED'):
        setattr(settings, key, True)
    import django
    django.setup()
    from config.celery import app
    host = os.environ.get('AJIRI_QUEUE_LAB_HOST', '127.0.0.1')
    app.conf.update(broker_url=f'redis://{host}:6379/{2 if restored else 0}', result_backend=None,
        task_ignore_result=True, task_serializer='json', accept_content=['json'],
        task_default_queue='ajiri.delivery', task_acks_late=True, worker_prefetch_multiplier=1,
        broker_transport_options={'visibility_timeout': 2, 'polling_interval': 0.2},
        beat_schedule={}, worker_send_task_events=False, task_send_sent_event=False)
    from jobs.tasks import run_delivery_task
    assert run_delivery_task.name == 'jobs.run_delivery_task'
    return app


def until(predicate, timeout=45):
    end = time.monotonic()+timeout
    while time.monotonic() < end:
        result = predicate()
        if result:
            return result
        time.sleep(0.2)
    raise AssertionError('Current-outbox verification timed out.')


def calls(identity=None):
    paths = [ROOT/'calls'/str(identity)] if identity else list((ROOT/'calls').glob('*'))
    return sum(path.read_text().count('captured\n') for path in paths if path.exists())


def worker(restored=False):
    app = setup(restored)
    from jobs import delivery_queue
    from jobs.brevo_transport import BrevoTransport, Result
    original = delivery_queue._run
    active = None

    def consume_mode(task):
        marker = ROOT/'modes'/str(task.pk)
        if not marker.exists():
            return ''
        mode = marker.read_text()
        marker.unlink()  # One controlled crash only; redelivery uses the real adapter.
        return mode

    def capture(_self, _payload):
        assert all(row['email'].endswith('@example.invalid') for row in json.loads(_payload)['to'])
        with (ROOT/'calls'/str(active.pk)).open('a') as stream:
            stream.write('captured\n'); stream.flush(); os.fsync(stream.fileno())
        if active.lab_mode == 'during':
            os._exit(74)
        return Result('accepted', '<synthetic-current-outbox@example.invalid>')

    def execute(task):
        nonlocal active
        active = task
        task.lab_mode = consume_mode(task)
        if task.lab_mode == 'before':
            os._exit(72)
        if task.lab_mode == 'hold':
            (ROOT/'held').write_text('claimed')
            until(lambda: (ROOT/'release').exists())
        if task.lab_mode == 'disabled':
            from django.test import override_settings
            with override_settings(GENERAL_APPLICATION_EMAIL_ENABLED=False,
                    GENERAL_ALERT_EMAIL_ENABLED=False, SAVED_SEARCH_EMAIL_ENABLED=False):
                result = original(task)
        else:
            result = original(task)
        if task.lab_mode == 'after':
            os._exit(73)
        return result

    with patch.object(BrevoTransport, 'send', capture), patch.object(delivery_queue, '_run', execute):
        app.worker_main(['worker', '--pool=solo', '--concurrency=1', '--loglevel=WARNING',
            '--without-gossip', '--without-mingle', '--without-heartbeat'])


def fixture(kind):
    from django.contrib.auth import get_user_model
    from django.test import override_settings
    from django.utils import timezone
    from profiles.alert_consent import record_choice
    from jobs.delivery_queue import enqueue
    from jobs.models import Job, JobPublication, Notification, SavedSearch
    from jobs.saved_searches import reset_windows
    from jobs.test_delivery_service import DeliveryServiceTests
    user = get_user_model().objects.create_user(email=f'{uuid.uuid4().hex}@example.invalid')
    profile = user.profile
    profile.email_verified_at = timezone.now(); profile.verified_email = user.email; profile.save()
    record_choice(user, True, uuid.uuid4())
    start = timezone.now()-timedelta(days=2)
    profile.alert_consent_events.update(created_at=start-timedelta(minutes=1))
    if kind == 'application':
        helper = SimpleNamespace(user=user)
        helper.authorization = lambda app: DeliveryServiceTests.authorization(helper, app)
        with override_settings(JOB_FRESHNESS_ENFORCED=False):
            application = DeliveryServiceTests.application(helper)
        job = application.job
        identity = application.test_authorization.pk
    else:
        word = 'case'+uuid.uuid4().hex
        job = Job.objects.create(title=word, company_name='Synthetic',
            source_url=f'https://example.invalid/{uuid.uuid4().hex}', source_name='synthetic')
        Job.objects.filter(pk=job.pk).update(scraped_at=start+timedelta(minutes=1))
        if kind == 'alert':
            identity = Notification.objects.create(user=user, job=job, match_score=70, in_app=False).pk
        else:
            search = SavedSearch(owner=user, name='Synthetic', q=word, email_frequency='daily')
            reset_windows(search, start)
            search.save()
            identity = search.pk
    JobPublication.objects.create(job=job, origin='rss', status='published',
        confirmed_at=timezone.now(), closes_at=timezone.now()+timedelta(days=1))
    task = enqueue(kind, identity, owner=user)
    assert enqueue(kind, identity, owner=user).pk == task.pk
    return task


class Workers:
    def __init__(self):
        self.processes = []
        self.logs = []

    def start(self, restored=False):
        log = (ROOT/f'worker-{uuid.uuid4().hex}.log').open('w')
        process = subprocess.Popen([sys.executable, __file__, '--worker']+(['--restored'] if restored else []),
            stdout=log, stderr=log)
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


def verify_restored():
    app = setup(True)
    from jobs.delivery_queue import publish
    from jobs.models import DeliveryAttempt, DeliveryTask
    expected = json.loads((ROOT/'restore-expectations.json').read_text())
    assert DeliveryAttempt.objects.count() == expected['count']
    workers = Workers()
    try:
        workers.start(restored=True)
        for identity in expected['targets']:
            app.send_task('jobs.run_delivery_task', args=[identity], queue='ajiri.delivery',
                retry=False, ignore_result=True)
        sentinel = fixture('alert')
        assert publish(sentinel.pk) == 'published'
        until(lambda: DeliveryTask.objects.get(pk=sentinel.pk).state == 'succeeded')
        assert calls() == expected['count']+1
        assert DeliveryAttempt.objects.count() == expected['count']+1
    finally:
        workers.stop()


def main():
    app = setup()
    if ROOT.exists():
        raise RuntimeError('A fresh disposable lab filesystem is required.')
    for name in ('state/media', 'calls', 'modes'):
        (ROOT/name).mkdir(parents=True)
    from django.core.management import call_command
    from django.db import connections
    from django.test import override_settings
    from django.utils import timezone
    from jobs.delivery_queue import execute, publish, recover_leases
    from jobs.models import DeliveryAttempt, DeliveryDailyBudget, DeliveryTask
    call_command('migrate', interactive=False, verbosity=0)
    workers = Workers()
    targets = []

    def state(task):
        return DeliveryTask.objects.get(pk=task.pk).state

    def replay(task):
        app.send_task('jobs.run_delivery_task', args=[str(task.pk)], queue='ajiri.delivery',
            retry=False, ignore_result=True)

    try:
        for kind in ('application', 'alert', 'saved_search'):
            for mode in ('before', 'during', 'after'):
                task = fixture(kind); targets.append(task.pk)
                (ROOT/'modes'/str(task.pk)).write_text(mode)
                assert publish(task.pk) == 'published'
                connections.close_all()
                process = workers.start()
                until(lambda: process.poll() is not None)
                assert process.returncode == {'before': 72, 'during': 74, 'after': 73}[mode]
                assert state(task) == 'running'
                assert calls(task.pk) == (0 if mode == 'before' else 1)
                # Explicitly expire the application's three-minute lease in this bounded lab.
                DeliveryTask.objects.filter(pk=task.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
                connections.close_all()
                workers.start()
                replay(task)  # Duplicate broker delivery, same immutable target, no new authorization.
                expected = 'needs_reconciliation' if mode == 'during' else 'succeeded'
                until(lambda: state(task) == expected)
                assert calls(task.pk) == 1
                before = DeliveryAttempt.objects.count()
                assert execute(task.pk, resume_blocked=True) == expected
                assert DeliveryAttempt.objects.count() == before and calls(task.pk) == 1
                workers.stop(); workers = Workers()

        # Actual publication reached Redis before a simulated lost broker confirmation.
        task = fixture('alert'); targets.append(task.pk)
        original = app.send_task
        def lost_confirmation(*args, **kwargs):
            original(*args, **kwargs)
            raise TimeoutError('Synthetic lost confirmation')
        with patch.object(app, 'send_task', side_effect=lost_confirmation) as send:
            assert publish(task.pk) == 'publication_unknown'
            assert publish(task.pk) == 'unchanged' and send.call_count == 1
        workers.start(); until(lambda: state(task) == 'succeeded')
        assert calls(task.pk) == 1
        workers.stop(); workers = Workers()

        # Two separate workers compete for one live lease; only the holder may hand off.
        task = fixture('application'); targets.append(task.pk)
        (ROOT/'modes'/str(task.pk)).write_text('hold')
        assert publish(task.pk) == 'published'
        workers.start(); until(lambda: (ROOT/'held').exists())
        workers.start(); replay(task)
        assert execute(task.pk) == 'running' and calls(task.pk) == 0
        (ROOT/'release').touch(); until(lambda: state(task) == 'succeeded')
        assert calls(task.pk) == 1
        workers.stop(); workers = Workers()

        exhausted = fixture('alert')
        for _ in range(3):
            (ROOT/'modes'/str(exhausted.pk)).write_text('before')
            replay(exhausted); process = workers.start()
            until(lambda: process.poll() is not None); assert process.returncode == 72
            DeliveryTask.objects.filter(pk=exhausted.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
        assert recover_leases() == 1 and state(exhausted) == 'dead'
        assert DeliveryTask.objects.get(pk=exhausted.pk).attempts == 3 and calls(exhausted.pk) == 0
        with override_settings(DELIVERY_QUEUE_ENABLED=False):
            assert execute(exhausted.pk) == 'disabled' and publish(exhausted.pk) == 'disabled'

        # Re-read eligibility in a separate real worker, after immutable enqueue.
        from profiles.alert_consent import record_choice
        from jobs.models import ApplicationSendAuthorization, JobPublication, SavedSearch
        blockers = [('alert', 'consent'), ('alert', 'mailbox'), ('alert', 'expiry'),
            ('alert', 'owner'), ('saved_search', 'revision'), ('application', 'authorization'),
            ('application', 'withdrawn')]
        blockers += [(kind, 'disabled') for kind in ('application', 'alert', 'saved_search')]
        for kind, blocker in blockers:
            task = fixture(kind)
            if blocker == 'consent':
                record_choice(task.owner, False, uuid.uuid4())
            elif blocker == 'mailbox':
                task.owner.email = f'{uuid.uuid4().hex}@example.invalid'; task.owner.save(update_fields=['email'])
            elif blocker == 'expiry':
                JobPublication.objects.filter(job=task.notification.job).update(closes_at=timezone.now()-timedelta(seconds=1))
            elif blocker == 'owner':
                foreign = fixture('alert').owner
                DeliveryTask.objects.filter(pk=task.pk).update(owner=foreign)
            elif blocker == 'revision':
                SavedSearch.objects.filter(pk=task.search_id).update(revision=task.search_revision+1)
            elif blocker == 'authorization':
                ApplicationSendAuthorization.objects.filter(pk=task.authorization_id).update(
                    authorized_at=timezone.now()-timedelta(hours=2), expires_at=timezone.now()-timedelta(seconds=1))
            elif blocker == 'withdrawn':
                from jobs.send_authorization import withdraw
                withdraw(task.owner, task.authorization.application_id, task.authorization_id)
            else:
                (ROOT/'modes'/str(task.pk)).write_text('disabled')
            assert publish(task.pk) == 'published'
            expected = 'needs_reconciliation' if kind == 'application' else 'blocked'
            workers.start(); until(lambda: state(task) == expected)
            assert calls(task.pk) == 0
            workers.stop(); workers = Workers()
        assert DeliveryAttempt.objects.count() == calls() == len(targets)
        budget = DeliveryDailyBudget.objects.get(scope='global')
        assert budget.application_reserved+budget.alert_reserved == calls()

        # Restore a consistent synthetic copy into a fresh private root and broker database.
        connections.close_all()
        restored = ROOT/'restored'; restored.mkdir()
        with sqlite3.connect(ROOT/'state/db.sqlite3') as source, sqlite3.connect(restored/'db.sqlite3') as target:
            source.backup(target)
            assert target.execute('PRAGMA integrity_check').fetchone() == ('ok',)
            assert not target.execute('PRAGMA foreign_key_check').fetchall()
        shutil.copytree(ROOT/'state/media', restored/'media')
        def hashes(area):
            return {str(p.relative_to(area)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in area.rglob('*') if p.is_file()}
        assert hashes(ROOT/'state/media') == hashes(restored/'media')
        (ROOT/'restore-expectations.json').write_text(json.dumps(
            {'targets': list(map(str, targets)), 'count': len(targets)}))
        subprocess.run([sys.executable, __file__, '--verify-restored'], check=True, timeout=70)
        print('AJIRI_CURRENT_OUTBOX_RESULT='+json.dumps({'synthetic_only': True,
            'registered_current_task': True, 'target_kinds': 3, 'hard_crash_cases': 9,
            'duplicate_handoffs': 0, 'single_shared_reservations': True,
            'broker_confirmation_unknown_not_republished': True, 'separate_worker_lease_contention': True,
            'three_claim_dead_letter': True, 'isolated_database_media_restored': True,
            'current_eligibility_and_disabled_cases': len(blockers),
            'fresh_logical_broker_database': True, 'host_loss_recovery_verified': False,
            'real_email_calls': 0, 'production_activation': False}, sort_keys=True))
    finally:
        workers.stop()


if __name__ == '__main__':
    if '--worker' in sys.argv:
        worker('--restored' in sys.argv)
    elif '--verify-restored' in sys.argv:
        verify_restored()
    else:
        main()
