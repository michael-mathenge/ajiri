"""Explicit feed evidence only; never guess a closing date from description prose."""

from datetime import datetime
from django.utils import timezone
from .models import JobPublication


def deadline(entry):
    # This first source contract accepts an explicit ISO timestamp with timezone.
    # Unknown date formats stay unverified, rather than silently assuming a zone.
    raw = entry.get("application_deadline") or entry.get("closing_date")
    if not isinstance(raw, str) or len(raw) > 80:
        return None
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return value if timezone.is_aware(value) else None
    except ValueError:
        return None


def record(job, entry):
    closes = deadline(entry)
    source_closed = str(entry.get("status", "")).strip().lower() in (
        "closed",
        "expired",
        "filled",
        "withdrawn",
    )
    existing = JobPublication.objects.filter(job=job).first()
    # An import cannot undo an archive, staff review or replace employer evidence.
    if existing:
        if existing.origin == "rss" and existing.status != "archived":
            if source_closed or closes and closes <= timezone.now():
                JobPublication.objects.filter(pk=existing.pk).update(
                    status="archived",
                    archive_reason="source_closed_or_deadline_passed",
                    archived_at=timezone.now(),
                )
            elif closes:
                # Earlier deadlines take effect; a later feed date cannot silently
                # extend an already advertised application window.
                effective = (
                    min(closes, existing.closes_at) if existing.closes_at else closes
                )
                JobPublication.objects.filter(pk=existing.pk).update(
                    closes_at=effective, status="published", confirmed_at=timezone.now()
                )
        return existing
    return JobPublication.objects.create(
        job=job,
        origin="rss",
        closes_at=closes,
        status="archived"
        if source_closed
        else ("published" if closes and closes > timezone.now() else "unverified"),
        archive_reason="source_closed" if source_closed else "",
        archived_at=timezone.now() if source_closed else None,
        evidence_url=job.source_url,
        confirmed_at=timezone.now() if closes else None,
    )
