from django.core.management.base import BaseCommand, CommandError
from accounts.erasure import operate
from django.db import DatabaseError
from django.db.models.deletion import ProtectedError


class Command(BaseCommand):
    help = 'Verified-request erasure; dry-run, prepare signed recovery journal, then explicit execution.'
    # see docs/CONCEPTS.md#recoverable-account-erasure

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, required=True)
        parser.add_argument('--request-id', required=True)
        parser.add_argument('--journal-dir', required=True)
        parser.add_argument('--mode', choices=['dry-run', 'prepare', 'execute', 'replay'], default='dry-run')
        for name in ('verified-request', 'writers-paused', 'legal-hold-cleared', 'journal-copied'):
            parser.add_argument('--' + name, action='store_true')

    def handle(self, *args, **options):
        try:
            self.stdout.write(operate(options))
        except CommandError:
            raise
        except (OSError, ValueError, KeyError, TypeError, DatabaseError, ProtectedError):
            raise CommandError('Erasure did not complete. Preserve the journal and investigate before retrying.') from None
