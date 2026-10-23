from django.core.management.base import BaseCommand
from jobs.freshness import archive_expired


class Command(BaseCommand):
    help = 'Archive expired publication evidence without deleting jobs or applications.'

    def handle(self, **options):
        self.stdout.write(f'Expired publications archived: {archive_expired()}. '
            'Unverified active historical rows are also archived when freshness enforcement is enabled.')
