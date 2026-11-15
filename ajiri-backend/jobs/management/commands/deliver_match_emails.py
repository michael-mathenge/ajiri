import json

from django.core.management.base import BaseCommand, CommandError

from jobs.general_alert_email import deliver, enabled
from jobs.models import Notification
from jobs.delivery_batches import decode, page, report, validate_limit


class Command(BaseCommand):
    help = 'Deliver a bounded batch of opted-in current-job match emails; disabled by default.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=20, choices=range(1, 51))
        parser.add_argument('--cursor', default=None)

    def handle(self, *args, **options):
        # call_command keyword options bypass argparse choices; enforce the cap here too.
        try:
            validate_limit(options['limit'])
            decode(options['cursor'], 'match-alerts')
        except ValueError as error:
            raise CommandError(str(error)) from None
        if not enabled():
            self.stdout.write('Match email delivery is disabled; no changes.')
            return
        # Freshness, consent and quotas are checked again per handoff, never inferred here.
        candidates = Notification.objects.filter(sent_email=False, match_score__gte=70,
            delivery_attempts__isnull=True)
        identities, cursor = page(candidates, 'match-alerts', options['cursor'], options['limit'])
        outcomes = [deliver(identity) for identity in identities]
        self.stdout.write(json.dumps(report(outcomes, len(identities), cursor)))
