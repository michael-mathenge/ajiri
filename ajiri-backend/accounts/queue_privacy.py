"""Owner privacy operations must retain uncertain delivery reconciliation."""
from django.core.management.base import CommandError
from django.db.models import Q
from jobs.models import DeliveryTask


def owned_tasks(user):
    # see docs/CONCEPTS.md#queue-account-privacy
    related = DeliveryTask.objects.filter(Q(owner=user) | Q(notification__user=user)
        | Q(search__owner=user) | Q(authorization__owner=user)
        | Q(authorization__application__user=user))
    if (related.exclude(owner=user).exists()
            or related.filter(notification__isnull=False).exclude(notification__user=user).exists()
            or related.filter(search__isnull=False).exclude(search__owner=user).exists()
            or related.filter(authorization__isnull=False).exclude(authorization__owner=user).exists()
            or related.filter(authorization__isnull=False).exclude(authorization__application__user=user).exists()):
        raise CommandError('Cross-owner queue reference; investigate before account privacy operations.')
    return DeliveryTask.objects.filter(owner=user)


def require_reconciled_tasks(user):
    if owned_tasks(user).exclude(state__in=('succeeded', 'dead')).exists():
        raise CommandError('Outstanding queued work requires reconciliation before account erasure.')
