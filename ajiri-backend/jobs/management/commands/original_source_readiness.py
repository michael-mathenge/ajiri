"""Aggregate, read-only readiness for Ajiri's original employer vacancy source."""
import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts import general_email
from jobs.freshness import eligible_jobs
from jobs.models import EmployerJobDraft, EmployerOrganisation, JobPublication


class Command(BaseCommand):
    # see docs/CONCEPTS.md#ajiri-original-vacancies
    help = 'Report original-source pilot counts; never creates or approves vacancies.'
    requires_system_checks = []

    def handle(self, *args, **options):
        original = eligible_jobs().filter(publication__origin='employer')
        if not settings.JOB_FRESHNESS_ENFORCED:
            original = original.none()
        roles = original.count()
        employers = original.values('publication__organisation_id').distinct().count()
        # Configuration can be inspected without creating tokens, receipts or mail.
        # see docs/CONCEPTS.md#vacancy-pilot-readiness
        security_mail = 'disabled'
        if getattr(settings, 'ACCOUNT_SECURITY_EMAIL_ENABLED', False):
            try:
                security_mail = ('configured_not_delivery_verified'
                                 if general_email.configuration() is not None else 'disabled')
            except ImproperlyConfigured:
                security_mail = 'misconfigured'
        blockers = []
        for present, code in (
            (settings.JOB_FRESHNESS_ENFORCED, 'freshness_disabled'),
            (security_mail == 'configured_not_delivery_verified', 'general_account_mail_unavailable'),
            (roles >= 1 and employers >= 1, 'first_reviewed_vacancy_missing'),
            (settings.EMPLOYER_POSTING_ENABLED, 'posting_disabled'),
            (settings.PUBLIC_JOBS_ENABLED, 'publication_disabled'),
        ):
            if not present:
                blockers.append(code)
        self.stdout.write(json.dumps({
            'evaluated_at': timezone.now().isoformat(),
            'publisher': 'Ajiri',
            'source_strategy': 'original_employer_submissions',
            'eligible_original_roles': roles,
            'employers_with_eligible_roles': employers,
            'pending_organisations': EmployerOrganisation.objects.filter(status='pending').count(),
            'pending_vacancies': EmployerJobDraft.objects.filter(status='pending').count(),
            'original_publication_records': JobPublication.objects.filter(origin='employer').count(),
            'pilot_role_target': 50,
            'pilot_employer_target': 10,
            'role_shortfall': max(0, 50 - roles),
            'employer_shortfall': max(0, 10 - employers),
            'inventory_targets_met': roles >= 50 and employers >= 10,
            'first_vacancy_role_target': 1,
            'first_vacancy_employer_target': 1,
            'first_vacancy_inventory_met': roles >= 1 and employers >= 1,
            'account_security_mail': security_mail,
            'saved_searches_enabled': settings.SAVED_SEARCHES_ENABLED,
            'application_email_enabled': settings.APPLICATION_EMAIL_ENABLED,
            'alert_email_enabled': settings.ALERT_EMAIL_ENABLED,
            'general_application_email_enabled': settings.GENERAL_APPLICATION_EMAIL_ENABLED,
            'general_alert_email_enabled': settings.GENERAL_ALERT_EMAIL_ENABLED,
            'saved_search_email_enabled': settings.SAVED_SEARCH_EMAIL_ENABLED,
            'configuration_blockers': blockers,
            'external_verification': 'not_established_by_this_command',
            'required_private_evidence': [
                'outside_employer_onboarding', 'employer_authority',
                'independent_review', 'no_applicant_fee',
                'consented_candidate_pilot', 'manual_mobile_accessibility',
            ],
            'freshness_enforced': settings.JOB_FRESHNESS_ENFORCED,
            'posting_enabled': settings.EMPLOYER_POSTING_ENABLED,
            'public_jobs_enabled': settings.PUBLIC_JOBS_ENABLED,
            'verification_limit': 'Counts do not establish employer authority, pilot usability or inbox delivery.',
        }, sort_keys=True))
