"""Private, immutable per-application permission; no credentials or provider I/O.

see docs/CONCEPTS.md#application-send-authorization
"""
from datetime import timedelta
import json
import re
import unicodedata

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from profiles.cv_builder import content_hash
from profiles.models import Profile
from .application_packages import context, require_editable, PackageConflict
from .brevo_transport import BrevoTransport
from .models import (Application, ApplicationSendAuthorization as Authorization,
                     ApplicationSendAttemptLink as Link, DeliveryAttempt)
from .package_review import approval_data, verified_documents, PackageUnavailable

POLICY = 'application-send-v1'
ATTACHMENTS = 'application-docx-v1'
MAX_RAW = 4 * 1024 * 1024
MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
DISABLED = 'Application email sending is disabled pending final release and pilot approval.'


def address(value):
    try:
        if not isinstance(value, str) or value != value.strip() or any(ord(c) < 32 for c in value) or '*' in value:
            raise ValueError
        validate_email(value)
        return value.casefold()
    except (ValueError, ValidationError):
        raise PackageConflict('A valid exact email address is required.') from None


def component(value, fallback):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    value = re.sub(r'\s+', '_', value)
    value = re.sub(r'[^A-Za-z0-9_-]', '', value)
    return re.sub('_+', '_', value).strip('_-')[:40] or fallback


def latest_package(application):
    package = application.packages.select_related('cv_approval__profile__user').order_by('-revision').first()
    if package is None or approval_data(package) is None:
        raise PackageConflict('Approve the latest saved documents first.')
    return package


def retry_allowed(application, retry_of):
    attempts = application.delivery_attempts.filter(channel='application')
    if attempts.filter(state__in=['reserved', 'unknown', 'accepted']).exists():
        raise PackageConflict('Delivery is pending, unknown or accepted; reconcile its receipt without resending.')
    failures = attempts.filter(state='definite_failure')
    if retry_of is None:
        if failures.exists():
            raise PackageConflict('An explicit retry must name the definite-failure receipt.')
    elif (failures.count() != 1 or not failures.filter(pk=retry_of).exists()
          or Link.objects.filter(previous_attempt_id=retry_of).exists()
          or Link.objects.filter(attempt_id=retry_of, previous_attempt__isnull=False).exists()):
        raise PackageConflict('Only one explicit retry of the initial definite failure is allowed.')


def build_plan(user, application, *, retry_of=None):
    require_editable(application)
    if (not user.is_active or application.application_method != 'email'
        or application.job.application_method != 'email'
        or address(application.job.application_email) != address(application.application_email)):
        raise PackageConflict('The saved application destination no longer matches the job.')
    profile = Profile.objects.get(user=user)
    if not profile.email_verified_at or address(profile.verified_email) != address(user.email):
        raise PackageConflict('Verify your current account email before authorizing an application.')
    retry_allowed(application, retry_of)
    package = latest_package(application)
    if package.job_snapshot != context(application):
        raise PackageConflict('Job context changed. Save and approve a new package first.')
    documents = verified_documents(package)
    subject, body = package.email_subject, package.email_body
    if not subject.strip() or not body.strip() or any(ord(c) < 32 or ord(c) == 127 for c in subject):
        raise PackageConflict('Save a nonempty email subject and body without header controls.')
    sender = address(getattr(settings, 'EMAIL_PLATFORM_FROM', ''))
    name = component(user.full_name, 'Applicant')
    company = component(application.job.company_name, 'Company')
    descriptors = []
    for role, label, digest, size in [('cv', 'CV', package.cv_sha256, package.cv_size),
                                    ('cover-letter', 'Cover_Letter', package.letter_sha256, package.letter_size)]:
        descriptors.append({'role': role, 'mime': MIME, 'filename': f'{name}_{label}_{company}.docx',
                            'size': size, 'sha256': digest})
    plan = {'schema_version': 1, 'application_id': application.pk, 'job_id': application.job_id, 'owner_id': user.pk,
        'package_id': str(package.pk), 'revision': package.revision, 'content_sha256': package.content_sha256,
        'document_approval_id': package.approval.pk, 'document_policy': package.approval.policy_version,
        'recipient': address(application.application_email), 'reply_to': address(user.email),
        'applicant_name': user.full_name,
        'sender': sender, 'sender_name': 'Ajiri', 'subject': subject, 'body': body,
        'attachments': descriptors, 'copy_to_self': False, 'policy_version': POLICY,
        'attachment_policy': ATTACHMENTS, 'retry_of': str(retry_of) if retry_of else None}
    if len(json.dumps(plan, ensure_ascii=True).encode('utf-8')) > 65536:
        raise PackageConflict('The email plan is too large. Shorten its text.')
    return plan, documents


def plan_response(user, application, retry_of=None):
    plan, _ = build_plan(user, application, retry_of=retry_of)
    from .application_dispatch import dispatch_status
    return {'plan': plan, 'plan_sha256': content_hash(plan), 'expires_after_hours': 24,
            **dispatch_status(user, application, plan)}


def owner_authorization(user, application_id, authorization_id):
    return get_object_or_404(Authorization, pk=authorization_id, application_id=application_id,
                             owner=user, application__user=user)


def receipt_data(attempt):
    return {'id': str(attempt.pk), 'state': attempt.state,
            'failure_category': attempt.failure_category, 'created_at': attempt.created_at}


def checked_link(authorization):
    # Read receipt and cutoff in ONE SQL snapshot; an earlier authorization object
    # can predate another request's committed handoff.
    link = Link.objects.select_related('attempt', 'authorization').filter(authorization=authorization).first()
    if link:
        attempt = link.attempt
        if (link.authorization.state != 'dispatch_started' or attempt.user_id != authorization.owner_id
            or attempt.application_id != authorization.application_id or attempt.notification_id is not None
            or attempt.channel != 'application' or attempt.idempotency_key != authorization.pk
            or link.previous_attempt_id != authorization.retry_of_id):
            raise PackageUnavailable('Delivery evidence needs private operator reconciliation.')
    return link


def authorization_data(authorization):
    link = checked_link(authorization)
    if link:
        authorization = link.authorization
    effective = ('expired' if authorization.state == 'authorized'
                 and authorization.expires_at <= timezone.now() else authorization.state)
    return {'id': str(authorization.pk), 'request_key': str(authorization.request_key),
        'plan': authorization.plan, 'plan_sha256': authorization.plan_sha256,
        'state': effective, 'authorized_at': authorization.authorized_at,
        'expires_at': authorization.expires_at, 'closed_at': authorization.closed_at,
        'attempt': receipt_data(link.attempt) if link else None,
        **_authorization_dispatch_status(authorization)}


def _authorization_dispatch_status(authorization):
    if authorization.state != 'authorized' or authorization.expires_at <= timezone.now():
        return {'dispatch_enabled': False, 'disabled_reason': 'This authorization is closed or expired.'}
    from .application_dispatch import dispatch_status
    return dispatch_status(authorization.owner, authorization.application, authorization.plan)


def claim_application(user, application_id):
    # Same first-write ordering as package saves: withdrawal/save/dispatch have one cutoff.
    if not Application.objects.filter(pk=application_id, user=user).update(status=F('status')):
        get_object_or_404(Application, pk=application_id, user=user)
    return Application.objects.select_related('job').get(pk=application_id, user=user)


def authorize(user, application_id, data):
    if data.get('authorization') is not True:
        raise PackageConflict('Explicit authorization of this exact application is required.')
    with transaction.atomic():
        application = claim_application(user, application_id)
        existing = Authorization.objects.filter(request_key=data['request_key']).first()
        if existing:
            if existing.owner_id != user.pk or existing.application_id != application_id:
                get_object_or_404(Authorization.objects.none())
            if (existing.plan_sha256 != data['plan_sha256']
                or existing.plan['package_id'] != str(data['package_id'])
                or existing.plan['revision'] != data['expected_revision']
                or existing.retry_of_id != data.get('retry_of')):
                raise PackageConflict('This request key already belongs to a different plan.')
            return existing, False
        plan, _ = build_plan(user, application, retry_of=data.get('retry_of'))
        if (content_hash(plan) != data['plan_sha256'] or plan['package_id'] != str(data['package_id'])
            or plan['revision'] != data['expected_revision']):
            raise PackageConflict('The send plan changed. Review it again before authorizing.')
        now = timezone.now()
        Authorization.objects.filter(application=application, state='authorized', expires_at__lte=now).update(
            state='expired', closed_at=now)
        if Authorization.objects.filter(application=application, state='authorized').exists():
            raise PackageConflict('An active authorization exists. Reconcile or withdraw it first.')
        return Authorization.objects.create(request_key=data['request_key'], application=application,
            owner=user, document_approval=latest_package(application).approval, plan=plan,
            plan_sha256=content_hash(plan), policy_version=POLICY, authorized_at=now,
            expires_at=now + timedelta(hours=24), retry_of_id=data.get('retry_of')), True


def withdraw(user, application_id, authorization_id):
    with transaction.atomic():
        claim_application(user, application_id)
        authorization = owner_authorization(user, application_id, authorization_id)
        if authorization.state == 'dispatch_started':
            raise PackageConflict('Sending has started or may have started; cancellation cannot be guaranteed.')
        if authorization.state == 'authorized':
            authorization.state = 'expired' if authorization.expires_at <= timezone.now() else 'withdrawn'
            authorization.closed_at = timezone.now()
            authorization.save(update_fields=['state', 'closed_at'])
        return authorization


def dispatch_inputs(user, authorization):
    if (authorization.state != 'authorized' or authorization.expires_at <= timezone.now()
        or authorization.policy_version != POLICY or content_hash(authorization.plan) != authorization.plan_sha256):
        raise PackageConflict('Authorization is closed, expired or changed. Review a new plan.')
    application = Application.objects.select_related('job').get(pk=authorization.application_id, user=user)
    plan, documents = build_plan(user, application, retry_of=authorization.retry_of_id)
    if (plan != authorization.plan or latest_package(application).approval.pk != authorization.document_approval_id):
        raise PackageConflict('The authorized plan no longer matches the current application.')
    attachments = tuple((row['filename'], documents[row['role']]) for row in plan['attachments'])
    return {'recipient': plan['recipient'], 'subject': plan['subject'], 'text': plan['body'],
            'attachments': attachments, 'max_attachment_bytes': MAX_RAW}


def validate_payload(user, authorization, payload):
    inputs = dispatch_inputs(user, authorization)
    # Pure serialization only. Comparing the entire payload forbids CC/BCC and substituted bytes.
    expected = BrevoTransport('not-a-credential', authorization.plan['sender'], sender_name='Ajiri').prepare(
        **inputs, reply_to=authorization.plan['reply_to'])
    if payload != expected:
        raise PackageConflict('The prepared message does not match the authorized plan.')


def linked_attempt(user_id, application_id, authorization_id, key):
    authorization = get_object_or_404(Authorization, pk=authorization_id, owner_id=user_id,
                                     application_id=application_id, application__user_id=user_id)
    if str(authorization.pk) != str(key):
        raise PackageConflict('Dispatch identity does not match authorization.')
    link = checked_link(authorization)
    return authorization, link.attempt if link else None
