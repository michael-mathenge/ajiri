import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import IntegrityError, OperationalError, close_old_connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from .daraja import PaymentBlocked
from .entitlements import has_capability, materialize_grant, revoke_settlement, FREE
from .models import PaymentOffer, PaymentCheckout, PaymentSettlement, CapabilityGrant


@override_settings(ENTITLEMENTS_ENABLED=True, PAYMENT_EVIDENCE_VERSION='synthetic-evidence-v1',
    ENTITLEMENT_APPROVED_CAPABILITIES=['synthetic_extra'],
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class EntitlementTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='ledger@example.invalid')
        self.other = get_user_model().objects.create_user(email='other-ledger@example.invalid')
        self.offer = PaymentOffer.objects.create(amount_kes=100, term_seconds=3600,
            capability='synthetic_extra', terms_version='synthetic-v1')
        self.now = timezone.now()
        self.row = self.settlement()

    def settlement(self, receipt=None):
        checkout = PaymentCheckout.objects.create(owner=self.user, decision_id=uuid.uuid4(), offer=self.offer,
            amount_kes=100, term_seconds=3600, capability='synthetic_extra', terms_version='synthetic-v1',
            merchant_shortcode='123456', payer_fingerprint='a'*64, state='accepted',
            provider_reference=uuid.uuid4().hex, merchant_reference=uuid.uuid4().hex)
        PaymentCheckout.objects.filter(pk=checkout.pk).update(created_at=self.now-timedelta(minutes=2))
        # Synthetic trusted-boundary fixture only. No runtime mapper/writer is claimed.
        return PaymentSettlement.objects.create(checkout=checkout, provider_receipt=receipt or uuid.uuid4().hex,
            amount_kes=100, merchant_shortcode='123456', payer_fingerprint='a'*64,
            paid_at=self.now-timedelta(minutes=1), verified_at=self.now,
            evidence_version='synthetic-evidence-v1', evidence_sha256='b'*64, state='settled')

    def test_atomic_grant_replay_never_extends_fixed_term_or_changes_owner(self):
        first = materialize_grant(self.row.id)
        self.assertEqual(materialize_grant(self.row.id).id, first.id)
        self.assertEqual(CapabilityGrant.objects.count(), 1)
        self.assertEqual(first.ends_at, self.row.paid_at+timedelta(hours=1))
        self.assertTrue(has_capability(self.user, 'synthetic_extra', now=self.now))
        self.assertFalse(has_capability(self.other, 'synthetic_extra', now=self.now))
        self.assertFalse(has_capability(self.user, 'synthetic_extra', now=first.ends_at))

    def test_callback_or_query_state_no_settlement_is_never_a_capability(self):
        PaymentSettlement.objects.filter(pk=self.row.id).update(state='unverified', verified_at=None)
        PaymentCheckout.objects.filter(pk=self.row.checkout_id).update(state='evidence_required')
        with self.assertRaises(PaymentBlocked):
            materialize_grant(self.row.id)
        self.assertFalse(has_capability(self.user, 'synthetic_extra'))

    def test_receipt_amount_currency_identity_version_and_future_time_mismatch_deny(self):
        changes = ({'amount_kes': 999}, {'merchant_shortcode': '999999'}, {'payer_fingerprint': 'c'*64},
            {'evidence_version': 'wrong'}, {'evidence_sha256': ''}, {'verified_at': self.now+timedelta(days=1)},
            {'paid_at': self.now-timedelta(days=1)})
        original = PaymentSettlement.objects.values().get(pk=self.row.id)
        for change in changes:
            PaymentSettlement.objects.filter(pk=self.row.id).update(**change)
            with self.assertRaises(PaymentBlocked):
                materialize_grant(self.row.id)
            PaymentSettlement.objects.filter(pk=self.row.id).update(**{key: original[key] for key in change})
        self.assertEqual(CapabilityGrant.objects.count(), 0)
        with self.assertRaises(IntegrityError):
            PaymentSettlement.objects.filter(pk=self.row.id).update(currency='USD')

    def test_rollback_after_grant_write_and_before_checkout_commit_recovers_one_grant(self):
        with patch.object(PaymentCheckout.objects, 'filter', side_effect=RuntimeError('synthetic interrupted commit')):
            with self.assertRaises(RuntimeError):
                materialize_grant(self.row.id)
        self.assertEqual(CapabilityGrant.objects.count(), 0)
        self.row.checkout.refresh_from_db()
        self.assertEqual(self.row.checkout.state, 'accepted')
        self.assertEqual(materialize_grant(self.row.id).settlement_id, self.row.id)

    def test_refund_is_terminal_duplicate_reversal_and_stale_grant_cannot_revive(self):
        materialize_grant(self.row.id)
        for _ in range(2):
            revoke_settlement(self.row.id, reversal_sha256='c'*64, evidence_version='synthetic-evidence-v1')
        self.assertFalse(has_capability(self.user, 'synthetic_extra'))
        with self.assertRaises(PaymentBlocked):
            materialize_grant(self.row.id)
        self.assertEqual(CapabilityGrant.objects.count(), 1)
        with self.assertRaises(PaymentBlocked):
            revoke_settlement(self.row.id, reversal_sha256='', evidence_version='synthetic-evidence-v1')

    def test_new_upgrade_and_old_refund_keep_independent_receipts_without_term_stacking(self):
        first = materialize_grant(self.row.id)
        second = self.settlement()
        with self.assertRaises(IntegrityError):
            PaymentSettlement.objects.filter(pk=second.id).update(provider_receipt=self.row.provider_receipt)
        next_grant = materialize_grant(second.id)
        self.assertEqual(next_grant.ends_at, first.ends_at)
        revoke_settlement(self.row.id, reversal_sha256='c'*64, evidence_version='synthetic-evidence-v1')
        self.assertTrue(has_capability(self.user, 'synthetic_extra'))
        revoke_settlement(second.id, reversal_sha256='d'*64, evidence_version='synthetic-evidence-v1')
        self.assertFalse(has_capability(self.user, 'synthetic_extra'))

    def test_default_off_unapproved_capability_and_tampered_grant_fall_back_to_free(self):
        grant = materialize_grant(self.row.id)
        for config in ({'ENTITLEMENTS_ENABLED': False}, {'PAYMENT_EVIDENCE_VERSION': ''},
                       {'ENTITLEMENT_APPROVED_CAPABILITIES': []}):
            with override_settings(**config):
                self.assertFalse(has_capability(self.user, 'synthetic_extra'))
                for capability in FREE:
                    self.assertTrue(has_capability(self.user, capability))
        CapabilityGrant.objects.filter(pk=grant.pk).update(ends_at=grant.ends_at+timedelta(days=1))
        self.assertFalse(has_capability(self.user, 'synthetic_extra'))
        with self.assertRaises(PaymentBlocked):
            materialize_grant(self.row.id)

    def test_concurrent_grant_projection_never_duplicates_or_extends_receipt(self):
        barrier = Barrier(2)
        def project():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return str(materialize_grant(self.row.id).id)
            except OperationalError:
                return 'contention'  # Safe SQLite lock refusal; no provider I/O exists here.
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: project(), range(2)))
        self.assertTrue(any(result != 'contention' for result in results))
        self.assertEqual(CapabilityGrant.objects.count(), 1)
        grant = materialize_grant(self.row.id)
        self.assertEqual(grant.ends_at, self.row.paid_at+timedelta(hours=1))
