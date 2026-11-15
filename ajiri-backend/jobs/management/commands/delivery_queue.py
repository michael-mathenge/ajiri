import json
import uuid
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from jobs.delivery_queue import enabled, execute, publish, recover_leases
from jobs.models import DeliveryTask
from jobs.delivery_batches import validate_limit


class Command(BaseCommand):
    help = 'Inspect durable queue counts or explicitly publish/execute/recover bounded work; no ambiguous publication retry.'

    def add_arguments(self, parser):
        action = parser.add_mutually_exclusive_group()
        action.add_argument('--publish-pending', action='store_true')
        action.add_argument('--recover-leases', action='store_true')
        action.add_argument('--execute-id', type=uuid.UUID)
        parser.add_argument('--resume-blocked', action='store_true')
        parser.add_argument('--limit', type=int, choices=range(1, 51), default=20)

    def handle(self, *args, **options):
        try:
            validate_limit(options['limit'])
            if (sum(bool(options[key]) for key in ('publish_pending', 'recover_leases', 'execute_id')) > 1
                    or (options['resume_blocked'] and not options['execute_id'])):
                raise ValueError('Choose one action; reconciliation requires an execution ID.')
            if options['execute_id'] is not None:
                options['execute_id'] = uuid.UUID(str(options['execute_id']))
        except (ValueError, TypeError, AttributeError):
            raise CommandError('Invalid queue action, ID or limit (1-50).') from None
        if not enabled() and any(options[key] for key in ('publish_pending', 'recover_leases', 'execute_id')):
            self.stdout.write('Delivery queue is disabled; no changes.')
            return
        if options['publish_pending']:
            for identity in list(DeliveryTask.objects.filter(state='pending').order_by('created_at')
                    .values_list('pk', flat=True)[:options['limit']]):
                publish(identity)
        elif options['recover_leases']:
            recover_leases(options['limit'])
        elif options['execute_id']:
            execute(options['execute_id'], resume_blocked=options['resume_blocked'])
        self.stdout.write(json.dumps(list(DeliveryTask.objects.values('state').annotate(count=Count('pk')).order_by('state'))))
