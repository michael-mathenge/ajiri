"""Synthetic source-contract evidence; no live feed access or ingestion."""
from datetime import datetime, timedelta, timezone as dt_timezone

import feedparser
from django.test import TestCase, override_settings
from django.utils import timezone

from .feed_deadlines import deadline, record
from .freshness import job_is_eligible
from .models import Job, JobPublication


class MyJobMagExpiryTests(TestCase):
    source = {"source_name": "MyJobMag Kenya", "source_url": "https://www.myjobmag.co.ke/synthetic-job"}
    expiry = "Fri, 31 Dec 2099 00:00:00 GMT"

    def job(self, **changes):
        values = {**self.source, "title": "Synthetic vacancy", "company_name": "Synthetic employer",
                  "description": "Synthetic fixture", "posted_at": timezone.now()}
        values.update(changes)
        return Job.objects.create(**values)

    def test_feedparser_normalizes_the_observed_xml_field(self):
        feed = feedparser.parse(
            '<rss version="2.0"><channel><item><expiryDate>' + self.expiry
            + '</expiryDate></item></channel></rss>'
        )
        self.assertEqual(deadline(feed.entries[0], **self.source),
                         datetime(2099, 12, 31, tzinfo=dt_timezone.utc))

    def test_numeric_offset_keeps_the_explicit_instant(self):
        self.assertEqual(deadline({"expirydate": "Fri, 31 Dec 2099 03:00:00 +0300"}, **self.source),
                         datetime(2099, 12, 31, 3, tzinfo=dt_timezone(timedelta(hours=3))))

    def test_missing_ambiguous_and_invalid_expiries_fail_closed(self):
        for value in (None, "", 123, "2099-12-31", "Fri, 31 Dec 2099 00:00:00",
                      "Fri, 31 Dec 2099 00:00:00 -0000", "Fri, 31 Dec 2099 00:00:00 CST",
                      "Fri, 32 Dec 2099 00:00:00 GMT", "Fri, 31 Dec 2099 00:00:00 +2460",
                      "Closing on " + self.expiry, "x" * 81):
            with self.subTest(value=value):
                self.assertIsNone(deadline({"expirydate": value}, **self.source))

    def test_other_sources_and_hosts_do_not_gain_this_contract(self):
        for source in ({}, {**self.source, "source_name": "Other source"},
                       {**self.source, "source_url": "https://www.myjobmag.co.ke.example.invalid/job"},
                       {**self.source, "source_url": "https://[invalid"}):
            with self.subTest(source=source):
                self.assertIsNone(deadline({"expirydate": self.expiry}, **source))

    def test_existing_explicit_iso_field_keeps_priority(self):
        entry = {"closing_date": "2099-12-01T12:00:00+03:00", "expirydate": self.expiry}
        self.assertEqual(deadline(entry, **self.source), datetime.fromisoformat(entry["closing_date"]))
        entry["closing_date"] = "2099-12-01"
        self.assertIsNone(deadline(entry, **self.source))

    def test_description_prose_is_never_deadline_evidence(self):
        self.assertIsNone(deadline({"description": "Closing " + self.expiry}, **self.source))

    @override_settings(JOB_FRESHNESS_ENFORCED=True)
    def test_new_explicit_evidence_uses_existing_freshness_and_scam_gates(self):
        job = self.job()
        publication = record(job, {"expirydate": self.expiry})
        self.assertEqual(publication.status, "published")
        self.assertEqual(publication.closes_at, datetime(2099, 12, 31, tzinfo=dt_timezone.utc))
        self.assertTrue(job_is_eligible(job))
        job.is_flagged_scam = True
        job.save(update_fields=["is_flagged_scam"])
        self.assertFalse(job_is_eligible(job))
        job.is_flagged_scam = False
        job.is_active = False
        job.save(update_fields=["is_flagged_scam", "is_active"])
        self.assertFalse(job_is_eligible(job))

    def test_unverified_row_can_receive_evidence_but_deadline_never_extends(self):
        job = self.job()
        publication = JobPublication.objects.create(job=job, origin="rss", status="unverified")
        record(job, {"expirydate": self.expiry})
        publication.refresh_from_db()
        self.assertEqual(publication.status, "published")
        record(job, {"expirydate": "Fri, 31 Dec 2100 00:00:00 GMT"})
        publication.refresh_from_db()
        self.assertEqual(publication.closes_at.year, 2099)

    def test_archived_rows_are_never_revived(self):
        job = self.job()
        publication = JobPublication.objects.create(job=job, origin="rss", status="archived",
                                                   archive_reason="availability_not_verified")
        record(job, {"expirydate": self.expiry})
        publication.refresh_from_db()
        self.assertEqual(publication.status, "archived")
        self.assertIsNone(publication.closes_at)

    @override_settings(JOB_FRESHNESS_ENFORCED=True)
    def test_expired_or_closed_entry_never_becomes_eligible(self):
        job = self.job()
        record(job, {"expirydate": "Sat, 1 Jan 2000 00:00:00 GMT"})
        self.assertFalse(job_is_eligible(job))
        record(job, {"expirydate": self.expiry, "status": "closed"})
        self.assertFalse(job_is_eligible(job))

    def test_employer_evidence_is_not_replaced(self):
        job = self.job()
        publication = JobPublication.objects.create(job=job, origin="employer", status="unverified")
        record(job, {"expirydate": self.expiry})
        publication.refresh_from_db()
        self.assertEqual(publication.status, "unverified")
        self.assertIsNone(publication.closes_at)
