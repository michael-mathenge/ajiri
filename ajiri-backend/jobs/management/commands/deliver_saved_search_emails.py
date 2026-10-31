import uuid

from django.core.management.base import BaseCommand
from jobs.general_saved_search_email import deliver_due, enabled


class Command(BaseCommand):
    help = 'Deliver one bounded saved-search email batch; disabled by default.'

    def add_arguments(self, parser):
        parser.add_argument('--search-id', required=True, type=uuid.UUID)

    def handle(self, *args, **options):
        if not enabled():
            self.stdout.write('Saved-search email delivery is disabled; no changes.')
            return
        outcomes = deliver_due(options['search_id'])
        self.stdout.write(str({state: outcomes.count(state) for state in set(outcomes)}))
