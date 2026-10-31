import uuid
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from jobs.delivery_queue import enabled, enqueue


class Command(BaseCommand):
    help = 'Enqueue a minimal existing owner target or a matching sweep; no provider I/O.'

    def add_arguments(self, parser):
        target = parser.add_mutually_exclusive_group(required=True)
        target.add_argument('--authorization-id', type=uuid.UUID)
        target.add_argument('--notification-id', type=int)
        target.add_argument('--search-id', type=uuid.UUID)
        target.add_argument('--matching', action='store_true')
        parser.add_argument('--owner-id', type=int)

    def handle(self, *args, **options):
        if not enabled():
            self.stdout.write('Delivery queue is disabled; no changes.')
            return
        try:
            if options['matching']:
                if options['owner_id'] is not None:
                    raise ValueError
                task = enqueue('matching')
            else:
                owner = get_user_model().objects.get(pk=options['owner_id'], is_active=True)
                kind, identity = next((kind, options[field]) for kind, field in (
                    ('application', 'authorization_id'), ('alert', 'notification_id'), ('saved_search', 'search_id')) if options[field] is not None)
                task = enqueue(kind, identity, owner=owner)
        except (ValueError, ObjectDoesNotExist):
            raise CommandError('Queue target is unavailable, not due or belongs to another owner.') from None
        self.stdout.write(str(task.pk))
