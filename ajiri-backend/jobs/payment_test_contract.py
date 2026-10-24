"""Offline synthetic payment lab. No HTTP, Django models, credentials or live routes.

This is deliberately not a production payment service or a Daraja wire adapter.
see docs/CONCEPTS.md#synthetic-payment-reconciliation
"""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from threading import RLock
from uuid import UUID, uuid4


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class Checkout:
    id: UUID
    owner: UUID
    decision: UUID
    amount: int
    currency: str = 'KES'
    state: str = 'pending'
    provider_reference: str = ''
    revision: int = 0
    expires_at: datetime | None = None


@dataclass(frozen=True)
class SyntheticStatus:
    checkout_id: UUID
    owner: UUID
    amount: int
    currency: str
    state: str
    revision: int
    receipt: str = ''


class SyntheticGateway:
    """In-memory stand-in only. A callback is not this authoritative query."""
    def __init__(self):
        self.starts = []
        self.statuses = {}
        self.timeout = False

    def initiate(self, checkout):
        self.starts.append(checkout.id)
        if self.timeout:
            raise TimeoutError('Synthetic unknown handoff')
        return 'synthetic-' + checkout.id.hex

    def query(self, checkout):
        return self.statuses.get(checkout.id)


class SyntheticCheckoutLab:
    """Reconciliation/entitlement contract with injected, memory-only fixtures.

    Test catalogue and 30-day entitlement are examples, not commercial decisions.
    RLock models one atomic repository boundary, not distributed durability.
    """
    def __init__(self, gateway):
        if type(gateway) is not SyntheticGateway:
            raise ContractError('Only the offline synthetic gateway is supported.')
        self.gateway = gateway
        self._rows = {}
        self._decisions = {}
        self._receipts = {}
        self._lock = RLock()
        self.fail_write = False

    def _owned(self, owner, checkout_id):
        row = self._rows.get(checkout_id)
        if not isinstance(owner, UUID) or row is None or row.owner != owner:
            raise ContractError('Checkout unavailable.')
        return row

    def start(self, owner, decision, plan='synthetic-month'):
        if not isinstance(owner, UUID) or not isinstance(decision, UUID):
            raise ContractError('Synthetic owner and decision UUIDs are required.')
        if plan != 'synthetic-month':
            raise ContractError('Unknown synthetic plan.')
        with self._lock:
            key = (owner, decision)
            if key in self._decisions:
                return self._rows[self._decisions[key]]
            row = Checkout(uuid4(), owner, decision, amount=100)
            # Persist identity before handoff; an interrupted response cannot start again.
            self._rows[row.id] = row
            self._decisions[key] = row.id
            try:
                reference = self.gateway.initiate(row)
                row = replace(row, provider_reference=reference)
            except TimeoutError:
                row = replace(row, state='unknown')
            self._rows[row.id] = row
            return row

    def get(self, owner, checkout_id):
        with self._lock:
            return self._owned(owner, checkout_id)

    def callback_hint(self, payload):
        # Untrusted input has no authority to create a checkout or entitlement.
        return False

    def reconcile(self, owner, checkout_id, *, now):
        if now.tzinfo is None or now.utcoffset() is None:
            raise ContractError('Use an aware reconciliation time.')
        with self._lock:
            row = self._owned(owner, checkout_id)
            status = self.gateway.query(row)
            if status is None:
                return row
            if (type(status) is not SyntheticStatus or status.checkout_id != row.id
                    or status.owner != row.owner or type(status.amount) is not int
                    or status.amount != row.amount or status.currency != row.currency
                    or type(status.revision) is not int or status.revision < 1
                    or status.state not in ('pending', 'unknown', 'success', 'failed', 'cancelled', 'refunded')):
                raise ContractError('Synthetic authoritative status does not match checkout.')
            if status.revision <= row.revision:
                return row
            if row.state == 'refunded' and status.state != 'refunded':
                raise ContractError('A refund cannot be undone by another status.')
            if status.state == 'success':
                if not status.receipt or not status.receipt.startswith('synthetic-') or len(status.receipt) > 100:
                    raise ContractError('A bounded synthetic receipt is required.')
                prior = self._receipts.get(status.receipt)
                if prior is not None and prior != row.id:
                    raise ContractError('Receipt belongs to another checkout.')
            # Never extend a term just because a successful query is replayed.
            expiry = row.expires_at
            if status.state == 'success' and expiry is None:
                expiry = now + timedelta(days=30)
            updated = replace(row, state=status.state, revision=status.revision, expires_at=expiry)
            if self.fail_write:
                raise ContractError('Synthetic interrupted receipt write; no entitlement committed.')
            self._rows[row.id] = updated
            if status.state == 'success':
                self._receipts[status.receipt] = row.id
            return updated

    def capabilities(self, owner, checkout_id, *, now):
        if now.tzinfo is None or now.utcoffset() is None:
            raise ContractError('Use an aware eligibility time.')
        with self._lock:
            row = self._owned(owner, checkout_id)
            premium = bool(row.state == 'success' and row.expires_at and now < row.expires_at)
            return {'tier': 'synthetic-test' if premium else 'free',
                    'browse_jobs': True, 'apply': True, 'download_existing_documents': True,
                    'synthetic_paid_capability': premium}
