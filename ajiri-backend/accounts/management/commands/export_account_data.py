"""Operator-assisted export; never sends data or modifies the owner's account."""
import hashlib
import json
import os
from pathlib import Path
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import FileField

from config.paths import application_tree
from jobs.management.commands.backup_private_data import no_links
from jobs.models import (Application, ApplicationPackage, ApplicationPackageApproval,
                         ApplicationSendAuthorization, ApplicationSendAttemptLink,
                         DeliveryAttempt, DeliveryDailyBudget, Job, Notification)
from profiles.models import Profile, CVWorkspace, CVApproval, AlertConsentEvent, CertificateEvidence
from jobs.models import SavedSearch, SavedSearchMatch
from jobs.models import AnalyticsChoice, DeliveryTask, PaymentCheckout


class Command(BaseCommand):
    help = 'Export one verified requester to a new private folder; dry-run first.'
    # see docs/CONCEPTS.md#verified-account-export

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, required=True)
        parser.add_argument('--destination', required=True)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--verified-request', action='store_true')
        parser.add_argument('--writers-paused', action='store_true')

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.export(options)
        except CommandError:
            raise
        except (OSError, ValueError, TypeError, get_user_model().DoesNotExist):
            raise CommandError('Export failed; no completion manifest was written. Account unchanged.') from None

    def export(self, options):
        destination = Path(options['destination'])
        if not destination.is_absolute():
            raise CommandError('Use an absolute private destination.')
        no_links(destination)
        destination = destination.resolve()
        media = Path(settings.MEDIA_ROOT).resolve()
        forbidden = (application_tree(settings.BASE_DIR), media,
                     Path(settings.DATABASES['default']['NAME']).resolve().parent)
        if destination.exists() or any(destination == p or destination.is_relative_to(p) for p in forbidden):
            raise CommandError('Destination must be new and outside application and live data directories.')
        if not destination.parent.is_dir():
            raise CommandError('Destination parent must already exist.')
        if not options['dry_run'] and not (options['verified_request'] and options['writers_paused']):
            raise CommandError('Execution requires a verified owner request and paused writers; use --dry-run first.')

        user = get_user_model().objects.get(pk=options['user_id'])
        applications = Application.objects.filter(user=user)
        packages = ApplicationPackage.objects.filter(application__user=user)
        if packages.exclude(cv_approval__profile__user=user).exists():
            raise CommandError('Cross-owner document reference; investigate before export.')
        authorizations = ApplicationSendAuthorization.objects.filter(owner=user)
        if authorizations.exclude(application__user=user).exists():
            raise CommandError('Cross-owner authorization reference; investigate before export.')
        notifications = Notification.objects.filter(user=user)
        jobs = Job.objects.filter(pk__in=applications.values('job_id')).union(
            Job.objects.filter(pk__in=notifications.values('job_id')),
            Job.objects.filter(pk__in=SavedSearchMatch.objects.filter(search__owner=user).values('job_id')))
        scopes = [
            ('payment_checkout', PaymentCheckout.objects.filter(owner=user)),
            ('delivery_task', DeliveryTask.objects.filter(owner=user)),
            ('analytics_choice', AnalyticsChoice.objects.filter(owner=user)),
            ('saved_search', SavedSearch.objects.filter(owner=user)),
            ('saved_search_match', SavedSearchMatch.objects.filter(search__owner=user)),
            ('profile', Profile.objects.filter(user=user)),
            ('cv_workspace', CVWorkspace.objects.filter(profile__user=user)),
            ('cv_approval', CVApproval.objects.filter(profile__user=user)),
            ('certificate_evidence', CertificateEvidence.objects.filter(profile__user=user)),
            ('alert_consent', AlertConsentEvent.objects.filter(profile__user=user)),
            ('application', applications), ('application_package', packages),
            ('package_approval', ApplicationPackageApproval.objects.filter(package__application__user=user)),
            ('send_authorization', authorizations),
            ('send_attempt_link', ApplicationSendAttemptLink.objects.filter(authorization__owner=user)),
            ('notification', notifications), ('delivery_attempt', DeliveryAttempt.objects.filter(user=user)),
            ('delivery_budget', DeliveryDailyBudget.objects.filter(scope=f'user:{user.pk}')),
            ('job', jobs),
        ]
        account_fields = ('id', 'email', 'full_name', 'phone_number', 'is_active', 'date_joined', 'last_login')
        data = {'format': 1, 'account': {k: getattr(user, k) for k in account_fields}, 'records': {}}
        files = []
        total = 0
        for label, rows in scopes:
            records = []
            for row in rows:
                record = {}
                for field in row._meta.concrete_fields:
                    if ((isinstance(row, DeliveryAttempt) and field.name in ('recipient_digest', 'idempotency_key'))
                            or (isinstance(row, AlertConsentEvent) and field.name == 'recipient_digest')
                            or (isinstance(row, SavedSearchMatch) and field.name == 'email_attempt')):
                        continue  # Internal accounting fingerprints/keys are not portable account content.
                    value = getattr(row, field.attname)
                    if isinstance(field, FileField):
                        if not value:
                            record[field.name] = None
                            continue
                        source = Path(value.path)
                        no_links(source)
                        source = source.resolve()
                        if not source.is_relative_to(media) or not source.is_file():
                            raise CommandError('Private document is missing or unsafe; export incomplete.')
                        total += source.stat().st_size
                        if total > 200 * 1024 * 1024 or len(files) >= 1000:
                            raise CommandError('Export exceeds operator review limits.')
                        suffix = source.suffix.lower()
                        suffix = suffix if suffix in ('.docx', '.doc', '.pdf') else '.bin'
                        name = f'documents/{uuid.uuid4().hex}{suffix}'
                        files.append((source, name))
                        record[field.name] = name
                    else:
                        record[field.name] = value
                if isinstance(row, Profile):
                    record['skills'] = list(row.skills.values('id', 'name'))
                records.append(record)
            data['records'][label] = records
        if options['dry_run']:
            self.stdout.write(f'DRY RUN: {sum(len(v) for v in data["records"].values())} records; '
                              f'{len(files)} documents; {total} bytes; no writes.')
            return

        destination.mkdir(mode=0o700)
        os.chmod(destination, 0o700)
        (destination / 'documents').mkdir(mode=0o700)
        checks = {}
        for source, name in files:
            target = destination / name
            with source.open('rb') as stream:
                before = hashlib.file_digest(stream, 'sha256').hexdigest()
            with source.open('rb') as src, target.open('xb') as dst:
                os.chmod(target, 0o600)
                while chunk := src.read(1024 * 1024):
                    dst.write(chunk)
            with target.open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            with source.open('rb') as stream:
                after = hashlib.file_digest(stream, 'sha256').hexdigest()
            if not before == actual == after:
                raise CommandError('Document changed during export; no completion manifest.')
            checks[name] = actual
        payload = destination / 'account.json'
        with payload.open('x', encoding='utf-8') as stream:
            os.chmod(payload, 0o600)
            json.dump(data, stream, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)
        with payload.open('rb') as stream:
            checks['account.json'] = hashlib.file_digest(stream, 'sha256').hexdigest()
        # A failed/partial directory is deliberately never presented as a completed export.
        manifest = {'format': 1, 'complete': True, 'sha256': checks,
                    'excluded': ['password hashes', 'JWT/session secrets', 'internal delivery keys/digests', 'platform credentials',
                                 'other accounts', 'shared global budgets', 'backups and platform logs']}
        with (destination / 'manifest.json').open('x', encoding='utf-8') as stream:
            os.chmod(destination / 'manifest.json', 0o600)
            json.dump(manifest, stream, indent=2)
        self.stdout.write('Private account export complete; deliver only after requester identity verification.')
