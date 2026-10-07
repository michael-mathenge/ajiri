import feedparser
from datetime import datetime, timezone
from django.utils.timezone import make_aware
from .models import Job
from .scam_filter import analyze_job_for_scam
from .utils import detect_application_method, fix_mojibake
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


def ingest_feed(feed):
    """
    Processes an already-parsed feedparser result: dedupe, repair encoding,
    create Job rows, scam-check, and fire match alerts. Split out from
    ingest_myjobmag_kenya() so TWO different callers can share it:
    the Celery task (which fetches the feed itself) and the remote ingest
    endpoint (where something else fetches the feed and POSTs it to us).
    See docs/CONCEPTS.md#remote-ingestion
    """
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

        # fix_mojibake() repairs a known encoding bug from this specific
        # feed — see docs/CONCEPTS.md#mojibake. Applied to every text
        # field pulled from the feed, since any of them can contain the
        # affected characters (en-dashes, curly quotes, etc.).
        title = fix_mojibake(entry.get('position') or entry.get('title', ''))
        company_name = fix_mojibake(entry.get('company', ''))

        if not title or not company_name:
            # Malformed entry — log and skip rather than saving garbage.
            skipped_count += 1
            continue

        description = fix_mojibake(entry.get('description', ''))
        location = fix_mojibake(entry.get('location', ''))

        # Scan the description for an email address to decide whether
        # this job supports true auto-apply (email) or needs the user
        # to click through and apply manually (external_link).
        # See docs/CONCEPTS.md#application-method-detection
        application_method, application_email = detect_application_method(description)

        job = Job.objects.create(
            title=title,
            company_name=company_name,
            description=description,
            location=location,
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


def ingest_myjobmag_kenya():
    """Fetches the live feed directly (works wherever outbound internet is open)."""
    feed = feedparser.parse(MYJOBMAG_KENYA_FEED)
    return ingest_feed(feed)
