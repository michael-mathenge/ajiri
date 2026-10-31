"""Single-attempt, TLS-verified Daraja sandbox Express transport.

No production host, callback authority, settlement inference or automatic retries.
see docs/CONCEPTS.md#durable-payment-boundary
"""
import base64
import json
import re
from datetime import datetime
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from zoneinfo import ZoneInfo

from django.conf import settings


class PaymentBlocked(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def configuration():
    if (not settings.DARAJA_SANDBOX_ENABLED or not settings.DARAJA_MERCHANT_REVIEWED
            or settings.DARAJA_PRODUCT_REVIEW != 'express-paybill-v1'):
        raise PaymentBlocked('Reviewed sandbox merchant/product configuration is required.')
    values = {name: getattr(settings, 'DARAJA_'+name, '') for name in (
        'CONSUMER_KEY', 'CONSUMER_SECRET', 'PASSKEY', 'SHORTCODE', 'CALLBACK_URL')}
    if any(not isinstance(value, str) or not value or len(value) > 1024
           or any(ord(char) < 32 for char in value) for value in values.values()):
        raise PaymentBlocked('Private sandbox configuration is incomplete.')
    url = urlsplit(values['CALLBACK_URL'])
    if (not re.fullmatch(r'[0-9]{5,8}', values['SHORTCODE']) or url.scheme != 'https'
            or not url.hostname or url.username or url.password or url.query or url.fragment
            or url.port not in (None, 443)):
        raise PaymentBlocked('Reviewed merchant/callback configuration is required.')
    return values


class DarajaSandbox:
    HOST = 'https://sandbox.safaricom.co.ke'

    def __init__(self):
        self.config = configuration()

    def _request(self, path, authorization, payload=None):
        # Disable ambient proxy credentials and redirects; default HTTPS verifies TLS.
        request = Request(self.HOST+path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={'Authorization': authorization, 'Content-Type': 'application/json',
                     'Accept': 'application/json'})
        try:
            with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=10) as response:
                raw = response.read(16385)
                if response.status != 200 or len(raw) > 16384:
                    raise ValueError
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise ValueError
                return result
        except Exception:
            # Never include provider text, payer information or credentials in errors.
            raise PaymentBlocked('Provider response unconfirmed; no automatic retry.') from None

    def _token(self):
        credentials = base64.b64encode((self.config['CONSUMER_KEY']+':'+self.config['CONSUMER_SECRET']).encode()).decode()
        result = self._request('/oauth/v1/generate?grant_type=client_credentials', 'Basic '+credentials)
        token = result.get('access_token')
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9._~-]{1,2048}', token):
            raise PaymentBlocked('Provider authentication unconfirmed.')
        return token

    def _password(self):
        timestamp = datetime.now(ZoneInfo('Africa/Nairobi')).strftime('%Y%m%d%H%M%S')
        return {'BusinessShortCode': self.config['SHORTCODE'], 'Timestamp': timestamp,
            'Password': base64.b64encode((self.config['SHORTCODE']+self.config['PASSKEY']+timestamp).encode()).decode()}

    def initiate(self, checkout, phone):
        self.config = configuration()  # Recheck gates, not only object construction.
        if checkout.merchant_shortcode != self.config['SHORTCODE']:
            raise PaymentBlocked('Merchant changed; reconcile the original checkout.')
        if not re.fullmatch(r'254[17][0-9]{8}', phone) or type(checkout.amount_kes) is not int or checkout.amount_kes < 1:
            raise PaymentBlocked('Valid server amount and Kenyan payer number are required.')
        payload = {**self._password(), 'TransactionType': 'CustomerPayBillOnline',
            'Amount': checkout.amount_kes, 'PartyA': phone, 'PartyB': self.config['SHORTCODE'],
            'PhoneNumber': phone, 'CallBackURL': self.config['CALLBACK_URL'],
            'AccountReference': checkout.id.hex[:12], 'TransactionDesc': 'Ajiri checkout'}
        token = self._token()
        if not settings.PAYMENTS_ENABLED or configuration() != self.config:
            raise PaymentBlocked('Initiation configuration changed; no handoff.')
        result = self._request('/mpesa/stkpush/v1/processrequest', 'Bearer '+token, payload)
        reference, merchant = result.get('CheckoutRequestID'), result.get('MerchantRequestID')
        if (str(result.get('ResponseCode')) != '0' or not valid_reference(reference)
                or not valid_reference(merchant)):
            raise PaymentBlocked('Initiation unconfirmed; retain the original checkout.')
        return reference, merchant

    def query(self, checkout):
        self.config = configuration()
        if checkout.merchant_shortcode != self.config['SHORTCODE']:
            raise PaymentBlocked('Merchant changed; manual reconciliation is required.')
        if not valid_reference(checkout.provider_reference):
            raise PaymentBlocked('No confirmed provider reference; manual reconciliation is required.')
        result = self._request('/mpesa/stkpushquery/v1/query', 'Bearer '+self._token(),
            {**self._password(), 'CheckoutRequestID': checkout.provider_reference})
        if (result.get('CheckoutRequestID') != checkout.provider_reference
                or result.get('MerchantRequestID') != checkout.merchant_reference):
            raise PaymentBlocked('Provider identity disagreement; no settlement.')
        # Express query success does not establish amount/receipt/reversal evidence.
        return 'evidence_required' if str(result.get('ResultCode')) == '0' else 'unresolved'


def valid_reference(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value) is not None
