"""Exact-address consent; legacy preferences never establish permission to send."""
import uuid
from django.core import signing
from django.db import transaction
from django.utils.crypto import salted_hmac
from .models import Profile, AlertConsentEvent

POLICY = 'job-alert-email-v1'
SALT = 'ajiri.alert-unsubscribe.v1'


def recipient_digest(email):
    return salted_hmac('ajiri.alert-consent.v1', email.casefold(), algorithm='sha256').hexdigest()


def eligible(profile):
    # see docs/CONCEPTS.md#explicit-alert-consent
    user = profile.user
    event = profile.alert_consent_events.order_by('-pk').first()
    return bool(user.is_active and profile.notify_email and profile.email_verified_at
                and profile.verified_email.casefold() == user.email.casefold()
                and event and event.enabled and event.policy_version == POLICY
                and event.recipient_digest == recipient_digest(user.email))


def record_choice(user, enabled, decision_id, *, source='in_app'):
    with transaction.atomic():
        # Acquire SQLite's writer slot before reading evidence; unsubscribe and save serialize.
        Profile.objects.filter(user=user).update(notify_email=enabled)
        profile = Profile.objects.select_related('user').get(user=user)
        existing = AlertConsentEvent.objects.filter(decision_id=decision_id).first()
        digest = recipient_digest(profile.user.email)
        if existing:
            if (existing.profile_id != profile.pk or existing.enabled != enabled
                    or existing.policy_version != POLICY or existing.recipient_digest != digest
                    or existing.source != source):
                raise ValueError('Decision key was already used for another choice.')
            # An old retry cannot reverse a newer unsubscribe or opt-in.
            latest = profile.alert_consent_events.order_by('-pk').first()
            Profile.objects.filter(pk=profile.pk).update(notify_email=latest.enabled)
            return profile
        AlertConsentEvent.objects.create(profile=profile, decision_id=decision_id, enabled=enabled,
            policy_version=POLICY, recipient_digest=digest, source=source)
        return profile


def unsubscribe_token(profile):
    return signing.dumps({'profile': profile.pk, 'recipient': recipient_digest(profile.user.email)}, salt=SALT)


def unsubscribe(token, *, confirm=False):
    try:
        payload = signing.loads(token, salt=SALT, max_age=30 * 24 * 60 * 60)
        with transaction.atomic():
            # No effect for link previews. Confirmation locks before reading current identity.
            if confirm:
                Profile.objects.filter(pk=payload['profile']).update(notify_email=False)
            profile = Profile.objects.select_related('user').get(pk=payload['profile'])
            if payload['recipient'] != recipient_digest(profile.user.email):
                raise ValueError('Invalid unsubscribe link.')
            if confirm:
                latest = profile.alert_consent_events.order_by('-pk').first()
                if latest is None or latest.enabled:
                    record_choice(profile.user, False, uuid.uuid4(), source='unsubscribe')
            return True
    except (signing.BadSignature, KeyError, TypeError, Profile.DoesNotExist):
        raise ValueError('Invalid or expired unsubscribe link.') from None
