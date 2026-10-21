"""Read-only search timings on existing listings; emits no job or owner data."""
import json
import statistics
import time
from django.core.management.base import BaseCommand, CommandError
from jobs.models import Job
from jobs.search import search_jobs, expression
from rest_framework.exceptions import ValidationError


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('--query', action='append', dest='queries')
        parser.add_argument('--runs', type=int, default=20)

    def handle(self, *args, **options):
        runs = options['runs']
        if not 5 <= runs <= 100:
            raise CommandError('Use between 5 and 100 runs.')
        queryset = Job.objects.filter(is_active=True, is_flagged_scam=False)
        summary = {'active_jobs': queryset.count(), 'runs_per_query': runs, 'samples': []}
        for value in options['queries'] or ['python', 'project manager', 'nairobi', 'accountant']:
            timings = []
            for _ in range(runs):
                started = time.perf_counter()
                rows = list(search_jobs(queryset, value).values_list('pk', flat=True)[:20])
                timings.append((time.perf_counter() - started) * 1000)
            summary['samples'].append({'query_number': len(summary['samples']) + 1,
                'returned': len(rows), 'median_ms': round(statistics.median(timings), 3),
                'p95_ms': round(sorted(timings)[int((runs - 1) * .95)], 3)})
        checked = found = skipped = 0
        seen = set()
        for job in queryset.order_by('-posted_at', '-pk')[:30]:
            key = job.title.strip().casefold()
            if key in seen or checked >= 12:
                continue
            seen.add(key)
            try:
                if not expression(job.title):
                    skipped += 1
                    continue
                candidates = list(search_jobs(queryset, job.title).values_list('title', flat=True)[:5])
            except ValidationError:
                skipped += 1
                continue
            checked += 1
            found += any(title.strip().casefold() == key for title in candidates)
        summary['known_title_recall'] = {'checked': checked, 'found_in_top5': found, 'skipped': skipped}
        self.stdout.write(json.dumps(summary, sort_keys=True))
