"""Synthetic approved CV fixture, never used by application runtime."""
from django.core.files.base import ContentFile
import hashlib
from .cv_builder import content_hash, render_docx, TEMPLATE_VERSION
from .cv_validation import validate_content
from .models import CVApproval


def approved_cv(user, revision=1):
    content = validate_content({'schema_version': 1, 'contact': {'name': 'Test Applicant'}, 'summary': 'Synthetic CV.'}, for_approval=True)
    data = render_docx(content)
    approval = CVApproval(profile=user.profile, revision=revision, content=content,
        content_sha256=content_hash(content), template_version=TEMPLATE_VERSION, document_sha256=hashlib.sha256(data).hexdigest())
    approval.document.save('test.docx', ContentFile(data), save=False)
    approval.save()
    return approval
