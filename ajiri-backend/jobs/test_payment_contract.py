"""Pure synthetic contracts: no payment destination or real payer data."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest import TestCase
from uuid import uuid4

from .payment_test_contract import ContractError, SyntheticCheckoutLab, SyntheticGateway, SyntheticStatus


class SyntheticPaymentTests(TestCase):
    def setUp(self):
        self.owner, self.other = uuid4(), uuid4()
        self.gateway = SyntheticGateway()
        self.lab = SyntheticCheckoutLab(self.gateway)
        self.now = datetime(2026, 10, 24, tzinfo=timezone.utc)
        self.row = self.lab.start(self.owner, uuid4())

    def status(self, **changes):
        result = SyntheticStatus(self.row.id, self.owner, 100, 'KES', 'success', 1, 'synthetic-receipt')
        self.gateway.statuses[self.row.id] = replace(result, **changes)

    def test_initialization_and_callback_cannot_grant_capability(self):
        self.assertEqual(self.row.amount, 100)
        self.assertFalse(self.lab.callback_hint({'state': 'success', 'amount': 1}))
        self.assertEqual(self.lab.capabilities(self.owner, self.row.id, now=self.now)['tier'], 'free')

    def test_server_catalogue_has_no_client_price_parameter(self):
        with self.assertRaises(TypeError):
            self.lab.start(self.owner, uuid4(), amount=1)
        with self.assertRaises(ContractError):
            self.lab.start(self.owner, uuid4(), 'client-premium')

    def test_anonymous_and_other_owner_are_isolated(self):
        for owner in (None, self.other, str(self.owner)):
            with self.subTest(owner=type(owner).__name__), self.assertRaises(ContractError):
                self.lab.get(owner, self.row.id)

    def test_duplicate_concurrent_start_hands_off_once(self):
        decision = uuid4()
        with ThreadPoolExecutor(max_workers=8) as pool:
            rows = list(pool.map(lambda _: self.lab.start(self.owner, decision), range(16)))
        self.assertEqual(len({row.id for row in rows}), 1)
        self.assertEqual(self.gateway.starts.count(rows[0].id), 1)

    def test_timeout_stays_unknown_and_duplicate_start_does_not_retry(self):
        self.gateway.timeout = True
        decision = uuid4()
        row = self.lab.start(self.owner, decision)
        self.assertEqual(row.state, 'unknown')
        self.assertEqual(self.lab.start(self.owner, decision), row)
        self.assertEqual(self.gateway.starts.count(row.id), 1)

    def test_authoritative_success_and_replay_do_not_extend_term(self):
        self.status()
        first = self.lab.reconcile(self.owner, self.row.id, now=self.now)
        again = self.lab.reconcile(self.owner, self.row.id, now=self.now+timedelta(days=2))
        self.assertEqual(first, again)
        self.assertTrue(self.lab.capabilities(self.owner, self.row.id, now=self.now)['synthetic_paid_capability'])
        self.assertEqual(self.lab.capabilities(self.owner, self.row.id, now=first.expires_at)['tier'], 'free')

    def test_spoofed_or_mismatched_status_fails_closed(self):
        for changes in ({'owner': self.other}, {'checkout_id': uuid4()}, {'amount': 1}, {'currency': 'USD'},
                        {'receipt': ''}, {'revision': True}, {'amount': True}, {'state': 'client-approved'}):
            with self.subTest(changes=tuple(changes)), self.assertRaises(ContractError):
                self.status(**changes)
                self.lab.reconcile(self.owner, self.row.id, now=self.now)
        self.assertEqual(self.lab.get(self.owner, self.row.id).state, 'pending')

    def test_failure_cancel_and_unknown_preserve_free_access(self):
        for state in ('failed', 'cancelled', 'unknown', 'pending'):
            with self.subTest(state=state):
                self.status(state=state, revision=self.lab.get(self.owner, self.row.id).revision+1)
                self.lab.reconcile(self.owner, self.row.id, now=self.now)
                result = self.lab.capabilities(self.owner, self.row.id, now=self.now)
                self.assertEqual(result['tier'], 'free')
                self.assertTrue(result['browse_jobs'] and result['apply'] and result['download_existing_documents'])

    def test_refund_revokes_and_out_of_order_success_cannot_restore(self):
        self.status()
        self.lab.reconcile(self.owner, self.row.id, now=self.now)
        self.status(state='refunded', revision=2)
        self.lab.reconcile(self.owner, self.row.id, now=self.now)
        self.status()
        self.assertEqual(self.lab.reconcile(self.owner, self.row.id, now=self.now).state, 'refunded')
        self.status(revision=3)
        with self.assertRaises(ContractError):
            self.lab.reconcile(self.owner, self.row.id, now=self.now)

    def test_receipt_cannot_pay_two_checkouts(self):
        self.status()
        self.lab.reconcile(self.owner, self.row.id, now=self.now)
        second = self.lab.start(self.owner, uuid4())
        self.gateway.statuses[second.id] = SyntheticStatus(second.id,self.owner,100,'KES','success',1,'synthetic-receipt')
        with self.assertRaises(ContractError):
            self.lab.reconcile(self.owner, second.id, now=self.now)

    def test_interrupted_receipt_write_is_atomic_and_query_can_reconcile(self):
        self.status()
        self.lab.fail_write = True
        with self.assertRaises(ContractError):
            self.lab.reconcile(self.owner, self.row.id, now=self.now)
        self.assertEqual(self.lab.get(self.owner, self.row.id), self.row)
        self.lab.fail_write = False
        self.assertEqual(self.lab.reconcile(self.owner, self.row.id, now=self.now).state, 'success')
        self.assertEqual(self.gateway.starts, [self.row.id])

    def test_real_transport_substitution_and_naive_time_are_rejected(self):
        with self.assertRaises(ContractError):
            SyntheticCheckoutLab(object())
        with self.assertRaises(ContractError):
            self.lab.reconcile(self.owner, self.row.id, now=datetime(2026, 10, 24))
