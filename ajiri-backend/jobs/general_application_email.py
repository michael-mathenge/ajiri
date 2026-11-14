"""Default-off application handoff from an exact immutable authorization.

see docs/CONCEPTS.md#general-application-email
"""
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import salted_hmac

from accounts.general_email import configuration
from profiles.cv_builder import content_hash
from .application_packages import context, PackageConflict
from .brevo_transport import BrevoTransport, Result
from .delivery_service import DeliveryError, DeliveryService
from .freshness import job_is_eligible
from .models import Application, ApplicationSendAuthorization
from .package_review import approval_data, verified_documents, PackageUnavailable
from .send_authorization import address, dispatch_inputs, POLICY, ATTACHMENTS, MAX_RAW


def enabled():
    return (getattr(settings, 'GENERAL_APPLICATION_EMAIL_ENABLED', False)
            and settings.APPLICATION_EMAIL_ENABLED and settings.JOB_FRESHNESS_ENFORCED
            and configuration() is not None)


def allowed(user, application, plan):
    if not enabled():
        return False
    try:
        profile = user.profile
        return (user.is_active and application.user_id == user.pk
            and application.status == 'ready_for_review' and job_is_eligible(application.job)
            and application.application_method == application.job.application_method == 'email'
            and address(application.application_email) == address(application.job.application_email)
            and profile.email_verified_at is not None and address(profile.verified_email) == address(user.email)
            and plan['recipient'] == address(application.application_email)
            and plan['reply_to'] == address(user.email) and plan['sender'] == configuration().sender.casefold()
            and plan['sender_name'] == 'Ajiri' and plan['copy_to_self'] is False
            and plan['policy_version'] == POLICY and plan['attachment_policy'] == ATTACHMENTS)
    except (KeyError, TypeError, PackageConflict):
        return False


class AuthorizedTransport:
    def __init__(self, authorization):
        self.identity = authorization.pk
        self.policy = configuration()
        self.plan = authorization.plan
        self.payload = None
        self.transport = BrevoTransport(settings.BREVO_API_KEY, self.policy.sender.casefold(),
            timeout=self.policy.timeout, sender_name='Ajiri')

    def prepare(self, **kwargs):
        self.payload = self.transport.prepare(**kwargs)
        return self.payload

    def send(self, payload):
        # The ledger has already claimed the cutoff. Verify the same plan and bytes
        # without reopening authorization or resetting a possibly ambiguous receipt.
        auth = ApplicationSendAuthorization.objects.select_related(
            'owner__profile', 'application__job', 'document_approval__package__cv_approval__profile__user').get(pk=self.identity)
        try:
            package = auth.document_approval.package
            if (not enabled() or configuration() != self.policy or auth.state != 'dispatch_started'
                    or auth.expires_at <= timezone.now() or auth.policy_version != POLICY or auth.plan != self.plan
                    or content_hash(auth.plan) != auth.plan_sha256
                    or not allowed(auth.owner, auth.application, auth.plan)
                    or package.job_snapshot != context(auth.application)
                    or auth.application.packages.order_by('-revision').values_list('pk', flat=True).first() != package.pk
                    or approval_data(package) is None or payload != self.payload):
                return Result('definite_failure', failure_category='configuration')
            documents = verified_documents(package)
            expected = self.transport.prepare(recipient=self.plan['recipient'], subject=self.plan['subject'],
                text=self.plan['body'], reply_to=self.plan['reply_to'], max_attachment_bytes=MAX_RAW,
                attachments=tuple((item['filename'], documents[item['role']]) for item in self.plan['attachments']))
            if payload != expected:
                return Result('definite_failure', failure_category='configuration')
        except (KeyError, TypeError, PackageConflict, PackageUnavailable):
            return Result('definite_failure', failure_category='configuration')
        return self.transport.send(payload)


def dispatch(user, authorization):
    application = Application.objects.select_related('job').get(pk=authorization.application_id, user=user)
    if not allowed(user, application, authorization.plan):
        raise DeliveryError('General application delivery is disabled or ineligible.')
    inputs = dispatch_inputs(user, authorization)
    key = salted_hmac('ajiri.account-recipient-digest.v1', 'delivery-accounting', algorithm='sha256').digest()
    return DeliveryService(AuthorizedTransport(authorization), digest_key=key, enabled=True).deliver(
        user_id=user.pk, channel='application', application_id=application.pk,
        authorization_id=authorization.pk, idempotency_key=authorization.pk,
        retry_of=authorization.retry_of_id, **inputs)
