"""Opt-in synthetic owner application pilot; normal employer delivery stays closed.

see docs/CONCEPTS.md#managed-application-pilot
"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils.crypto import salted_hmac

from accounts import pilot as account_pilot
from profiles.models import Profile
from .application_pilot import ApplicationPilot, ApplicationPilotTransport
from .brevo_transport import BrevoTransport, Result
from .delivery_service import DeliveryService, DeliveryError
from .models import Application
from .application_packages import PackageConflict
from .send_authorization import address, dispatch_inputs, linked_attempt, DISABLED

SOURCE = 'ajiri-owner-application-pilot'
LIMIT_REVIEW = 'brevo-api-attachments-2026-10-22'
DISCLAIMER = 'Synthetic owner-only application test. No employer is being contacted.'
MAX_REQUEST = 6 * 1024 * 1024


def configuration():
    # Do not inspect provider configuration/credentials while this route is off.
    if not getattr(settings, 'APPLICATION_EMAIL_ENABLED', False):
        return None
    if getattr(settings, 'APPLICATION_PILOT_LIMIT_REVIEW', '') != LIMIT_REVIEW:
        return None
    try:
        account = account_pilot.configuration()
        if account is None or account.limit != 5:
            return None
        policy = ApplicationPilot(account.owner_id, account.recipient, account.recipient,
            address(account.sender), MAX_REQUEST, LIMIT_REVIEW)
        return policy, account.timeout
    except (ImproperlyConfigured, ValueError, TypeError):
        return None


def owner_job(user, application, policy):
    try:
        job = application.job
        return (user.is_active and user.pk == policy.owner_id
            and address(user.email) == policy.recipient
            and Profile.objects.filter(user_id=user.pk, email_verified_at__isnull=False,
                verified_email__iexact=policy.recipient).exists()
            and application.user_id == user.pk and application.status == 'ready_for_review'
            and application.application_method == 'email'
            and address(application.application_email) == policy.recipient
            and job.application_method == 'email' and address(job.application_email) == policy.recipient
            and job.source_name == SOURCE
            and job.source_url.startswith(f'https://example.invalid/{SOURCE}/{policy.owner_id}/')
            and job.title == 'Ajiri synthetic application pilot' and job.company_name == 'Synthetic example'
            and not job.is_active and not job.is_flagged_scam)
    except (ObjectDoesNotExist, ValueError, TypeError, PackageConflict):
        return False


def editable_pilot(application):
    configured = configuration()
    return bool(configured and owner_job(application.user, application, configured[0]))


def allowed(user, application, plan, policy):
    return (isinstance(plan, dict) and owner_job(user, application, policy)
        and plan.get('subject', '').startswith('[AJIRI PILOT] ')
        and plan.get('body', '').startswith(DISCLAIMER)
        and plan.get('recipient') == policy.recipient and plan.get('reply_to') == policy.reply_to
        and plan.get('sender') == policy.sender and plan.get('copy_to_self') is False)


def dispatch_status(user, application, plan):
    configured = configuration()
    enabled = bool(configured and allowed(user, application, plan, configured[0]))
    return {'dispatch_enabled': enabled, 'disabled_reason': '' if enabled else DISABLED}


def dispatch(user, authorization):
    # Durable receipt reconciliation comes first, including after the pilot is off.
    authorization, existing = linked_attempt(user.pk, authorization.application_id,
        authorization.pk, authorization.pk)
    if existing is not None:
        return existing
    configured = configuration()
    application = Application.objects.select_related('job').get(pk=authorization.application_id, user=user)
    if not configured or not allowed(user, application, authorization.plan, configured[0]):
        raise DeliveryError(DISABLED)
    policy, timeout = configured
    inputs = dispatch_inputs(user, authorization)

    def still_approved(expected):
        current = configuration()
        try:
            fresh = Application.objects.select_related('job', 'user__profile').get(pk=application.pk)
            return bool(current and current[0] == expected
                and allowed(fresh.user, fresh, authorization.plan, expected))
        except Application.DoesNotExist:
            return False

    class FinalBoundary(ApplicationPilotTransport):
        def send(self, payload):
            if not still_approved(self.policy):
                return Result('definite_failure', failure_category='configuration')
            return super().send(payload)

    transport = FinalBoundary(policy, BrevoTransport(settings.BREVO_API_KEY, policy.sender,
        timeout=timeout, sender_name='Ajiri'), still_approved=still_approved)
    key = salted_hmac('ajiri.account-recipient-digest.v1', 'delivery-accounting', algorithm='sha256').digest()
    return DeliveryService(transport, digest_key=key, enabled=True, pilot=policy).deliver(
        user_id=user.pk, channel='application', application_id=application.pk,
        authorization_id=authorization.pk, idempotency_key=authorization.pk,
        retry_of=authorization.retry_of_id, **inputs)
