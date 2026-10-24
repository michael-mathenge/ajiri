"""Closed inline queue integration; no broker, worker registration or live caller."""
from dataclasses import dataclass
from threading import RLock
from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model

from .application_dispatch import dispatch
from .delivery_service import DeliveryError
from .models import ApplicationSendAuthorization


@dataclass(frozen=True)
class ApplicationEnvelope:
    owner_id: int
    authorization_id: UUID

    def __post_init__(self):
        if type(self.owner_id) is not int or self.owner_id <= 0 or not isinstance(self.authorization_id, UUID):
            raise ValueError('A positive owner ID and exact authorization UUID are required.')


def execute_application(envelope):
    # see docs/CONCEPTS.md#queue-reconciliation-contract
    if settings.DELIVERY_QUEUE_TEST_CAPTURE is not True:
        raise DeliveryError('The offline queue integration is disabled.')
    user = get_user_model().objects.filter(pk=envelope.owner_id, is_active=True).first()
    authorization = ApplicationSendAuthorization.objects.filter(
        pk=envelope.authorization_id, owner_id=envelope.owner_id).first()
    if user is None or authorization is None:
        raise DeliveryError('Queued authorization unavailable.')
    # Resolve current documents/permission and reuse the authorization's ledger key.
    # Never serialize a recipient, document bytes or a new retry identity into a job.
    return dispatch(user, authorization)


class InlineTestQueue:
    """Memory-only acknowledgement model, not durable or cross-process locking."""
    def __init__(self):
        self._states = {}
        self._lock = RLock()

    def enqueue(self, envelope):
        if type(envelope) is not ApplicationEnvelope:
            raise ValueError('Only a minimal application envelope is supported.')
        with self._lock:
            self._states.setdefault(envelope, 'pending')

    def execute(self, envelope, worker=execute_application, *, reconcile=False):
        with self._lock:
            if envelope not in self._states:
                raise DeliveryError('Envelope is not queued.')
            if self._states[envelope] == 'needs_reconciliation' and reconcile is not True:
                raise DeliveryError('Reconcile the existing receipt before another worker attempt.')
            try:
                result = worker(envelope)
            except Exception:
                self._states[envelope] = 'needs_reconciliation'
                raise
            self._states[envelope] = 'acknowledged'
            return result
