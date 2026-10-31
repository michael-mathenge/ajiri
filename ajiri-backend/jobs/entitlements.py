"""Durable paid capability evaluation; no production settlement writer exists yet.

Free browsing/applying/existing documents are independent of this optional service.
see docs/CONCEPTS.md#verified-capability-ledger
"""
import re
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from profiles.models import Profile
from .daraja import PaymentBlocked, valid_reference
from .models import CapabilityGrant, PaymentCheckout, PaymentSettlement

FREE = {'browse_jobs', 'apply', 'download_existing_documents'}


def _valid(row, now):
    checkout = row.checkout
    return bool(settings.ENTITLEMENTS_ENABLED and settings.PAYMENT_EVIDENCE_VERSION
        and row.evidence_version == settings.PAYMENT_EVIDENCE_VERSION
        and row.state == 'settled' and row.verified_at
        and checkout.created_at <= row.paid_at <= row.verified_at <= now
        and row.revoked_at is None and not row.reversal_sha256
        and re.fullmatch(r'[0-9a-f]{64}', row.evidence_sha256)
        and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', row.provider_receipt)
        and row.currency == 'KES' and row.amount_kes == checkout.amount_kes
        and row.merchant_shortcode == checkout.merchant_shortcode
        and row.payer_fingerprint == checkout.payer_fingerprint
        and checkout.state != 'closed'
        and valid_reference(checkout.provider_reference) and valid_reference(checkout.merchant_reference)
        and re.fullmatch(r'[0-9a-f]{64}', row.payer_fingerprint)
        and checkout.capability not in FREE
        and checkout.capability in settings.ENTITLEMENT_APPROVED_CAPABILITIES
        and 1 <= checkout.term_seconds <= 366*86400)


def materialize_grant(settlement_id):
    """Atomic, replay-safe projection from an already authenticated settlement.

    This is NOT the missing provider verifier. No request, callback, CLI or admin
    can create verified settlements. Fixtures exercise that trusted boundary only.
    """
    with transaction.atomic():
        candidate = PaymentSettlement.objects.select_related('checkout').filter(pk=settlement_id).first()
        if not candidate:
            raise PaymentBlocked('Verified settlement unavailable.')
        if not Profile.objects.filter(user_id=candidate.checkout.owner_id).update(user_id=candidate.checkout.owner_id):
            raise PaymentBlocked('Owner unavailable.')
        row = PaymentSettlement.objects.select_related('checkout').get(pk=settlement_id)
        if not _valid(row, timezone.now()):
            raise PaymentBlocked('Authoritative settlement evidence or approved capability is unavailable.')
        checkout = row.checkout
        ends_at = row.paid_at+timedelta(seconds=checkout.term_seconds)
        expected = dict(owner_id=checkout.owner_id, capability=checkout.capability,
            starts_at=row.paid_at, ends_at=ends_at)
        grant, _ = CapabilityGrant.objects.get_or_create(settlement=row, defaults=expected)
        if any(getattr(grant, key) != value for key, value in expected.items()):
            raise PaymentBlocked('Capability ledger mismatch; no extension or overwrite.')
        PaymentCheckout.objects.filter(pk=checkout.pk).update(state='settled', updated_at=timezone.now())
        return grant


def revoke_settlement(settlement_id, *, reversal_sha256, evidence_version):
    # Trusted internal boundary only; the actual reversal mapper is still blocked.
    if (not settings.PAYMENT_EVIDENCE_VERSION or evidence_version != settings.PAYMENT_EVIDENCE_VERSION
            or not re.fullmatch(r'[0-9a-f]{64}', reversal_sha256 or '')):
        raise PaymentBlocked('Authenticated reversal evidence is required.')
    with transaction.atomic():
        candidate = PaymentSettlement.objects.select_related('checkout').get(pk=settlement_id)
        Profile.objects.filter(user_id=candidate.checkout.owner_id).update(user_id=candidate.checkout.owner_id)
        # Terminal: stale settlement evidence cannot revive this receipt.
        PaymentSettlement.objects.filter(pk=settlement_id).exclude(state='revoked').update(
            state='revoked', revoked_at=timezone.now(), reversal_sha256=reversal_sha256)


def has_capability(owner, capability, *, now=None):
    if capability in FREE:
        return True
    if not settings.ENTITLEMENTS_ENABLED or not owner.is_active:
        return False
    now = now or timezone.now()
    if timezone.is_naive(now):
        raise PaymentBlocked('Use an aware capability time.')
    grants = CapabilityGrant.objects.filter(owner=owner, capability=capability,
        starts_at__lte=now, ends_at__gt=now).select_related('settlement__checkout').order_by('-ends_at')[:100]
    for grant in grants:
        row = grant.settlement
        if (_valid(row, now) and row.checkout.owner_id == owner.pk
                and grant.capability == row.checkout.capability and grant.starts_at == row.paid_at
                and grant.ends_at == row.paid_at+timedelta(seconds=row.checkout.term_seconds)):
            return True
    return False
