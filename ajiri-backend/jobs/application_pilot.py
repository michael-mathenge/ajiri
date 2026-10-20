"""Separate, explicit application-pilot boundary. Not connected to production dispatch.

No settings/credentials are loaded here. The release runbook requires a current
provider-limit review and final approval before constructing a live adapter.
see docs/CONCEPTS.md#application-send-authorization
"""
import base64
from dataclasses import dataclass
import json
import re

from .delivery_service import DeliveryError
from .send_authorization import address, MAX_RAW


@dataclass(frozen=True)
class ApplicationPilot:
    owner_id: int
    recipient: str
    reply_to: str
    sender: str
    max_request_bytes: int
    provider_limit_review: str
    limit: int = 5
    application_only: bool = True

    def __post_init__(self):
        if (type(self.owner_id) is not int or self.owner_id <= 0
            or type(self.max_request_bytes) is not int or self.max_request_bytes <= 0
            or self.limit != 5 or self.application_only is not True
            or not self.provider_limit_review.strip()):
            raise ValueError('Reviewed application pilot configuration required.')
        for value in (self.recipient, self.reply_to, self.sender):
            if address(value) != value:
                raise ValueError('Use exact normalized pilot addresses.')


class ApplicationPilotTransport:
    def __init__(self, policy, transport, *, still_approved):
        self.policy, self.transport, self.still_approved = policy, transport, still_approved

    def prepare(self, **kwargs):
        payload = self.transport.prepare(**kwargs)
        self.validate(payload)
        return payload

    def validate(self, payload):
        try:
            if not self.still_approved(self.policy) or len(payload) > self.policy.max_request_bytes:
                raise ValueError
            message = json.loads(payload)
            if (set(message) != {'sender', 'to', 'replyTo', 'subject', 'textContent', 'attachment'}
                or message['to'] != [{'email': self.policy.recipient}]
                or message['replyTo'] != {'email': self.policy.reply_to}
                or message['sender'] != {'email': self.policy.sender, 'name': 'Ajiri'}
                or not message['subject'].startswith('[AJIRI PILOT] ')
                or len(message['attachment']) != 2):
                raise ValueError
            total = 0
            for item in message['attachment']:
                if set(item) != {'name', 'content'} or not re.fullmatch(r'[A-Za-z0-9_-]{1,115}\.docx', item['name']):
                    raise ValueError
                data = base64.b64decode(item['content'], validate=True)
                if not 0 < len(data) <= MAX_RAW // 2:
                    raise ValueError
                total += len(data)
            if total > MAX_RAW:
                raise ValueError
        except (ValueError, TypeError, KeyError, AttributeError):
            raise DeliveryError('Application pilot message is not allowed.') from None

    def send(self, payload):
        self.validate(payload)  # Recheck the exact recipient and approval at the final boundary.
        return self.transport.send(payload)
