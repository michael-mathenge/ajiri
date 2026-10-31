"""Report-only private storage reconciliation. Never removes or repairs bytes."""
import json

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from profiles.certificates import private_bytes
from profiles.cv_builder import CVUnavailable
from profiles.models import CertificateEvidence


class Command(BaseCommand):
    help = 'Report certificate storage integrity/orphans without changing records or files.'

    def handle(self, *args, **options):
        rows = CertificateEvidence.objects.all()
        if rows.count() > 10000:
            raise CommandError('Certificate inventory exceeds operator review limit; no changes.')
        referenced, invalid = set(), 0
        for row in rows.iterator():
            referenced.add(row.document.name)
            try:
                private_bytes(row)
            except CVUnavailable:
                invalid += 1
        try:
            directories, files = default_storage.listdir('quarantine/certificates')
        except FileNotFoundError:
            directories, files = [], []
        if len(files) > 10000 or directories:
            raise CommandError('Certificate storage needs scoped operator review; no changes.')
        stored = {f'quarantine/certificates/{name}' for name in files}
        self.stdout.write(json.dumps({'referenced': len(referenced), 'invalid_or_missing': invalid,
            'unreferenced': len(stored-referenced), 'changed': False}))
