from django.core.management.base import BaseCommand

from jobs.general_alert_email import deliver, enabled
from jobs.models import Notification


class Command(BaseCommand):
    help = 'Deliver a bounded batch of opted-in current-job match emails; disabled by default.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=20, choices=range(1, 51))

    def handle(self, *args, **options):
        if not enabled():
            self.stdout.write('Match email delivery is disabled; no changes.')
            return
        # Freshness, consent and quotas are checked again per handoff, never inferred here.
        candidates = Notification.objects.filter(sent_email=False, match_score__gte=70,
            delivery_attempts__isnull=True).order_by('pk').values_list('pk', flat=True)[:options['limit']]
        counts = {}
        for identity in list(candidates):
            state = deliver(identity)
            counts[state] = counts.get(state, 0) + 1
        self.stdout.write(str(counts))  # Counts only; no mailbox, token, job text or provider body.
