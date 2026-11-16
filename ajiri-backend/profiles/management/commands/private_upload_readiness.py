"""Aggregate private quarantine checks. No credentials, paths or documents."""
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Sum
from profiles.models import CertificateEvidence
from profiles.scanner import configuration_ready, enabled, probe_ready


class Command(BaseCommand):
    # see docs/CONCEPTS.md#local-malware-scanning
    help = 'Report private upload gates and quarantine counts; optional document-free local engine probe.'

    def add_arguments(self, parser):
        parser.add_argument('--probe', action='store_true')

    def handle(self, *args, **options):
        probe = options.get('probe', False)
        if type(probe) is not bool:
            raise CommandError('probe must be a boolean.')
        counts = {row['scan_state']: row['count'] for row in
                  CertificateEvidence.objects.values('scan_state').annotate(count=Count('pk'))}
        configured = configuration_ready()
        self.stdout.write(json.dumps({
            'certificate_evidence_enabled': settings.CERTIFICATE_EVIDENCE_ENABLED,
            'scanning_enabled': enabled(),
            'uploads_suspended': settings.PRIVATE_UPLOADS_SUSPENDED,
            'scanner_configuration_ready': configured,
            'engine_probe': ('ready' if probe_ready() else 'unavailable') if probe else 'not_requested',
            'evidence_counts': counts,
            'evidence_bytes': CertificateEvidence.objects.aggregate(total=Sum('size_bytes'))['total'] or 0,
            'external_verification': 'capacity_processing_terms_real_engine_and_recovery_not_established',
            'changes': False,
        }, sort_keys=True))
