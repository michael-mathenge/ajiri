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
    if owner is None or not owner.is_active:
        raise ValueError('An active owner is required.')
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
        values['search_revision'] = target.revision
        values['window_end'] = target.next_email_at
        suffix = f'{target.pk}:{target.revision}:{target.next_email_at.isoformat()}'
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
        return DeliveryTask.objects.filter(pk=identity).values_list('state', flat=True).first() or 'missing'
    # A fast worker may already have claimed/completed it; never overwrite that state.
    DeliveryTask.objects.filter(pk=identity, state='publishing').update(state='published', updated_at=timezone.now())
    return DeliveryTask.objects.filter(pk=identity).values_list('state', flat=True).first() or 'missing'


def _run(task):
    if task.owner is None or not task.owner.is_active:
        return 'ineligible'
    if task.kind == 'application':
        from .application_dispatch import dispatch
        if task.authorization is None or task.authorization.owner_id != task.owner_id:
            return 'ineligible'
        return dispatch(task.owner, task.authorization).state
    if task.kind == 'alert':
        from .general_alert_email import deliver
        from .models import DeliveryAttempt
        if task.notification is None or task.notification.user_id != task.owner_id:
            return 'ineligible'
        previous = DeliveryAttempt.objects.filter(notification_id=task.notification_id).order_by('-created_at').first()
        return previous.state if previous else deliver(task.notification_id)
    if task.kind == 'saved_search':
        from .general_saved_search_email import deliver_batch, enabled as mail_enabled
        if (task.search is None or task.search.owner_id != task.owner_id
                or task.search.revision != task.search_revision or task.window_end is None):
            return 'ineligible'
        rows = task.search.matches.filter(channel='email', revision=task.search_revision,
                                         window_end=task.window_end)
        if rows.filter(email_attempt__state__in=['unknown', 'reserved']).exists():
            return 'unknown'
        if not mail_enabled():
            if rows.exists() and not rows.filter(email_attempt__isnull=True).exists():
                return 'definite_failure' if rows.filter(email_attempt__state='definite_failure').exists() else 'complete'
            return 'disabled'
        result = deliver_batch(task.search_id, at=task.window_end, window_end=task.window_end)
        outcomes = result['results']
        if (any(state in ('unknown', 'reserved') for state in outcomes)
                or rows.filter(email_attempt__state__in=['unknown', 'reserved']).exists()):
            return 'unknown'
        if 'definite_failure' in outcomes:
            return 'definite_failure'
        return 'ineligible' if rows.filter(email_attempt__isnull=True).exists() else 'complete'
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
        DeliveryTask.objects.filter(pk=identity, state='running', lease_until__lte=now, attempts__gte=3).update(
            state='dead', last_error='lease_exhausted', lease_token=None, lease_until=None, updated_at=now)
        eligible = DeliveryTask.objects.filter(pk=identity, attempts__lt=3).filter(Q(state__in=states)
            | Q(state='running', lease_until__lte=now))
        if eligible.update(state='running', lease_token=token, lease_until=now+timedelta(minutes=3),
                attempts=F('attempts')+1, updated_at=now) != 1:
            return DeliveryTask.objects.filter(pk=identity).values_list('state', flat=True).first() or 'missing'
        task = DeliveryTask.objects.select_related('owner', 'authorization', 'notification', 'search').get(pk=identity)
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
    from .delivery_batches import validate_limit
    validate_limit(limit)
    if not enabled():
        return 0
    identities = list(DeliveryTask.objects.filter(state='running', lease_until__lte=timezone.now())
        .order_by('lease_until').values_list('pk', flat=True)[:limit])
    for identity in identities:
        execute(identity)  # Same immutable target; existing receipts reconcile, never repeat provider I/O.
    return len(identities)
