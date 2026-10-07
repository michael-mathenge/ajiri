from django.core.management.base import BaseCommand
from jobs.models import Job
from jobs.utils import fix_mojibake


class Command(BaseCommand):
    """
    One-off repair for jobs ingested before ingestion.py started calling
    fix_mojibake() on every text field. See docs/CONCEPTS.md#mojibake.

    Usage: python manage.py fix_mojibake
           python manage.py fix_mojibake --dry-run   (preview only, no writes)
    """
    help = "Repairs mojibake (wrongly-decoded UTF-8) in existing Job rows."

    FIELDS = ['title', 'company_name', 'description', 'requirements', 'location']

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without saving anything.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fixed_count = 0

        for job in Job.objects.all():
            changed_fields = []

            for field_name in self.FIELDS:
                original = getattr(job, field_name)
                repaired = fix_mojibake(original)
                if repaired != original:
                    setattr(job, field_name, repaired)
                    changed_fields.append(field_name)

            if changed_fields:
                fixed_count += 1
                self.stdout.write(
                    f"Job {job.id}: fixing {', '.join(changed_fields)}"
                )
                if not dry_run:
                    job.save(update_fields=changed_fields)

        verb = "Would fix" if dry_run else "Fixed"
        self.stdout.write(self.style.SUCCESS(f"{verb} {fixed_count} job(s)."))
