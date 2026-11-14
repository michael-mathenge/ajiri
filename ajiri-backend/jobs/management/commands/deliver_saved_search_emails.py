import json
import uuid

from django.core.management.base import BaseCommand, CommandError
from jobs.general_saved_search_email import deliver_batch, enabled


class Command(BaseCommand):
    help = 'Deliver one bounded saved-search email batch; disabled by default.'

    def add_arguments(self, parser):
        parser.add_argument('--search-id', required=True, type=uuid.UUID)
        parser.add_argument('--cursor', default=None)
        parser.add_argument('--limit', type=int, default=50, choices=range(1, 51))

    def handle(self, *args, **options):
        from jobs.delivery_batches import validate_limit
        try:
            validate_limit(options['limit'])
            search_id = uuid.UUID(str(options['search_id']))
        except (ValueError, TypeError, AttributeError):
            raise CommandError('A valid search UUID and limit between 1 and 50 are required.') from None
        if not enabled():
            self.stdout.write('Saved-search email delivery is disabled; no changes.')
            return
        try:
            result = deliver_batch(search_id, cursor=options['cursor'], limit=options['limit'])
        except ValueError as error:
            raise CommandError(str(error)) from None
        result.pop('results')
        self.stdout.write(json.dumps(result))

