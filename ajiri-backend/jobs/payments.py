"""Durable checkout claims; no callback, client label or Express result grants access.

see docs/CONCEPTS.md#durable-payment-boundary
"""
import re
from uuid import UUID
from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from profiles.models import Profile
from .daraja import DarajaSandbox, PaymentBlocked, configuration
from .models import PaymentCheckout, PaymentOffer


def start_checkout(owner, *, decision_id, offer_id, terms_version, phone):
    if connection.in_atomic_block:
        raise PaymentBlocked('Checkout must run outside a wrapping transaction.')
    if not isinstance(decision_id, UUID) or not isinstance(offer_id, UUID):
        raise PaymentBlocked('Explicit decision and offer UUIDs are required.')
    # Existing identities remain inspectable when initiation is disabled. No repeat.
    prior = PaymentCheckout.objects.filter(decision_id=decision_id).first()
    if prior:
        if prior.owner_id != owner.pk:
            raise PaymentBlocked('Checkout unavailable.')
        return prior
    if not settings.PAYMENTS_ENABLED or not owner.is_active:
        raise PaymentBlocked('Checkout is inactive.')
    config = configuration()
    if not isinstance(phone, str) or not re.fullmatch(r'254[17][0-9]{8}', phone):
        raise PaymentBlocked('Use a Kenyan payer number in international format.')
    with transaction.atomic(durable=True):
        # First write serializes owner decisions on SQLite as well as row-locking DBs.
        if not Profile.objects.filter(user=owner).update(user_id=owner.pk):
            raise PaymentBlocked('Profile unavailable.')
        prior = PaymentCheckout.objects.filter(decision_id=decision_id).first()
        if prior:
            if prior.owner_id != owner.pk:
                raise PaymentBlocked('Checkout unavailable.')
            return prior
        if PaymentCheckout.objects.filter(owner=owner).exclude(state__in=['settled', 'closed']).exists():
            raise PaymentBlocked('Reconcile the existing checkout before any new initiation.')
        offer = PaymentOffer.objects.filter(pk=offer_id, active=True).first()
        if (not offer or not offer.terms_version or terms_version != offer.terms_version
                or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', offer.capability)
                or not 1 <= offer.term_seconds <= 366*86400):
            raise PaymentBlocked('Approved server offer and exact current terms are required.')
        checkout = PaymentCheckout.objects.create(owner=owner, decision_id=decision_id, offer=offer,
            amount_kes=offer.amount_kes, term_seconds=offer.term_seconds,
            capability=offer.capability, terms_version=offer.terms_version,
            merchant_shortcode=config['SHORTCODE'], payer_fingerprint=salted_hmac(
                'ajiri-payment-payer-v1', phone, algorithm='sha256').hexdigest())
    # The committed handoff_started state survives process death, even before I/O.
    try:
        if (not settings.PAYMENTS_ENABLED
                or not type(owner).objects.filter(pk=owner.pk, is_active=True).exists()
                or not PaymentOffer.objects.filter(pk=checkout.offer_id, active=True,
                    amount_kes=checkout.amount_kes, term_seconds=checkout.term_seconds,
                    terms_version=checkout.terms_version, capability=checkout.capability).exists()):
            raise PaymentBlocked('Checkout is inactive.')
        reference, merchant = DarajaSandbox().initiate(checkout, phone)
        PaymentCheckout.objects.filter(pk=checkout.pk, state='handoff_started').update(
            state='accepted', provider_reference=reference, merchant_reference=merchant, updated_at=timezone.now())
    except Exception:
        PaymentCheckout.objects.filter(pk=checkout.pk, state='handoff_started').update(state='unknown', updated_at=timezone.now())
    checkout.refresh_from_db()
    return checkout


def reconcile_checkout(owner, checkout_id):
    checkout = PaymentCheckout.objects.filter(pk=checkout_id, owner=owner).first()
    if not checkout:
        raise PaymentBlocked('Checkout unavailable.')
    if checkout.state in ('settled', 'closed'):
        return checkout
    if not settings.DARAJA_RECONCILIATION_ENABLED:
        raise PaymentBlocked('Provider reconciliation is inactive.')
    # A read-only query cannot initiate, resolve missing receipts, or grant anything.
    state = DarajaSandbox().query(checkout)
    PaymentCheckout.objects.filter(pk=checkout.pk, state=checkout.state).update(state=state, updated_at=timezone.now())
    checkout.refresh_from_db()
    return checkout
