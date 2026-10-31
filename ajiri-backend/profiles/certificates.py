"""Private quarantine lifecycle; no provider, public URLs or employer sharing.

see docs/CONCEPTS.md#private-certificate-evidence
"""
import hashlib
import re
from datetime import timedelta
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import CommandError
from django.db import transaction
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .cv_builder import CVConflict, CVUnavailable
from .models import CertificateEvidence, CVWorkspace, certificate_path
from .upload_validation import MAX_BYTES, validate_cv_upload
from jobs.management.commands.backup_private_data import no_links


def metadata(row):
    return {'id': row.pk, 'certification_id': row.certification_id, 'sha256': row.sha256,
        'size_bytes': row.size_bytes, 'scan_state': row.scan_state, 'created_at': row.created_at,
        'qualification_verified': False}


def claim(profile, expected_revision):
    # FIRST database operation is a conditional write: also serializes SQLite quota checks.
    if CVWorkspace.objects.filter(profile=profile, revision=expected_revision).update(revision=F('revision')) != 1:
        raise CVConflict()
    return CVWorkspace.objects.get(profile=profile)


def put(profile, certification_id, expected_revision, upload, *, expected_id=None, expected_hash=''):
    if PurePosixPath(upload.name).suffix.lower() != '.pdf':
        raise ValidationError({'document': ['Certificate evidence supports PDF only.']})
    validate_cv_upload(upload, scan=False)  # Persist private quarantine; explicit scanner claims this exact row later.
    upload.seek(0)
    data = upload.read(MAX_BYTES+1)
    if not data or len(data) != upload.size or len(data) > MAX_BYTES:
        raise ValidationError({'document': ['Invalid bounded PDF bytes.']})
    name = None
    try:
        # Stage a fresh private UUID; a crash leaves an orphan, never a public file.
        name = default_storage.save(certificate_path(None, ''), ContentFile(data))
        with transaction.atomic():
            workspace = claim(profile, expected_revision)
            if str(certification_id) not in {str(row['id']) for row in workspace.content.get('certifications', [])}:
                raise ValidationError({'certification_id': ['Save this certification in your current CV first.']})
            existing = CertificateEvidence.objects.filter(profile=profile, certification_id=certification_id).first()
            if ((existing is None and (expected_id is not None or expected_hash))
                    or (existing is not None and (existing.pk != expected_id or existing.sha256 != expected_hash))):
                raise CVConflict()
            others = CertificateEvidence.objects.filter(profile=profile)
            if existing:
                others = others.exclude(pk=existing.pk)
            if others.count() >= 5 or (others.aggregate(total=Sum('size_bytes'))['total'] or 0)+len(data) > 20*1024*1024:
                raise ValidationError({'document': ['Certificate quota is five files and 20 MiB per owner.']})
            if existing:
                existing.delete()  # Signal removes old bytes only after this transaction commits.
            row = CertificateEvidence.objects.create(profile=profile, certification_id=certification_id,
                document=name, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        return row
    except Exception:
        if name:
            default_storage.delete(name)  # Only the new UUID owned by this failed request.
        raise


def remove(profile, certification_id, expected_revision, expected_id, expected_hash):
    with transaction.atomic():
        claim(profile, expected_revision)
        row = get_object_or_404(CertificateEvidence, profile=profile, certification_id=certification_id)
        if row.pk != expected_id or row.sha256 != expected_hash:
            raise CVConflict()
        row.delete()


def private_bytes(row):
    if (not 1 <= row.size_bytes <= MAX_BYTES
            or not re.fullmatch(r'quarantine/certificates/[a-f0-9]{32}\.pdf', row.document.name)):
        raise CVUnavailable()
    try:
        try:
            from pathlib import Path
            path = Path(row.document.path)
            no_links(path)
            if not path.is_file() or path.stat().st_nlink != 1:
                raise CVUnavailable()
        except NotImplementedError:
            pass  # Remote private storage must supply its own non-link object semantics.
        with row.document.open('rb') as stream:
            data = stream.read(MAX_BYTES+1)
        if len(data) != row.size_bytes or hashlib.sha256(data).hexdigest() != row.sha256:
            raise CVUnavailable()
        return data
    except (OSError, ValueError, CommandError):
        raise CVUnavailable() from None


def downloadable(row):
    from .scanner import result_current
    now = timezone.now()
    if (row.scan_state != 'clean' or not row.scan_version or row.scanned_at is None
            or not now-timedelta(hours=24) <= row.scanned_at <= now
            or not result_current(row.scan_version, row.scanned_at)):
        raise CVConflict('This evidence is quarantined until a current clean malware scan is available.')
    data = private_bytes(row)
    if not CertificateEvidence.objects.filter(pk=row.pk, profile=row.profile, sha256=row.sha256,
            scan_state='clean', scanned_at=row.scanned_at).exists():
        raise CVConflict()
    return data
