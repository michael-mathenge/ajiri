import json
from django.core.management.base import BaseCommand, CommandError
from jobs.daraja import PaymentBlocked
from jobs.models import PaymentCheckout
from jobs.payments import reconcile_checkout


class Command(BaseCommand):
    help = 'Explicit bounded read-only sandbox query; never initiates, retries payment or grants access.'

    def add_arguments(self, parser):
        parser.add_argument('--checkout-id', required=True)

    def handle(self, *args, **options):
        try:
            row = PaymentCheckout.objects.select_related('owner').get(pk=options['checkout_id'])
            row = reconcile_checkout(row.owner, row.id)
        except (PaymentCheckout.DoesNotExist, PaymentBlocked, ValueError):
            raise CommandError('Checkout reconciliation unavailable; retain the original identity.') from None
        self.stdout.write(json.dumps({'checkout_id': str(row.id), 'state': row.state, 'granted': False}))
