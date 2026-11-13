"""Aggregate, read-only readiness for Ajiri's original employer vacancy source."""
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

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
            'freshness_enforced': settings.JOB_FRESHNESS_ENFORCED,
            'posting_enabled': settings.EMPLOYER_POSTING_ENABLED,
            'public_jobs_enabled': settings.PUBLIC_JOBS_ENABLED,
            'verification_limit': 'Counts do not establish employer authority, pilot usability or inbox delivery.',
        }, sort_keys=True))
