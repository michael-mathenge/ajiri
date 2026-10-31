from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .certificates import private_bytes
from .cv_builder import CVUnavailable
from .models import CertificateEvidence
from .scanner import Verdict, enabled, scan_bytes


def scan_certificate(identity, *, recover_stalled=False):
    # see docs/CONCEPTS.md#local-malware-scanning
    if not enabled():
        return False
    started = timezone.now()
    with transaction.atomic():
        rows = CertificateEvidence.objects.filter(pk=identity)
        allowed = rows.exclude(scan_state='scanning')
        if recover_stalled:
            allowed = allowed | rows.filter(scan_state='scanning', scanned_at__lt=started-timedelta(minutes=1))
        if allowed.update(scan_state='scanning', scanned_at=started, scan_version='') != 1:
            return False
        row = CertificateEvidence.objects.get(pk=identity)
    try:
        result = scan_bytes(private_bytes(row))
    except CVUnavailable:
        result = Verdict('unavailable', row.sha256)
    state = result.state if result.sha256 == row.sha256 else 'unavailable'
    # Replacement/deletion and a later explicit recovery invalidate this claim.
    return CertificateEvidence.objects.filter(pk=identity, sha256=row.sha256, document=row.document.name,
        scan_state='scanning', scanned_at=started).update(scan_state=state,
        scan_version=result.version if state in ('clean', 'infected') else '', scanned_at=timezone.now()) == 1
