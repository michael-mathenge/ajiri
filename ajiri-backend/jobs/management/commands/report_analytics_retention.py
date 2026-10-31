import json
from datetime import date
from django.core.management.base import BaseCommand
from jobs.models import AnalyticsDailyCount


class Command(BaseCommand):
    help = 'Report aggregate bucket retention candidates without pruning or exposing user records.'

    def add_arguments(self, parser):
        parser.add_argument('--before', type=date.fromisoformat, required=True)

    def handle(self, *args, **options):
        self.stdout.write(json.dumps({'candidate_buckets': AnalyticsDailyCount.objects.filter(
            day__lt=options['before']).count(), 'changed': False}))
