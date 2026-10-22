"""Prepare a hidden blank review draft; never approves documents or sends email."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import User
from profiles.models import Profile
from jobs.application_dispatch import configuration, SOURCE, DISCLAIMER
from jobs.models import Job, Application


class Command(BaseCommand):
    help = 'Dry-run or create one inactive synthetic owner application; no mail or approvals.'

    def add_arguments(self, parser):
        parser.add_argument('--create', action='store_true')

    def handle(self, *args, **options):
        # see docs/CONCEPTS.md#managed-application-pilot
        configured = configuration()
        if configured is None:
            raise CommandError('The reviewed owner application pilot is not enabled.')
        policy, _ = configured
        user = User.objects.filter(pk=policy.owner_id, is_active=True).first()
        if (user is None or user.email.casefold() != policy.recipient
            or not Profile.objects.filter(user=user, email_verified_at__isnull=False,
                verified_email__iexact=policy.recipient).exists()):
            raise CommandError('The pilot owner must verify the current allowlisted mailbox first.')
        if not options['create']:
            self.stdout.write('DRY RUN: one inactive synthetic job and blank review draft; no writes, approvals or email.')
            return
        expected = dict(title='Ajiri synthetic application pilot', company_name='Synthetic example',
            description=DISCLAIMER, source_name=SOURCE, is_active=False, is_flagged_scam=False,
            application_method='email', application_email=policy.recipient)
        with transaction.atomic():
            job, _ = Job.objects.get_or_create(
                source_url=f'https://example.invalid/{SOURCE}/{user.pk}/draft-v1', defaults=expected)
            if any(getattr(job, field) != value for field, value in expected.items()):
                raise CommandError('Existing synthetic job changed; review it privately without overwriting it.')
            app, created = Application.objects.get_or_create(user=user, job=job, defaults={
                'status': 'ready_for_review', 'application_method': 'email',
                'application_email': policy.recipient})
        self.stdout.write(('Prepared' if created else 'Existing') + f' owner-only draft: {app.pk}; no documents approved or email attempted.')
