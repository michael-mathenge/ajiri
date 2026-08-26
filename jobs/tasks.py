from celery import shared_task
from .ingestion import ingest_myjobmag_kenya
from .matching import sweep_all_active_jobs_for_matches


@shared_task
def ingest_myjobmag_kenya_task():
    """
    Celery task wrapper around ingest_myjobmag_kenya(). Celery can only
    schedule/queue functions decorated with @shared_task — this is what
    makes autodiscover_tasks() (in config/celery.py) find and register it.
    """
    result = ingest_myjobmag_kenya()
    return result


@shared_task
def sweep_job_matches_task():
    """
    Celery task wrapper around sweep_all_active_jobs_for_matches(). Runs on
    the schedule defined in CELERY_BEAT_SCHEDULE (every 6 hours) as a
    safety net for matches the immediate ingest-time check would miss —
    e.g. a profile created or edited after a job was already ingested.
    See docs/CONCEPTS.md#job-alerts
    """
    result = sweep_all_active_jobs_for_matches()
    return result