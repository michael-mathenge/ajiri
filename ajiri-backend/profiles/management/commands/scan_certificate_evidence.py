import uuid
from django.core.management.base import BaseCommand
from profiles.certificate_scanning import scan_certificate


class Command(BaseCommand):
    help = 'Explicitly scan one private certificate via the configured local engine; no automatic retry.'

    def add_arguments(self, parser):
        parser.add_argument('--evidence-id', type=uuid.UUID, required=True)
        parser.add_argument('--recover-stalled', action='store_true')

    def handle(self, *args, **options):
        changed = scan_certificate(options['evidence_id'], recover_stalled=options['recover_stalled'])
        self.stdout.write('Scan result recorded.' if changed else 'No scan claim; disabled, missing or already running.')
