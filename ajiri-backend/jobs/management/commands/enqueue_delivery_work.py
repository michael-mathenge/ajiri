import uuid
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from jobs.delivery_queue import enabled, enqueue


class Command(BaseCommand):
    help = 'Enqueue a minimal existing owner target ; no provider I/O.'

    def add_arguments(self, parser):
        target = parser.add_mutually_exclusive_group(required=True)
        target.add_argument('--authorization-id', type=uuid.UUID)
        target.add_argument('--notification-id', type=int)
        target.add_argument('--search-id', type=uuid.UUID)
        parser.add_argument('--owner-id', type=int)

    def handle(self, *args, **options):
        fields = [('application', 'authorization_id'), ('alert', 'notification_id'), ('saved_search', 'search_id')]
        targets = [(kind, options[field]) for kind, field in fields if options[field] is not None]
        try:
            if len(targets) != 1 or type(options['owner_id']) is not int or options['owner_id'] <= 0:
                raise ValueError
            kind, identity = targets[0]
            if kind == 'alert':
                if type(identity) is not int or identity <= 0:
                    raise ValueError
            else:
                identity = uuid.UUID(str(identity))
        except (ValueError, TypeError, AttributeError):
            raise CommandError('Exactly one valid target and a positive owner ID are required.') from None
        if not enabled():
            self.stdout.write('Delivery queue is disabled; no changes.')
            return
        try:
            owner = get_user_model().objects.get(pk=options['owner_id'], is_active=True)
            task = enqueue(kind, identity, owner=owner)
        except (ValueError, ObjectDoesNotExist):
            raise CommandError('Queue target is unavailable, not due or belongs to another owner.') from None
        self.stdout.write(str(task.pk))
