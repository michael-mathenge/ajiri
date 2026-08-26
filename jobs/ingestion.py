import feedparser
from datetime import datetime, timezone
from django.utils.timezone import make_aware
from .models import Job
from .scam_filter import analyze_job_for_scam
from .utils import detect_application_method
from .matching import notify_matching_profiles

MYJOBMAG_KENYA_FEED = "https://www.myjobmag.co.ke/jobsxml_by_categories.xml"


def parse_pubdate(entry):
    """
    RSS pubDate looks like 'Fri, 21 Aug 2026 15:33:32 GMT'.
    feedparser conveniently pre-parses this into a time.struct_time
    via entry.published_parsed — we just convert it to a real datetime.
    """
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return make_aware(datetime(*entry.published_parsed[:6]))
    return None


def ingest_myjobmag_kenya():
    feed = feedparser.parse(MYJOBMAG_KENYA_FEED)

    created_count = 0
    skipped_count = 0
    flagged_count = 0
    notified_count = 0

    for entry in feed.entries:
        source_url = entry.get('link')

        if not source_url:
            skipped_count += 1
            continue

        # source_url is unique on the Job model — this is our natural
        # de-duplication check. If we've already ingested this exact
        # listing before, skip it rather than creating a duplicate.
        if Job.objects.filter(source_url=source_url).exists():
            skipped_count += 1
            continue

        title = entry.get('position') or entry.get('title', '')
        company_name = entry.get('company', '')

        if not title or not company_name:
            # Malformed entry — log and skip rather than saving garbage.
            skipped_count += 1
            continue

        description = entry.get('description', '')

        # Scan the description for an email address to decide whether
        # this job supports true auto-apply (email) or needs the user
        # to click through and apply manually (external_link).
        # See docs/CONCEPTS.md#application-method-detection
        application_method, application_email = detect_application_method(description)

        job = Job.objects.create(
            title=title,
            company_name=company_name,
            description=description,
            location=entry.get('location', ''),
            source_url=source_url,
            source_name='MyJobMag Kenya',
            posted_at=parse_pubdate(entry),
            application_method=application_method,
            application_email=application_email,
        )

        # Run the job through the rule-based scam filter AFTER creation,
        # since analyze_job_for_scam() expects a real Job instance with
        # actual field values to scan. Most jobs won't be flagged, so the
        # second save() only fires when something's actually suspicious.
        is_scam, reasons = analyze_job_for_scam(job)
        if is_scam:
            job.is_flagged_scam = True
            job.scam_flags = '; '.join(reasons)
            job.save(update_fields=['is_flagged_scam', 'scam_flags'])
            flagged_count += 1

        created_count += 1

        # Alert any profile that's a strong match (>=70%) for this job,
        # right away rather than waiting for the periodic sweep. Skipped
        # automatically inside notify_matching_profiles() if the job just
        # got flagged as a scam above. See docs/CONCEPTS.md#job-alerts
        notified_count += notify_matching_profiles(job)

    return {
        'created': created_count,
        'skipped': skipped_count,
        'flagged': flagged_count,
        'notified': notified_count,
    }