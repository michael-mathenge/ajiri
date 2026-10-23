from datetime import timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import User
from .models import (
    Job,
    JobPublication,
    EmployerOrganisation,
    EmployerJobDraft,
    EmployerReview,
)
from .freshness import eligible_jobs, archive_expired
from .feed_deadlines import record


@override_settings(
    JOB_FRESHNESS_ENFORCED=True,
    EMPLOYER_POSTING_ENABLED=True,
    PUBLIC_JOBS_ENABLED=True,
    PUBLIC_JOB_ORIGIN="https://jobs.example.invalid",
)
class JobFreshnessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.invalid", password="Synthetic-Strong-892!"
        )
        self.owner.profile.email_verified_at = timezone.now()
        self.owner.profile.verified_email = self.owner.email
        self.owner.profile.save()
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def job(self):
        return Job.objects.create(
            title="Synthetic developer",
            company_name="Synthetic organisation",
            source_url=f"https://example.invalid/jobs/{Job.objects.count()}",
            source_name="test",
            description="A detailed synthetic description. " * 8,
        )

    def test_unknown_expired_and_exact_boundary_hidden_everywhere(self):
        unknown = self.job()
        expired = self.job()
        JobPublication.objects.create(
            job=expired, origin="rss", status="published", closes_at=timezone.now()
        )
        for job in (unknown, expired):
            self.assertEqual(self.client.get(f"/api/jobs/{job.pk}/").status_code, 404)
            self.assertEqual(
                self.client.post(f"/api/jobs/{job.pk}/apply/", {}).status_code, 404
            )
        self.assertEqual(self.client.get("/api/jobs/").data["count"], 0)
        self.assertEqual(archive_expired(), 1)
        expired.publication.refresh_from_db()
        self.assertEqual(expired.publication.status, "archived")
        self.assertEqual(Job.objects.count(), 2)

    def test_source_deadlines_are_explicit_and_archives_never_reopen(self):
        future = timezone.now() + timedelta(days=2)
        for raw in (None, "tomorrow", "2027-02-01", ""):
            job = self.job()
            record(job, {"closing_date": raw})
            self.assertFalse(eligible_jobs().filter(pk=job.pk).exists())
        job = self.job()
        record(job, {"closing_date": future.isoformat()})
        self.assertTrue(eligible_jobs().filter(pk=job.pk).exists())
        record(
            job, {"closing_date": (timezone.now() - timedelta(seconds=1)).isoformat()}
        )
        record(job, {"closing_date": future.isoformat()})
        self.assertFalse(eligible_jobs().filter(pk=job.pk).exists())

    def test_staff_reviews_and_owner_withdrawal(self):
        organisation = EmployerOrganisation.objects.create(
            owner=self.owner, name="Synthetic team", website="https://example.invalid"
        )
        draft = EmployerJobDraft.objects.create(
            organisation=organisation,
            title="Synthetic engineer",
            description="Detailed responsibilities for a synthetic role. " * 8,
            location="Nairobi, Kenya",
            application_url="https://example.invalid/jobs/application",
            closes_at=timezone.now() + timedelta(days=2),
        )
        review = {
            "approve": True,
            "reason": "Synthetic independent review",
            "revision": 1,
        }
        self.assertEqual(
            self.client.post(
                f"/api/jobs/employers/drafts/{draft.pk}/review/", review
            ).status_code,
            403,
        )
        staff = User.objects.create_user(
            email="reviewer@example.invalid", is_staff=True
        )
        self.client.force_authenticate(staff)
        self.assertEqual(
            self.client.post(
                f"/api/jobs/employers/drafts/{draft.pk}/review/", review
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                f"/api/jobs/employers/organisations/{organisation.pk}/review/", review
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                f"/api/jobs/employers/drafts/{draft.pk}/review/", review
            ).status_code,
            200,
        )
        draft.refresh_from_db()
        self.assertTrue(eligible_jobs().filter(pk=draft.job_id).exists())
        self.assertEqual(EmployerReview.objects.count(), 1)
        self.assertEqual(
            self.client.post(
                f"/api/jobs/employers/drafts/{draft.pk}/review/", review
            ).status_code,
            409,
        )
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.post(
                f"/api/jobs/employers/drafts/{draft.pk}/withdraw/", {}
            ).status_code,
            200,
        )
        self.assertFalse(eligible_jobs().filter(pk=draft.job_id).exists())

    def test_unverified_account_and_other_owner_cannot_submit(self):
        organisation = EmployerOrganisation.objects.create(
            owner=self.owner, name="Synthetic", website="https://example.invalid"
        )
        other = User.objects.create_user(email="other@example.invalid")
        self.client.force_authenticate(other)
        self.assertEqual(
            self.client.get("/api/jobs/employers/organisations/").status_code, 403
        )
        other.profile.email_verified_at = timezone.now()
        other.profile.verified_email = other.email
        other.profile.save()
        other.refresh_from_db()
        self.client.force_authenticate(other)
        response = self.client.post(
            "/api/jobs/employers/drafts/",
            {
                "organisation": organisation.pk,
                "title": "Role",
                "description": "Text " * 30,
                "location": "Kenya",
                "application_url": "https://example.invalid/role",
                "closes_at": (timezone.now() + timedelta(days=1)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(EmployerJobDraft.objects.exists())

    def test_expiry_is_checked_on_each_request_without_waiting_for_archiver(self):
        job = self.job()
        closes = timezone.now() + timedelta(hours=1)
        JobPublication.objects.create(
            job=job, origin="rss", status="published", closes_at=closes, confirmed_at=timezone.now()
        )
        self.assertEqual(self.client.get(f"/api/jobs/{job.pk}/").status_code, 200)
        from unittest.mock import patch

        with patch("jobs.freshness.timezone.now", return_value=closes):
            self.assertEqual(self.client.get(f"/api/jobs/{job.pk}/").status_code, 404)
            self.assertEqual(self.client.get("/sitemap-jobs-1.xml").status_code, 200)
            self.assertNotIn(
                f"/vacancies/{job.pk}/",
                self.client.get("/sitemap-jobs-1.xml").content.decode(),
            )
        self.assertEqual(job.publication.status, "published")

    def test_changed_rss_url_is_not_current_evidence_and_does_not_mutate_history(self):
        from types import SimpleNamespace
        from .ingestion import ingest_feed

        job = self.job()
        JobPublication.objects.create(
            job=job,
            origin="rss",
            status="published",
            closes_at=timezone.now() + timedelta(days=1),
            confirmed_at=timezone.now(),
        )
        ingest_feed(
            SimpleNamespace(
                entries=[
                    {
                        "link": job.source_url,
                        "title": "A different role",
                        "company": job.company_name,
                        "description": job.description,
                        "closing_date": (
                            timezone.now() + timedelta(days=2)
                        ).isoformat(),
                    }
                ]
            )
        )
        job.refresh_from_db()
        self.assertEqual(job.title, "Synthetic developer")
        self.assertFalse(eligible_jobs().filter(pk=job.pk).exists())

    def test_matching_never_alerts_an_unverified_job(self):
        from unittest.mock import patch
        from .matching import notify_matching_profiles

        with patch("jobs.matching.send_match_email") as send:
            self.assertEqual(notify_matching_profiles(self.job()), 0)
            send.assert_not_called()

    def test_employer_erasure_stops_before_writes_without_a_scoped_review(self):
        from accounts.erasure import inventory
        from django.core.management.base import CommandError

        EmployerOrganisation.objects.create(
            owner=self.owner,
            name="Synthetic company",
            website="https://example.invalid",
        )
        with self.assertRaisesMessage(CommandError, "reviewed erasure plan"):
            inventory(self.owner)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_active)

    def test_staff_can_reject_a_job_without_first_approving_its_organisation(self):
        organisation = EmployerOrganisation.objects.create(
            owner=self.owner, name="Synthetic", website="https://example.invalid"
        )
        draft = EmployerJobDraft.objects.create(
            organisation=organisation,
            title="Synthetic",
            description="Text " * 30,
            location="Kenya",
            application_url="https://example.invalid/reject",
            closes_at=timezone.now() + timedelta(days=1),
        )
        staff = User.objects.create_user(
            email="staff-reject@example.invalid", is_staff=True
        )
        self.client.force_authenticate(staff)
        self.assertEqual(
            self.client.post(
                f"/api/jobs/employers/drafts/{draft.pk}/review/",
                {
                    "approve": False,
                    "reason": "Synthetic insufficient evidence",
                    "revision": 1,
                },
            ).status_code,
            200,
        )
        self.assertFalse(Job.objects.exists())

    def test_explicit_closure_and_earlier_deadline_override_a_future_date(self):
        job = self.job()
        later = timezone.now() + timedelta(days=5)
        earlier = timezone.now() + timedelta(days=1)
        record(job, {"closing_date": later.isoformat()})
        record(job, {"closing_date": earlier.isoformat()})
        record(job, {"closing_date": later.isoformat()})
        job.publication.refresh_from_db()
        self.assertEqual(job.publication.closes_at, earlier)
        record(job, {"status": "closed", "closing_date": later.isoformat()})
        self.assertFalse(eligible_jobs().filter(pk=job.pk).exists())

    def test_employer_http_creation_cannot_self_publish_or_omit_future_deadline(self):
        org_response = self.client.post(
            "/api/jobs/employers/organisations/",
            {
                "name": "Synthetic employer",
                "website": "https://example.invalid",
                "status": "approved",
            },
        )
        self.assertEqual(org_response.status_code, 201)
        self.assertEqual(org_response.data["status"], "pending")
        payload = {
            "organisation": org_response.data["id"],
            "title": "Synthetic opportunity",
            "description": "A full synthetic description. " * 10,
            "location": "Nairobi, Kenya",
            "application_url": "https://example.invalid/careers/opportunity",
            "status": "published",
        }
        self.assertEqual(
            self.client.post("/api/jobs/employers/drafts/", payload).status_code, 400
        )
        payload["closes_at"] = (timezone.now() - timedelta(seconds=1)).isoformat()
        self.assertEqual(
            self.client.post("/api/jobs/employers/drafts/", payload).status_code, 400
        )
        payload["closes_at"] = (timezone.now() + timedelta(days=1)).isoformat()
        response = self.client.post("/api/jobs/employers/drafts/", payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "pending")
        self.assertFalse(Job.objects.exists())

    def test_future_deadline_does_not_keep_old_rss_confirmation_visible(self):
        from unittest.mock import patch
        job=self.job()
        now=timezone.now()
        record(job, {'closing_date':(now+timedelta(days=5)).isoformat()})
        self.assertTrue(eligible_jobs().filter(pk=job.pk).exists())
        with patch('jobs.freshness.timezone.now',return_value=now+timedelta(hours=25)):
            self.assertFalse(eligible_jobs().filter(pk=job.pk).exists())
            self.assertEqual(archive_expired(),1)
        job.publication.refresh_from_db()
        self.assertEqual(job.publication.status,'archived')

    def test_distinct_reviewed_jobs_can_share_one_official_application_portal(self):
        organisation=EmployerOrganisation.objects.create(owner=self.owner,name='Synthetic employer',website='https://example.invalid',status='approved')
        staff=User.objects.create_user(email='portal-reviewer@example.invalid',is_staff=True)
        self.client.force_authenticate(staff)
        jobs=[]
        for title in ['Synthetic engineer','Synthetic designer']:
            draft=EmployerJobDraft.objects.create(organisation=organisation,title=title,description='Detailed synthetic responsibilities. '*8,
                location='Nairobi, Kenya',application_url='https://example.invalid/application-portal',closes_at=timezone.now()+timedelta(days=2))
            self.assertEqual(self.client.post(f'/api/jobs/employers/drafts/{draft.pk}/review/',
                {'approve':True,'reason':'Synthetic independent review','revision':1}).status_code,200)
            draft.refresh_from_db()
            jobs.append(draft.job)
        self.assertNotEqual(jobs[0].source_url,jobs[1].source_url)
        self.assertEqual(jobs[0].application_target,jobs[1].application_target)
        self.assertEqual(self.client.get(f'/api/jobs/{jobs[0].pk}/').data['source_url'],'https://example.invalid/application-portal')

    def test_unsafe_feed_destinations_are_not_imported(self):
        from types import SimpleNamespace
        from .ingestion import ingest_feed
        for link in ['javascript:alert(1)','ftp://example.invalid/jobs','https://user:pass@example.invalid/jobs',7]:
            result=ingest_feed(SimpleNamespace(entries=[{'link':link,'title':'Synthetic','company':'Synthetic','description':'Text '*30}]))
            self.assertEqual(result['created'],0)
        self.assertFalse(Job.objects.exists())

    def test_posting_kill_switch_preserves_reads_and_owner_withdrawal(self):
        organisation=EmployerOrganisation.objects.create(owner=self.owner,name='Synthetic',website='https://example.invalid',status='approved')
        job=self.job()
        JobPublication.objects.create(job=job,origin='employer',status='published',organisation=organisation,closes_at=timezone.now()+timedelta(days=1))
        draft=EmployerJobDraft.objects.create(organisation=organisation,job=job,status='published',title=job.title,
            description=job.description,location='Kenya',application_url='https://example.invalid/portal',closes_at=timezone.now()+timedelta(days=1))
        with override_settings(EMPLOYER_POSTING_ENABLED=False):
            self.assertEqual(self.client.get('/api/jobs/employers/drafts/').status_code,200)
            self.assertEqual(self.client.post('/api/jobs/employers/organisations/',{'name':'Blocked','website':'https://example.invalid'}).status_code,403)
            self.owner.profile.email_verified_at=None
            self.owner.profile.save()
            self.assertEqual(self.client.post(f'/api/jobs/employers/drafts/{draft.pk}/withdraw/',{}).status_code,200)
        self.assertFalse(eligible_jobs().filter(pk=job.pk).exists())

    def test_busy_review_rolls_back_and_returns_a_sanitized_reload_message(self):
        from unittest.mock import patch
        from django.db import OperationalError
        organisation=EmployerOrganisation.objects.create(owner=self.owner,name='Synthetic',website='https://example.invalid')
        staff=User.objects.create_user(email='busy-reviewer@example.invalid',is_staff=True)
        self.client.force_authenticate(staff)
        with patch('jobs.employer_views.EmployerOrganisation.objects.filter',side_effect=OperationalError('synthetic-private-sql')):
            response=self.client.post(f'/api/jobs/employers/organisations/{organisation.pk}/review/',{'approve':True,'reason':'Synthetic review'})
        self.assertEqual(response.status_code,503)
        self.assertNotIn('synthetic-private-sql',str(response.data))
        organisation.refresh_from_db()
        self.assertEqual(organisation.status,'pending')
