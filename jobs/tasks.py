from celery import shared_task
from .ingestion import ingest_myjobmag_kenya


@shared_task
def ingest_myjobmag_kenya_task():
    """
    Celery task wrapper around ingest_myjobmag_kenya(). Celery can only
    schedule/queue functions decorated with @shared_task — this is what
    makes autodiscover_tasks() (in config/celery.py) find and register it.
    """
    result = ingest_myjobmag_kenya()
    return result