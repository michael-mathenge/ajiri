from django.db import models
from profiles.models import Skill


class Job(models.Model):
    """
    A single job listing pulled in from an external job board.
    We don't create jobs ourselves — every Job row represents something
    scraped/ingested from a source like BrighterMonday or MyJobMag.
    """

    class JobType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        CONTRACT = 'contract', 'Contract'
        INTERNSHIP = 'internship', 'Internship'

    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)

    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    # When True, frontend shows "To be discussed during interview process"
    # instead of salary_min/max, regardless of whether they're filled in.
    is_salary_negotiable = models.BooleanField(default=False)

    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.FULL_TIME,
    )

    # Reuses the SAME Skill model from the profiles app (not a separate one).
    # This is what makes match-scoring possible later: a profile's skills
    # and a job's required skills point at the exact same underlying rows.
    skills_required = models.ManyToManyField(Skill, blank=True, related_name='jobs')

    source_url = models.URLField(unique=True)
    source_name = models.CharField(max_length=100)

    posted_at = models.DateTimeField(null=True, blank=True)
    scraped_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_flagged_scam = models.BooleanField(default=False)
    scam_flags = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.title} at {self.company_name}"