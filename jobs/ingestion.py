import feedparser
from datetime import datetime, timezone
from django.utils.timezone import make_aware
from .models import Job

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

        Job.objects.create(
            title=title,
            company_name=company_name,
            description=entry.get('description', ''),
            location=entry.get('location', ''),
            source_url=source_url,
            source_name='MyJobMag Kenya',
            posted_at=parse_pubdate(entry),
        )
        created_count += 1

    return {'created': created_count, 'skipped': skipped_count}