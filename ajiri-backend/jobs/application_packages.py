"""Owner-scoped, append-only document drafting. No approval or delivery here.

see docs/CONCEPTS.md#application-package-editor
"""
from datetime import datetime
import hashlib
from io import BytesIO

from docx import Document
from docx.shared import Pt
from django.core.files.base import ContentFile
from django.db import OperationalError, transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException

from profiles.cv_builder import content_hash, document_bytes, CVUnavailable
from profiles.cv_validation import MAX_DOCUMENT_BYTES
from profiles.models import CVApproval
from .models import Application, ApplicationPackage, ApplicationSendAuthorization

TEMPLATE_VERSION = 'application-letter-v1'


class PackageConflict(APIException):
    status_code = 409
    default_detail = 'The application changed or cannot be edited. Reload its revisions before continuing.'


def blocked(application):
    return (application.status not in (Application.Status.DRAFT, Application.Status.READY_FOR_REVIEW)
            or application.delivery_attempts.filter(channel='application',
                state__in=['reserved', 'unknown', 'accepted']).exists())


def context(application):
    job = application.job
    # Plain text only, bounded and allowlisted; never fetch source URLs or execute job instructions.
    limits = {'title': 255, 'company_name': 255, 'description': 12000, 'requirements': 6000}
    result = {key: getattr(job, key)[:limit] for key, limit in limits.items()}
    result.update(application_method=application.application_method,
                  application_email=application.application_email,
                  truncated=any(len(getattr(job, key)) > limit for key, limit in limits.items()))
    return result


def require_editable(application):
    if blocked(application) or application.job.is_flagged_scam:
        raise PackageConflict()
    if not application.job.is_active:
        # Only the separately enabled, exact owner synthetic pilot can prepare an
        # inactive job. Keeping it inactive excludes it from browsing/match sweeps.
        from .application_dispatch import editable_pilot
        if not editable_pilot(application):
            raise PackageConflict()


def is_editable(application):
    try:
        require_editable(application)
        return True
    except PackageConflict:
        return False


def selected_cv(user, version):
    return get_object_or_404(CVApproval, pk=version, profile__user=user)


def draft_letter(approval, job_context):
    """Deterministic neutral draft from approved content, never inferred qualifications."""
    content = approval.content
    name = content.get('contact', {}).get('name', '')
    summary = content.get('summary', '')
    skills = ', '.join(content.get('skills', []))
    paragraphs = [f"Dear Hiring Manager at {job_context['company_name']},",
        f"I am applying for the {job_context['title']} position.", summary]
    if skills:
        paragraphs.append(f'Skills listed in my selected CV: {skills}.')
    paragraphs.extend(['Thank you for considering my application.', 'Kind regards,', name])
    return '\n\n'.join(value for value in paragraphs if value)


def render_letter(text):
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    doc.core_properties.author = ''
    doc.core_properties.last_modified_by = ''
    doc.core_properties.created = doc.core_properties.modified = datetime(2000, 1, 1)
    for paragraph in text.split('\n'):
        doc.add_paragraph(paragraph)
    buffer = BytesIO()
    doc.save(buffer)
    data = buffer.getvalue()
    if len(data) > MAX_DOCUMENT_BYTES:
        raise CVUnavailable('The letter is too large. Shorten it before saving.')
    return data


def package_data(package):
    # Paths and owner identities stay private. Reading never generates documents.
    return {'id': str(package.pk), 'revision': package.revision,
        'cv_version': str(package.cv_approval_id), 'job_context': package.job_snapshot,
        'letter_text': package.letter_text, 'email_subject': package.email_subject,
        'email_body': package.email_body, 'content_sha256': package.content_sha256,
        'template_version': package.template_version, 'created_at': package.created_at}


def package_fingerprint(package):
    return content_hash({'job': package.job_snapshot, 'cv_version': str(package.cv_approval_id),
        'cv_sha256': package.cv_sha256, 'letter_sha256': package.letter_sha256,
        'letter_text': package.letter_text, 'email_subject': package.email_subject,
        'email_body': package.email_body, 'template_version': package.template_version})


def save_package(user, application_id, data):
    application = get_object_or_404(Application.objects.select_related('job'), pk=application_id, user=user)
    require_editable(application)
    approval = selected_cv(user, data['cv_version'])
    cv = document_bytes(approval)
    letter = render_letter(data['letter_text'])
    displayed = context(application)
    if content_hash(displayed) != data['context_sha256']:
        raise PackageConflict('Job context changed. Reload it and review before saving.')
    package = ApplicationPackage(application=application, revision=data['expected_revision'] + 1,
        cv_approval=approval, job_snapshot=displayed, letter_text=data['letter_text'],
        email_subject=data['email_subject'], email_body=data['email_body'],
        cv_sha256=hashlib.sha256(cv).hexdigest(), letter_sha256=hashlib.sha256(letter).hexdigest(),
        cv_size=len(cv), letter_size=len(letter), template_version=TEMPLATE_VERSION)
    package.content_sha256 = package_fingerprint(package)
    written = []
    try:
        for field, payload in [(package.cv_document, cv), (package.letter_document, letter)]:
            field.save('document.docx', ContentFile(payload), save=False)
            written.append((field.storage, field.name))
        with transaction.atomic():
            # SQLite needs a WRITE before reads; select_for_update alone does not serialize writers.
            matched = Application.objects.filter(pk=application_id, user=user,
                status__in=['draft', 'ready_for_review']).update(status=F('status'))
            if not matched:
                raise PackageConflict()
            current = Application.objects.select_related('job').get(pk=application_id)
            require_editable(current)
            latest = current.packages.order_by('-revision').values_list('revision', flat=True).first() or 0
            if latest != data['expected_revision'] or context(current) != displayed:
                raise PackageConflict()
            if not CVApproval.objects.filter(pk=approval.pk, profile__user=user).exists():
                raise PackageConflict()
            package.save(force_insert=True)
            ApplicationSendAuthorization.objects.filter(application=current, state='authorized').update(
                state='superseded', closed_at=timezone.now())
        return package
    except Exception as error:
        # Only files staged by this request can be removed; crash orphans require report-only review.
        for storage, name in written:
            try:
                storage.delete(name)
            except OSError:
                pass
        if isinstance(error, OperationalError) and 'locked' in str(error).lower():
            # Shared-cache SQLite can reject rather than wait. No automatic mutation retry.
            raise PackageConflict('The application is busy. Reload saved revisions before another save.') from None
        raise
