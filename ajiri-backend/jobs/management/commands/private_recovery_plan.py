"""Read-only account-quota plan for the next private snapshot and transfer copy."""
from datetime import datetime, timezone
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from jobs.management.commands.backup_private_data import media_inventory, no_links
from jobs.recovery_capacity import capacity_plan, MIB


class Command(BaseCommand):
    # see docs/CONCEPTS.md#private-recovery-capacity
    help = 'Plan private backup peak space from fresh account quota; never creates or prunes backups.'

    def add_arguments(self, parser):
        parser.add_argument('--quota-bytes', type=int, required=True)
        parser.add_argument('--used-bytes', type=int, required=True)
        parser.add_argument('--reserve-bytes', type=int, default=16 * MIB)
        parser.add_argument('--extra-snapshot-bytes', type=int, default=0)

    def handle(self, *args, **options):
        database = settings.DATABASES['default']
        if database['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('This planner supports SQLite only.')
        source = Path(database['NAME'])
        no_links(source)
        if not source.is_absolute() or not source.is_file():
            raise CommandError('Configured SQLite database must be an existing absolute file.')
        try:
            # Stat files rather than opening SQLite: even a read-only WAL connection
            # can create shared-memory files. Include journal bytes conservatively.
            size = source.stat().st_size
            for suffix in ('-wal', '-journal'):
                journal = Path(str(source) + suffix)
                no_links(journal)
                if journal.exists():
                    if not journal.is_file():
                        raise CommandError('SQLite journals must be regular files.')
                    size += journal.stat().st_size
            media_root = Path(settings.MEDIA_ROOT)
            if not media_root.is_absolute():
                raise CommandError('Private media must be an absolute directory.')
            media = media_inventory(media_root)
            ledger_root = Path(settings.ERASURE_LEDGER_DIR)
            no_links(ledger_root)
            if not ledger_root.is_absolute():
                raise CommandError('Erasure ledger must be an absolute private directory.')
            ledger = media_inventory(ledger_root) if ledger_root.exists() else {}
            plan = capacity_plan(
                quota_bytes=options['quota_bytes'], used_bytes=options['used_bytes'],
                reserve_bytes=options['reserve_bytes'], database_bytes=size,
                media_sizes=[entry[0] for entry in media.values()],
                ledger_sizes=[entry[0] for entry in ledger.values()],
                ledger_present=ledger_root.exists(),
                extra_snapshot_bytes=options['extra_snapshot_bytes'])
        except (OSError, ValueError) as error:
            raise CommandError('Recovery capacity could not be measured safely; no backup created.') from error
        plan['measured_at_utc'] = datetime.now(timezone.utc).isoformat()
        plan['measurement_limit'] = 'Recheck account usage and inputs under the paused-writer release window.'
        self.stdout.write(json.dumps(plan, sort_keys=True))
        if not plan['sufficient']:
            raise CommandError('Insufficient account-quota reserve; preserve files and resolve capacity before backup/release.')
