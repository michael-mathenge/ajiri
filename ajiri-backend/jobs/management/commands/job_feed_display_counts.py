"""SELECT-only counts; no ingestion, sweeps or delivery side effects."""
import json
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from jobs.models import Job
from jobs.freshness import eligible_jobs
from jobs.feed_display import browse_jobs, supplemental_jobs


class Command(BaseCommand):
    help = 'Read-only feed display counts; does not change settings or data.'
    requires_system_checks = []

    def handle(self, *args, **options):
        at = timezone.now()
        eligible = eligible_jobs(at=at)
        supplemental = supplemental_jobs(at=at).exclude(pk__in=eligible.values('pk'))
        self.stdout.write(json.dumps({
            'evaluated_at': at.isoformat(),
            'total': Job.objects.count(),
            'scam_flagged': Job.objects.filter(is_flagged_scam=True).count(),
            'eligible': eligible.count(),
            'supplemental_unverified': supplemental.count(),
            'browse_off': browse_jobs(at=at, enabled=False).count(),
            'browse_on': browse_jobs(at=at, enabled=True).count(),
            'supplemental_posted_within_14_days': supplemental.filter(
                posted_at__gte=at-timedelta(days=14), posted_at__lte=at).count(),
        }, indent=2))
