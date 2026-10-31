"""Durable minimal outbox, leases and receipt-preserving worker execution.

see docs/CONCEPTS.md#durable-delivery-queue
"""
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from .models import ApplicationSendAuthorization, DeliveryTask, Notification, SavedSearch


def enabled():
    return getattr(settings, 'DELIVERY_QUEUE_ENABLED', False) is True


def enqueue(kind, identity=None, *, owner=None):
    if not enabled():
        raise ValueError('Delivery queue is disabled.')
    values = {'kind': kind, 'owner': owner}
    if kind == 'application':
        target = ApplicationSendAuthorization.objects.get(pk=identity, owner=owner)
        values['authorization'] = target
        suffix = str(target.pk)
    elif kind == 'alert':
        target = Notification.objects.get(pk=identity, user=owner)
        values['notification'] = target
        suffix = str(target.pk)
    elif kind == 'saved_search':
        target = SavedSearch.objects.get(pk=identity, owner=owner)
        if target.email_frequency == 'off' or target.next_email_at is None or target.next_email_at > timezone.now():
            raise ValueError('Saved-search window is not due.')
        values['search'] = target
        suffix = f'{target.pk}:{target.next_email_at.isoformat() if target.next_email_at else "off"}'
    elif kind == 'matching' and owner is None:
        suffix = timezone.now().replace(minute=0, second=0, microsecond=0).isoformat()
    else:
        raise ValueError('Unsupported queue target.')
    key = uuid.uuid5(uuid.NAMESPACE_URL, f'ajiri-queue:{kind}:{suffix}')
    return DeliveryTask.objects.get_or_create(dedupe_key=key, defaults=values)[0]


def publish(identity):
    if not enabled():
        return 'disabled'
    if DeliveryTask.objects.filter(pk=identity, state='pending').update(state='publishing', updated_at=timezone.now()) != 1:
        return 'unchanged'
    try:
        from config.celery import app
        # Explicitly disable publisher retries; a timeout may already have queued it.
        with app.connection_for_write(connect_timeout=5) as connection:
            app.send_task('jobs.run_delivery_task', args=[str(identity)], task_id=str(identity),
                retry=False, ignore_result=True, serializer='json', connection=connection,
                queue='ajiri.delivery', delivery_mode=2)
    except Exception:
        DeliveryTask.objects.filter(pk=identity, state='publishing').update(
            state='publication_unknown', last_error='broker_unknown', updated_at=timezone.now())
        return 'publication_unknown'
    # A fast worker may already have claimed/completed it; never overwrite that state.
    DeliveryTask.objects.filter(pk=identity, state='publishing').update(state='published', updated_at=timezone.now())
    return 'published'


def _run(task):
    if task.kind != 'matching' and (task.owner is None or not task.owner.is_active):
        return 'ineligible'
    if task.kind == 'application':
        from .application_dispatch import dispatch
        if task.authorization is None or task.authorization.owner_id != task.owner_id:
            return 'ineligible'
        return dispatch(task.owner, task.authorization).state
    if task.kind == 'alert':
        from .general_alert_email import deliver
        if task.notification is None or task.notification.user_id != task.owner_id:
            return 'ineligible'
        return deliver(task.notification_id)
    if task.kind == 'saved_search':
        from .general_saved_search_email import deliver_due, enabled as mail_enabled
        if task.search is None or task.search.owner_id != task.owner_id:
            return 'ineligible'
        if not mail_enabled():
            return 'disabled'
        outcomes = deliver_due(task.search_id)
        if (any(state in ('unknown', 'reserved') for state in outcomes)
                or task.search.matches.filter(email_attempt__state__in=['unknown', 'reserved']).exists()):
            return 'unknown'
        if 'definite_failure' in outcomes:
            return 'definite_failure'
        pending = task.search.matches.filter(channel='email', email_attempt__isnull=True,
            revision=F('search__revision')).exists()
        return 'unavailable' if pending else 'complete'
    if task.kind == 'matching':
        from .matching import sweep_all_active_jobs_for_matches
        sweep_all_active_jobs_for_matches()
        return 'complete'
    return 'ineligible'


def execute(identity, *, resume_blocked=False):
    if not enabled():
        return 'disabled'
    try:
        identity = uuid.UUID(str(identity))
    except (ValueError, TypeError, AttributeError):
        return 'missing'
    now, token = timezone.now(), uuid.uuid4()
    states = ['pending', 'publishing', 'published', 'publication_unknown']
    if resume_blocked:
        # Explicit operator work can reconcile the same target or finish unattempted
        # rows; the shared ledger still forbids repeating every ambiguous handoff.
        states.extend(['blocked', 'needs_reconciliation'])
    with transaction.atomic():
        eligible = DeliveryTask.objects.filter(pk=identity).filter(Q(state__in=states)
            | Q(state='running', lease_until__lte=now))
        if eligible.update(state='running', lease_token=token, lease_until=now+timedelta(minutes=3),
                attempts=F('attempts')+1, updated_at=now) != 1:
            return DeliveryTask.objects.filter(pk=identity).values_list('state', flat=True).first() or 'missing'
        task = DeliveryTask.objects.select_related('owner', 'authorization', 'notification', 'search').get(pk=identity)
    if task.attempts > 3:
        state, error = 'dead', 'lease_exhausted'
    else:
        try:
            result = _run(task)
            state = {'accepted': 'succeeded', 'complete': 'succeeded', 'unknown': 'needs_reconciliation',
                'reserved': 'needs_reconciliation', 'definite_failure': 'dead', 'disabled': 'blocked',
                'ineligible': 'blocked'}.get(result, 'needs_reconciliation')
            error = '' if state == 'succeeded' else result[:32]
        except Exception:
            state, error = 'needs_reconciliation', 'unavailable'
        # BaseException (hard termination) deliberately leaves the durable lease.
    DeliveryTask.objects.filter(pk=identity, state='running', lease_token=token).update(
        state=state, last_error=error, lease_until=None, lease_token=None, updated_at=timezone.now())
    return DeliveryTask.objects.filter(pk=identity).values_list('state', flat=True).first() or 'missing'


def recover_leases(limit=50):
    if not enabled():
        return 0
    identities = list(DeliveryTask.objects.filter(state='running', lease_until__lte=timezone.now())
        .order_by('lease_until').values_list('pk', flat=True)[:limit])
    for identity in identities:
        execute(identity)  # Same immutable target; existing receipts reconcile, never repeat provider I/O.
    return len(identities)
