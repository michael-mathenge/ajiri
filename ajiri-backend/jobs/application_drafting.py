"""Copy an explicitly selected approved CV; never regenerate it from Profile.

see docs/CONCEPTS.md#approved-cv-applications
"""
import uuid
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from profiles.cv_builder import document_bytes, CVUnavailable
from profiles.cv_validation import MAX_DOCUMENT_BYTES
from .cover_letter_generator import generate_cover_letter_docx
from .models import Application, Job


def prepare_application(user, job, approval):
    cv = document_bytes(approval)
    letter = generate_cover_letter_docx(user.profile, job).getvalue()
    if len(letter) > MAX_DOCUMENT_BYTES:
        raise CVUnavailable('The application document is too large. Please shorten your profile summary.')
    application = Application(user=user, job=job, status=Application.Status.READY_FOR_REVIEW,
        application_method=job.application_method, application_email=job.application_email)
    if job.application_method == Job.ApplicationMethod.EMAIL:
        applicant_name = user.full_name or user.email
        application.email_subject = f'Application for {job.title} position'
        application.email_body = (
            f'Dear Hiring Manager,\n\nPlease find attached my CV and cover letter for the '
            f'{job.title} position at {job.company_name}.\n\nKind regards,\n{applicant_name}')
    written = []
    try:
        token = uuid.uuid4().hex
        for field, filename, data in [
            (application.generated_cv, f'{token}_CV.docx', cv),
            (application.generated_cover_letter, f'{token}_Cover_Letter.docx', letter),
        ]:
            field.save(filename, ContentFile(data), save=False)
            written.append((field.storage, field.name))
        try:
            with transaction.atomic():
                application.save(force_insert=True)
        except IntegrityError:
            # Another request may have won the user/job uniqueness constraint.
            existing = Application.objects.filter(user=user, job=job).first()
            if not existing:
                raise
            for storage, name in written:
                storage.delete(name)
            return existing, False
        return application, True
    except Exception:
        for storage, name in written:
            try:
                storage.delete(name)
            except OSError:
                pass  # Private report-only orphan review; never leak paths.
        raise
