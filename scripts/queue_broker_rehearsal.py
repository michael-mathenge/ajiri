"""Actual isolated Celery/Redis rehearsal; synthetic documents and captured IO only.

see docs/CONCEPTS.md#isolated-queue-broker-rehearsal
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from unittest.mock import patch


def require_lab():
    if (os.name != 'posix' or os.environ.get('AJIRI_QUEUE_REHEARSAL') != 'synthetic-only'
            or not Path('/app/manage.py').is_file()):
        raise RuntimeError('Use only the dedicated isolated synthetic queue container.')


def setup():
    require_lab()
    sys.path.insert(0, '/app')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    from django.conf import settings
    settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': '/tmp/queue.sqlite3'}}
    settings.MEDIA_ROOT = '/tmp/queue-media'
    settings.SECRET_KEY = 'public-synthetic-queue-rehearsal-only'
    settings.REAL_EMAIL_ENABLED = False
    settings.APPLICATION_EMAIL_ENABLED = False
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
    import django
    django.setup()


def make_app():
    require_lab()
    from celery import Celery
    app = Celery('ajiri_synthetic_queue', broker='redis://127.0.0.1:6379/0',
                 backend='redis://127.0.0.1:6379/1')
    app.conf.update(task_serializer='json', accept_content=['json'], result_serializer='json',
        task_acks_late=True, task_reject_on_worker_lost=True, worker_prefetch_multiplier=1,
        task_default_queue='ajiri-synthetic-only', result_expires=120,
        broker_transport_options={'visibility_timeout': 2},
        worker_send_task_events=False, task_send_sent_event=False)

    @app.task(name='ajiri.synthetic.exact_authorization')
    def execute(owner_id, authorization_id):
        from django.contrib.auth import get_user_model
        from django.test import override_settings
        from jobs.brevo_transport import BrevoTransport, Result
        from jobs.application_packages import PackageConflict
        from jobs.package_review import PackageUnavailable
        from jobs.delivery_service import DeliveryError
        from jobs.pilot_test_helpers import pilot_settings
        from jobs.queue_test_integration import ApplicationEnvelope, execute_application
        user = get_user_model().objects.get(pk=owner_id)

        def capture(_payload):
            with Path('/tmp/provider-calls').open('a') as stream:
                stream.write('synthetic-handoff\n')
                stream.flush()
                os.fsync(stream.fileno())
            return Result('accepted', '<synthetic-queue@example.invalid>')

        with override_settings(**pilot_settings(user), DELIVERY_QUEUE_TEST_CAPTURE=True):
            with patch.object(BrevoTransport, 'send', side_effect=capture):
                try:
                    receipt = execute_application(ApplicationEnvelope(owner_id, uuid.UUID(authorization_id)))
                except (DeliveryError, PackageConflict, PackageUnavailable):
                    return {'state': 'blocked'}
        # A hard process exit after the durable receipt, before Celery can ack.
        marker = Path('/tmp/crash-after-handoff')
        if marker.exists():
            marker.unlink()
            os._exit(73)
        return {'state': receipt.state, 'receipt': str(receipt.pk)}

    return app, execute


def until(predicate, timeout=35):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.2)
    raise AssertionError('Synthetic worker verification timed out.')


def main():
    setup()
    app, execute = make_app()
    if '--worker' in sys.argv:
        app.worker_main(['worker', '--pool=solo', '--concurrency=1', '--loglevel=WARNING',
            '--without-gossip', '--without-mingle', '--without-heartbeat'])
        return
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import connections
    from django.test import override_settings
    from django.utils import timezone
    from jobs.models import DeliveryAttempt, DeliveryDailyBudget
    from jobs.pilot_test_helpers import prepared_pilot, pilot_settings
    from jobs.send_authorization import authorize, plan_response, withdraw
    from profiles.models import CVApproval
    assert not Path('/tmp/queue.sqlite3').exists()
    call_command('migrate', interactive=False, verbosity=0)
    user = get_user_model().objects.create_user(email='queue-owner@example.invalid', full_name='Synthetic Applicant')
    profile = user.profile
    profile.email_verified_at = timezone.now(); profile.verified_email = user.email; profile.save()

    def fixture():
        existing = CVApproval.objects.filter(profile=profile).first()
        from contextlib import nullcontext
        with override_settings(**pilot_settings(user)):
            with patch('jobs.pilot_test_helpers.approved_cv', return_value=existing) if existing else nullcontext():
                application, package = prepared_pilot(user)
            plan = plan_response(user, application)
            authorization = authorize(user, application.pk, {'request_key': uuid.uuid4(),
                'package_id': package.pk, 'expected_revision': 1, 'plan_sha256': plan['plan_sha256'],
                'authorization': True})[0]
        return application, authorization

    application, authorization = fixture()
    # Broker carries only the existing owner's ID and exact authorization UUID.
    Path('/tmp/crash-after-handoff').touch()
    first = execute.apply_async(args=[user.pk, str(authorization.pk)])
    connections.close_all()
    log = Path('/tmp/worker.log').open('w')
    worker = None

    def start():
        return subprocess.Popen([sys.executable, __file__, '--worker'], stdout=log, stderr=log)

    try:
        worker = start()
        until(lambda: worker.poll() is not None)
        assert worker.returncode == 73
        assert DeliveryAttempt.objects.get(application=application).state == 'accepted'
        assert Path('/tmp/provider-calls').read_text().count('synthetic-handoff') == 1
        # Let the restarted worker recover its expired lease without operator IO.
        time.sleep(2.2)
        connections.close_all()
        worker = start()
        replay = first.get(timeout=35)
        duplicate = execute.apply_async(args=[user.pk, str(authorization.pk)]).get(timeout=20)
        assert replay == duplicate and replay['state'] == 'accepted'
        assert DeliveryAttempt.objects.filter(application=application).count() == 1
        assert DeliveryDailyBudget.objects.get(scope='global').application_reserved == 1
        assert Path('/tmp/provider-calls').read_text().count('synthetic-handoff') == 1
        other_application, revoked = fixture()
        with override_settings(**pilot_settings(user)):
            withdraw(user, other_application.pk, revoked.pk)
        blocked = execute.apply_async(args=[user.pk, str(revoked.pk)]).get(timeout=20)
        assert blocked == {'state': 'blocked'}
        assert not DeliveryAttempt.objects.filter(application=other_application).exists()
        assert Path('/tmp/provider-calls').read_text().count('synthetic-handoff') == 1
        print('AJIRI_QUEUE_REHEARSAL_RESULT='+json.dumps({'synthetic_only': True,
            'real_redis_broker': True, 'real_celery_worker': True, 'hard_worker_exit': 73,
            'explicit_expired_lease_restore': False, 'automatic_worker_recovery': True,
            'same_receipt_after_redelivery': True,
            'duplicate_handoffs': 0, 'captured_handoffs': 1, 'real_email_calls': 0,
            'withdrawal_rechecked': True, 'production_worker': False}, sort_keys=True))
    finally:
        if worker is not None and worker.poll() is None:
            worker.terminate()
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker.kill(); worker.wait(timeout=5)
        log.close()


if __name__ == '__main__':
    main()
