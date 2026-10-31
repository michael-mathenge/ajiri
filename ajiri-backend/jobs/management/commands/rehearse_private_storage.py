import json
import hashlib
from pathlib import Path
from django.apps import apps
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand, CommandError
from django.db.models import FileField
from jobs.storage_copy import StorageCopyBlocked, copy_private_storage


class Command(BaseCommand):
    help = 'Verify an explicit private filesystem copy/isolated restore; never switches storage or removes data.'

    def add_arguments(self, parser):
        parser.add_argument('--source-dir', required=True)
        parser.add_argument('--target-dir', required=True)
        parser.add_argument('--journal', required=True)
        parser.add_argument('--restore-dir')
        parser.add_argument('--writers-paused', action='store_true')
        parser.add_argument('--target-private', action='store_true')

    def handle(self, *args, **options):
        if not options['writers_paused'] or not options['target_private']:
            raise CommandError('Explicit paused-writer and private-target attestations are required; no transfer.')
        def inventory():
            references = []
            for model in apps.get_models():
                for field in model._meta.fields:
                    if isinstance(field, FileField):
                        references.extend((model._meta.label_lower, str(pk), field.name, name)
                            for pk, name in model.objects.values_list('pk', field.name) if name)
            return sorted(references)
        references = inventory()
        names = {reference[3] for reference in references}
        source = FileSystemStorage(location=options['source_dir'])
        target = FileSystemStorage(location=options['target_dir'])
        try:
            result = copy_private_storage(source, target, names, options['journal'], writers_paused=True, target_private=True)
            if inventory() != references:
                raise StorageCopyBlocked('Database file references changed; no cutover.')
            result['reference_snapshot_sha256'] = hashlib.sha256(json.dumps(references).encode()).hexdigest()
            result['references_unchanged'] = True
            if options['restore_dir']:
                restored = FileSystemStorage(location=options['restore_dir'])
                restore_journal = Path(options['journal']).with_name(Path(options['journal']).name+'.restore.json')
                result['restore'] = copy_private_storage(target, restored, names, restore_journal,
                    writers_paused=True, target_private=True)
        except (StorageCopyBlocked, OSError, ValueError):
            raise CommandError('Private copy/restore was blocked. Preserve all source/target bytes and journals for review.') from None
        self.stdout.write(json.dumps(result))
