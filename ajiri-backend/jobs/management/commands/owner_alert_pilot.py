import uuid
from django.core.management.base import BaseCommand, CommandError
from jobs.alert_delivery import configuration, deliver_match, synthetic, SYNTHETIC_SOURCE
from jobs.models import Job, Notification, DeliveryAttempt
from django.contrib.auth import get_user_model
from profiles.alert_consent import eligible
from django.db import transaction


class Command(BaseCommand):
    help = 'Prepare a hidden synthetic owner alert, or explicitly send its one bounded pilot attempt.'

    def add_arguments(self, parser):
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument('--prepare', action='store_true')
        action.add_argument('--notification-id', type=int)
        parser.add_argument('--confirm-owner-recipient', action='store_true')

    def handle(self, *args, **options):
        policy = configuration()
        if policy is None:
            raise CommandError('Owner alert pilot is disabled.')
        user = get_user_model().objects.get(pk=policy.owner_id, is_active=True)
        if user.email.casefold() != policy.recipient or not eligible(user.profile):
            raise CommandError('The owner must explicitly choose email alerts and verify the current mailbox first.')
        if options['prepare']:
            with transaction.atomic():
                job = Job.objects.create(title='Ajiri synthetic alert pilot', company_name='Synthetic example',
                    description='Owner-only delivery test, not a vacancy.', source_name=SYNTHETIC_SOURCE,
                    source_url=f'https://example.invalid/ajiri-owner-alert-pilot/{user.pk}/{uuid.uuid4()}', is_active=False)
                notification = Notification.objects.create(user=user, job=job, match_score=100, in_app=False)
            self.stdout.write(f'Prepared hidden synthetic notification: {notification.pk}; no email attempted.')
            return
        if not options['confirm_owner_recipient']:
            raise CommandError('An explicit owner-recipient pilot handoff is required.')
        notification = Notification.objects.select_related('user__profile', 'job').get(pk=options['notification_id'], user=user)
        if not synthetic(notification, policy):
            raise CommandError('Only the hidden synthetic owner pilot may be sent.')
        previous = DeliveryAttempt.objects.filter(notification=notification).first()
        if previous:
            self.stdout.write('Existing receipt: ' + previous.state + '; no new provider call. Reconcile before any retry.')
            return
        accepted = deliver_match(notification, explicit_owner_pilot=True)
        self.stdout.write('Provider accepted; inbox delivery is unverified.' if accepted
            else 'No provider acceptance confirmed. Inspect the receipt; never retry an ambiguous handoff.')
