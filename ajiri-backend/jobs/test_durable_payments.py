import json
import uuid
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import TransactionTestCase, SimpleTestCase, override_settings
from rest_framework.test import APIClient
from .daraja import DarajaSandbox, PaymentBlocked, configuration
from .models import PaymentOffer, PaymentCheckout
from .payments import start_checkout, reconcile_checkout


SANDBOX = dict(PAYMENTS_ENABLED=True, DARAJA_SANDBOX_ENABLED=True,
    DARAJA_RECONCILIATION_ENABLED=True, DARAJA_MERCHANT_REVIEWED=True,
    DARAJA_PRODUCT_REVIEW='express-paybill-v1', DARAJA_CONSUMER_KEY='synthetic-key',
    DARAJA_CONSUMER_SECRET='synthetic-secret', DARAJA_PASSKEY='synthetic-passkey',
    DARAJA_SHORTCODE='123456', DARAJA_CALLBACK_URL='https://callback.example.invalid/unused/',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])


@override_settings(**SANDBOX)
class DurablePaymentTests(TransactionTestCase):
    def setUp(self):
        for cache in caches.all():
            cache.clear()
        self.user = get_user_model().objects.create_user(email='payer@example.invalid')
        self.other = get_user_model().objects.create_user(email='other-payer@example.invalid')
        # Test-only offer. No runtime price/term/catalogue is seeded by migrations.
        self.offer = PaymentOffer.objects.create(active=True, amount_kes=100, term_seconds=3600,
            capability='synthetic_extra', terms_version='synthetic-v1')
        self.key = uuid.uuid4()
        self.transport = patch('jobs.daraja.build_opener', side_effect=AssertionError('No network in tests'))
        self.transport.start()
        self.addCleanup(self.transport.stop)

    def start(self, **kwargs):
        values = dict(decision_id=self.key, offer_id=self.offer.id, terms_version=self.offer.terms_version,
            phone='254700000000')
        values.update(kwargs)
        return start_checkout(self.user, **values)

    def test_committed_claim_precedes_handoff_replays_same_id_and_blocks_new_decisions(self):
        def accepted(row, phone):
            self.assertTrue(PaymentCheckout.objects.filter(pk=row.pk, state='handoff_started').exists())
            return 'checkout_test', 'merchant_test'
        with patch.object(DarajaSandbox, 'initiate', side_effect=accepted) as send:
            row = self.start()
            self.assertEqual(row.state, 'accepted')
            self.assertEqual(self.start().id, row.id)
            with self.assertRaises(PaymentBlocked):
                self.start(decision_id=uuid.uuid4())
            send.assert_called_once()
        self.assertEqual(row.amount_kes, 100)
        self.assertNotIn('254700000000', str(PaymentCheckout.objects.values().get()))

    def test_unknown_and_process_death_never_repeat_provider_handoff(self):
        with patch.object(DarajaSandbox, 'initiate', side_effect=TimeoutError) as send:
            row = self.start()
            self.assertEqual(row.state, 'unknown')
            self.start()
            send.assert_called_once()
        PaymentCheckout.objects.all().delete()  # Isolated synthetic test DB only.
        with patch.object(DarajaSandbox, 'initiate', side_effect=SystemExit) as send:
            with self.assertRaises(SystemExit):
                self.start()
            self.assertEqual(self.start().state, 'handoff_started')
            send.assert_called_once()

    def test_owner_identity_terms_inactive_offer_and_off_gates(self):
        for changes in ({'terms_version': 'wrong'}, {'phone': '0700000000'}):
            with self.assertRaises(PaymentBlocked):
                self.start(**changes)
        with override_settings(PAYMENTS_ENABLED=False), self.assertRaises(PaymentBlocked):
            self.start()
        with patch.object(DarajaSandbox, 'initiate', return_value=('checkout_test', 'merchant_test')):
            row = self.start()
        with self.assertRaises(PaymentBlocked):
            start_checkout(self.other, decision_id=self.key, offer_id=self.offer.id,
                terms_version=self.offer.terms_version, phone='254700000000')
        with override_settings(PAYMENTS_ENABLED=False):
            self.assertEqual(self.start().id, row.id)

    def test_offer_edits_cannot_change_checkout_snapshot_and_query_cannot_settle(self):
        with patch.object(DarajaSandbox, 'initiate', return_value=('checkout_test', 'merchant_test')):
            row = self.start()
        PaymentOffer.objects.filter(pk=self.offer.id).update(amount_kes=999, term_seconds=1)
        with patch.object(DarajaSandbox, 'query', return_value='evidence_required'):
            row = reconcile_checkout(self.user, row.id)
        self.assertEqual((row.state, row.amount_kes, row.term_seconds), ('evidence_required', 100, 3600))
        with self.assertRaises(PaymentBlocked):
            reconcile_checkout(self.other, row.id)
        with override_settings(DARAJA_RECONCILIATION_ENABLED=False), self.assertRaises(PaymentBlocked):
            reconcile_checkout(self.user, row.id)

    def test_api_owner_isolation_strict_server_pricing_and_disabled_status_access(self):
        client = APIClient()
        client.force_authenticate(self.user)
        body = dict(decision_id=str(self.key), offer_id=str(self.offer.id),
            terms_version='synthetic-v1', phone='254700000000')
        url = '/api/jobs/payments/checkouts/'
        self.assertEqual(client.post(url, {**body, 'amount_kes': 1}, format='json').status_code, 400)
        with patch.object(DarajaSandbox, 'initiate', return_value=('checkout_test', 'merchant_test')):
            response = client.post(url, body, format='json')
        self.assertEqual(response.status_code, 202)
        self.assertNotIn('phone', response.data)
        detail = url+response.data['id']+'/'
        with override_settings(PAYMENTS_ENABLED=False):
            self.assertEqual(client.get(detail).status_code, 200)
            self.assertEqual(client.post(url, body, format='json').status_code, 404)
        client.force_authenticate(self.other)
        self.assertEqual(client.get(detail).status_code, 404)

    def test_financial_retention_blocks_erasure_before_any_removal(self):
        from accounts.erasure import inventory
        from django.core.management.base import CommandError
        with patch.object(DarajaSandbox, 'initiate', side_effect=TimeoutError):
            self.start()
        with self.assertRaisesMessage(CommandError, 'financial retention'):
            inventory(self.user)
        self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())

    def test_spoofed_replayed_callback_only_records_hint_and_never_queries_or_settles(self):
        with patch.object(DarajaSandbox, 'initiate', return_value=('checkout_test', 'merchant_test')):
            row = self.start()
        client = APIClient()
        url = '/api/jobs/payments/daraja/callback/'
        payload = {'Body': {'stkCallback': {'CheckoutRequestID': 'checkout_test',
            'MerchantRequestID': 'merchant_test', 'ResultCode': 0,
            'CallbackMetadata': {'Items': [{'Name': 'Amount', 'Value': 999}]}}}}
        with patch.object(DarajaSandbox, 'query') as query:
            for _ in range(2):
                self.assertEqual(client.post(url, payload, format='json').status_code, 200)
            query.assert_not_called()
        row.refresh_from_db()
        self.assertEqual(row.state, 'accepted')
        self.assertIsNotNone(row.callback_seen_at)
        self.assertEqual(client.post(url, 'x'*8193, content_type='application/json').status_code, 400)
        with override_settings(DARAJA_SANDBOX_ENABLED=False):
            self.assertEqual(client.post(url, payload, format='json').status_code, 404)


@override_settings(**SANDBOX)
class DarajaWireTests(SimpleTestCase):
    def test_default_off_and_missing_product_never_construct_a_request(self):
        with override_settings(DARAJA_SANDBOX_ENABLED=False), patch('jobs.daraja.build_opener') as opener:
            with self.assertRaises(PaymentBlocked):
                DarajaSandbox()
            opener.assert_not_called()
        with override_settings(DARAJA_PRODUCT_REVIEW=''), self.assertRaises(PaymentBlocked):
            configuration()

    def test_wire_payload_has_server_price_fixed_host_and_auth_without_redirects(self):
        gateway = DarajaSandbox()
        row = MagicMock(id=uuid.uuid4(), amount_kes=100, merchant_shortcode='123456')
        replies = [{'access_token': 'synthetic-token'},
            {'ResponseCode': '0', 'CheckoutRequestID': 'checkout_test', 'MerchantRequestID': 'merchant_test'}]
        captured = []
        def open_request(request, **kwargs):
            captured.append(request)
            response = MagicMock(status=200)
            response.read.return_value = json.dumps(replies.pop(0)).encode()
            response.__enter__.return_value = response
            return response
        with patch('jobs.daraja.build_opener') as builder:
            builder.return_value.open.side_effect = open_request
            self.assertEqual(gateway.initiate(row, '254700000000'), ('checkout_test', 'merchant_test'))
            self.assertEqual(builder.call_count, 2)
        payload = json.loads(captured[1].data)
        self.assertEqual(payload['Amount'], 100)
        self.assertEqual(payload['PartyB'], '123456')
        self.assertEqual(captured[1].full_url, 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest')
        self.assertTrue(captured[0].get_header('Authorization').startswith('Basic '))

    def test_error_oversize_malformed_and_identity_disagreement_fail_without_retry(self):
        gateway = DarajaSandbox()
        for raw in (b'x'*16385, b'not json', b'[]'):
            with patch('jobs.daraja.build_opener') as builder:
                response = builder.return_value.open.return_value.__enter__.return_value
                response.status, response.read.return_value = 200, raw
                with self.assertRaises(PaymentBlocked):
                    gateway._request('/unused', 'Bearer synthetic')
                builder.return_value.open.assert_called_once()
        row = MagicMock(provider_reference='checkout_test', merchant_reference='merchant_test', merchant_shortcode='123456')
        with patch.object(gateway, '_token', return_value='synthetic'), patch.object(gateway, '_request', return_value={
                'CheckoutRequestID': 'other', 'MerchantRequestID': 'merchant_test', 'ResultCode': 0}):
            with self.assertRaises(PaymentBlocked):
                gateway.query(row)
