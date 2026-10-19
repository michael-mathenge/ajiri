"""Delivery accounting service; only account test/pilot callers are connected.

see docs/CONCEPTS.md#atomic-delivery-budgets
"""
from dataclasses import dataclass
import hashlib
import hmac
import time
import uuid
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import F
from django.utils import timezone

from profiles.models import Profile
from .brevo_transport import Result
from .models import Application, DeliveryAttempt as Attempt, DeliveryDailyBudget as Budget, Notification


class DeliveryError(Exception):
    pass


class QuotaExceeded(DeliveryError):
    pass


@dataclass(frozen=True)
class Policy:
    total: int = 200
    applications: int = 150
    accounts: int = 30
    alerts: int = 20
    per_user_applications: int = 10

    def __post_init__(self):
        values = (self.total, self.applications, self.accounts, self.alerts, self.per_user_applications)
        if any(type(value) is not int or value < 0 for value in values) or sum(values[1:4]) > self.total:
            raise ValueError('Invalid delivery limits.')


class DeliveryService:
    def __init__(self, transport, *, digest_key, policy=None, enabled=False, pilot=None):
        self.transport = transport
        self._digest_key = digest_key
        self.policy = policy or Policy()
        self.enabled = enabled  # Caller must pass eligibility and transport configuration checks.
        self.pilot = pilot

    def deliver(self, *, user_id, channel, recipient, subject, text, idempotency_key,
                application_id=None, notification_id=None, alert_consent_confirmed=False,
                retry_of=None, attachments=(), max_attachment_bytes=0):
        if not self.enabled:
            raise DeliveryError('Real delivery is disabled.')
        if transaction.get_connection().in_atomic_block:
            raise DeliveryError('Delivery must run outside caller transactions.')
        if not isinstance(self._digest_key, bytes) or len(self._digest_key) < 32:
            raise DeliveryError('Delivery digest configuration is unavailable.')
        key = uuid.UUID(str(idempotency_key))
        if channel not in Attempt.Channel.values:
            raise DeliveryError('Invalid delivery channel.')
        user = get_user_model().objects.get(pk=user_id, is_active=True)
        self._check_pilot(user, channel, recipient)
        application, notification = None, None
        if channel == 'application':
            application = Application.objects.get(pk=application_id, user=user)
            if notification_id or application.application_method != 'email' or application.status != 'ready_for_review':
                raise DeliveryError('Application is not ready for email delivery.')
            profile = Profile.objects.get(user=user)
            if not profile.email_verified_at or profile.verified_email.casefold() != user.email.casefold():
                raise DeliveryError('Verified mailbox required.')
            expected_recipient = application.application_email
        elif channel == 'alert':
            notification = Notification.objects.get(pk=notification_id, user=user)
            if application_id or not alert_consent_confirmed or not Profile.objects.get(user=user).notify_email:
                raise DeliveryError('Confirmed alert consent required.')
            expected_recipient = user.email
        else:
            if application_id or notification_id:
                raise DeliveryError('Account email must not link documents.')
            expected_recipient = user.email
        if recipient.casefold() != expected_recipient.casefold():
            raise DeliveryError('Recipient does not match the delivery purpose.')
        digest = hmac.new(self._digest_key, recipient.casefold().encode(), hashlib.sha256).hexdigest()
        payload = self.transport.prepare(recipient=recipient, subject=subject, text=text,
            reply_to=user.email if channel == 'application' else None,
            attachments=attachments, max_attachment_bytes=max_attachment_bytes)
        day = timezone.now().astimezone(ZoneInfo('Africa/Nairobi')).date()
        for number in range(3):
            try:
                attempt, created = self._reserve(user, channel, digest, key, day, application, notification,
                    retry_of)
                break
            except OperationalError:
                if number == 2:
                    raise DeliveryError('Delivery accounting is busy; no email was attempted.') from None
                time.sleep(0.02 * (number + 1))  # Database-only retry, always before network I/O.
            except (IntegrityError, ValidationError):
                raise DeliveryError('A conflicting delivery already exists; no email was attempted.') from None
        if not created:
            return attempt  # Repeated key never repeats provider I/O, regardless of outcome.
        try:
            result = self.transport.send(payload)
            if not isinstance(result, Result) or result.state not in ('accepted', 'definite_failure', 'unknown'):
                result = Result('unknown', failure_category='transport')
        except Exception:
            result = Result('unknown', failure_category='transport')  # Never surface credentials/provider text.
        # see docs/CONCEPTS.md#atomic-delivery-budgets
        # A competing reservation may hold SQLite's writer lock after provider I/O.
        # Retry only the conditional receipt write/read, never the provider call.
        for number in range(3):
            try:
                Attempt.objects.filter(pk=attempt.pk, state='reserved').update(state=result.state,
                    provider_message_id=result.provider_message_id, failure_category=result.failure_category,
                    resolved_at=timezone.now() if result.state != 'unknown' else None)
                attempt.refresh_from_db()
                return attempt
            except OperationalError:
                if number < 2:
                    time.sleep(0.02 * (number + 1))
                    continue
            except Exception:
                pass
            # A durable reserved/finished receipt blocks repeats even if reading it fails.
            raise DeliveryError('Delivery outcome needs reconciliation; do not retry.') from None

    def _check_pilot(self, user, channel, recipient):
        if self.pilot is not None and (channel not in ('password_reset', 'email_verification')
            or user.pk != self.pilot.owner_id or recipient.casefold() != self.pilot.recipient
            or user.email.casefold() != self.pilot.recipient):
            raise DeliveryError('Pilot delivery is not allowed.')

    def _reserve(self, user, channel, digest, key, day, application, notification, retry_of):
        counter, cap = {'application': ('application_reserved', self.policy.applications),
            'alert': ('alert_reserved', self.policy.alerts)}.get(channel, ('account_reserved', self.policy.accounts))
        with transaction.atomic():
            # INSERT is the FIRST database operation: SQLite serializes writers before
            # any read/check, including cold-start initialization and stale requests.
            Budget.objects.bulk_create([Budget(scope='global', day=day)], ignore_conflicts=True)
            existing = Attempt.objects.filter(idempotency_key=key).first()
            if existing:
                if (existing.user_id, existing.channel, existing.recipient_digest, existing.application_id,
                    existing.notification_id) != (user.pk, channel, digest,
                    application.pk if application else None, notification.pk if notification else None):
                    raise DeliveryError('Idempotency key belongs to another delivery.')
                return existing, False
            if not get_user_model().objects.filter(pk=user.pk, is_active=True).exists():
                raise DeliveryError('Inactive delivery owner.')
            if application:
                proof = Profile.objects.get(user=user)
                current_email = get_user_model().objects.get(pk=user.pk).email
                if (not Application.objects.filter(pk=application.pk, user=user,
                    status='ready_for_review', application_method='email',
                    application_email=application.application_email).exists()
                    or not proof.email_verified_at or proof.verified_email.casefold() != current_email.casefold()
                    or current_email != user.email):
                    raise DeliveryError('Application or verification changed before reservation.')
            elif notification:
                if not Profile.objects.filter(user=user, notify_email=True).exists():
                    raise DeliveryError('Alert preference changed before reservation.')
            elif get_user_model().objects.get(pk=user.pk).email != user.email:
                raise DeliveryError('Account email changed before reservation.')
            self._check_pilot(user, channel, user.email)
            target = Attempt.objects.filter(application=application) if application else (
                Attempt.objects.filter(notification=notification) if notification else
                Attempt.objects.filter(user=user, channel=channel, recipient_digest=digest))
            if target.filter(state__in=['reserved', 'accepted']).exists():
                # Account purposes can legitimately recur after completed acceptance.
                if application or notification or target.filter(state='reserved').exists():
                    raise DeliveryError('Delivery is already pending or accepted.')
            unknown = target.filter(state='unknown')
            if unknown.exists():
                # No reconciliation operation or schema marker is authorized yet.
                # A warning alone cannot safely resolve durable unknown receipts.
                raise DeliveryError('Unknown delivery requires reconciliation before manual retry.')
            if retry_of is not None:
                previous = target.filter(pk=retry_of, state='definite_failure').first()
                if previous is None:
                    raise DeliveryError('Retry requires a definite-failure receipt.')
                if channel == 'alert':
                    raise DeliveryError('Alert retry bounds need approval; no automatic retry.')
            elif target.filter(state='definite_failure').exists():
                raise DeliveryError('Retry must name its definite-failure receipt.')
            budgets = Budget.objects.filter(scope='global', day=day).annotate(
                total=F('application_reserved') + F('account_reserved') + F('alert_reserved'))
            # One atomic shared total, including earlier non-pilot attempts that day.
            limit = min(self.policy.total, self.pilot.limit) if self.pilot else self.policy.total
            if not budgets.filter(total__lt=limit, **{counter+'__lt': cap}).update(**{counter: F(counter)+1}):
                raise QuotaExceeded('Daily platform allocation reached; keep the draft and try next Nairobi day.')
            if channel == 'application':
                scope = f'user:{user.pk}'
                Budget.objects.bulk_create([Budget(scope=scope, day=day)], ignore_conflicts=True)
                if not Budget.objects.filter(scope=scope, day=day,
                    application_reserved__lt=self.policy.per_user_applications).update(application_reserved=F('application_reserved')+1):
                    raise QuotaExceeded('Daily user application limit reached; keep the draft.')
            attempt = Attempt(user=user, channel=channel, recipient_digest=digest,
                application=application, notification=notification, idempotency_key=key)
            attempt.full_clean()
            attempt.save(force_insert=True)
            return attempt, True
