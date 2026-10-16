"""Isolated HTTPS adapter; no email backend registration, retries or credentials loading.

see docs/CONCEPTS.md#isolated-email-transport
"""
import base64
from dataclasses import dataclass, field
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.core.validators import validate_email


@dataclass(frozen=True)
class Result:
    state: str
    provider_message_id: str = ''
    failure_category: str = ''


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward api-key or CV content to a redirect destination.


@dataclass(frozen=True, repr=False)
class BrevoTransport:
    api_key: str = field(repr=False)
    sender: str
    timeout: float = 10
    sender_name: str = ''

    def __repr__(self):
        return 'BrevoTransport(configuration=redacted)'

    def prepare(self, *, recipient, subject, text, reply_to=None, attachments=(), max_attachment_bytes=0):
        """Freeze one-recipient payload BEFORE claiming quota; attachments are bytes only.

        No attachment policy was silently selected: caller must supply an approved
        aggregate byte limit, otherwise attachments are disabled.
        """
        if not self.api_key or not 0 < self.timeout <= 60:
            raise ValueError('Invalid transport configuration.')
        for address in (self.sender, recipient, *([reply_to] if reply_to else [])):
            validate_email(address)
            if '\r' in address or '\n' in address:
                raise ValueError('Invalid address.')
        if not subject or '\r' in subject or '\n' in subject or not text:
            raise ValueError('Invalid message.')
        payload = {'sender': {'email': self.sender}, 'to': [{'email': recipient}],
                   'subject': subject, 'textContent': text}
        if self.sender_name:
            if self.sender_name != 'Ajiri':
                raise ValueError('Invalid sender name.')
            payload['sender']['name'] = self.sender_name
        if reply_to:
            payload['replyTo'] = {'email': reply_to}
        total, files = 0, []
        for name, content in attachments:
            if not isinstance(content, bytes) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,120}', name):
                raise ValueError('Invalid attachment.')
            total += len(content)
            if total > max_attachment_bytes or not content:
                raise ValueError('Attachment limit exceeded.')
            files.append({'name': name, 'content': base64.b64encode(content).decode('ascii')})
        if files:
            payload['attachment'] = files
        return json.dumps(payload, ensure_ascii=True).encode('utf-8')

    def send(self, payload):
        request = Request('https://api.brevo.com/v3/smtp/email', data=payload,
            headers={'api-key': self.api_key, 'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST')
        try:
            with build_opener(NoRedirect()).open(request, timeout=self.timeout) as response:
                body = response.read(16385)
                if response.status != 201 or len(body) > 16384:
                    return Result('unknown', failure_category='transport')
                receipt = json.loads(body).get('messageId')
                # Permit only a compact opaque receipt, never arbitrary provider text.
                if not isinstance(receipt, str) or not re.fullmatch(r'[A-Za-z0-9<>@._:+/=-]{1,255}', receipt):
                    return Result('unknown', failure_category='transport')
                return Result('accepted', provider_message_id=receipt)
        except HTTPError as error:
            status = error.code
            error.close()  # Do not read, log or expose raw provider rejection bodies.
            if 400 <= status < 500 and status != 408:
                return Result('definite_failure', failure_category='provider_rejected')
            return Result('unknown', failure_category='transport')
        except (TimeoutError, URLError, OSError):
            return Result('unknown', failure_category='timeout')
        except (ValueError, TypeError, AttributeError):
            return Result('unknown', failure_category='transport')
