import json
import re
from datetime import timedelta
from unittest.mock import patch
from xml.etree import ElementTree
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from .models import Job, Application
from .public_views import job_path


@override_settings(
    PUBLIC_JOBS_ENABLED=True, PUBLIC_JOB_ORIGIN="https://public.example.invalid"
)
class PublicJobTests(TestCase):
    def job(self, **changes):
        values = dict(
            title="Synthetic developer",
            company_name="Synthetic team",
            description="Build tested systems.",
            requirements="Python experience.",
            location="Nairobi, Kenya",
            source_name="test",
            source_url=f"https://example.invalid/{Job.objects.count()}",
            posted_at=timezone.now() - timedelta(days=1),
            application_method="email",
            application_email="private-employer@example.invalid",
        )
        values.update(changes)
        return Job.objects.create(**values)

    def structured(self, response):
        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>',
            response.content.decode(),
            re.S,
        )
        return json.loads(match.group(1)) if match else None

    def test_anonymous_page_has_truthful_bounded_metadata_without_private_fields(self):
        job = self.job()
        response = self.client.get(job_path(job))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("private-employer", response.content.decode())
        data = self.structured(response)
        self.assertEqual(data["title"], job.title)
        self.assertEqual(data["datePosted"], job.posted_at.isoformat())
        self.assertEqual(data["hiringOrganization"]["name"], job.company_name)
        self.assertEqual(data["jobLocation"]["address"]["addressCountry"], "KE")
        self.assertNotIn("validThrough", data)
        self.assertNotIn("baseSalary", data)
        self.assertNotIn("directApply", data)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn("csrftoken", response.cookies)
        self.assertLess(len(response.content), 12000)
        self.assertEqual(self.client.get("/api/jobs/").status_code, 401)

    def test_missing_or_future_date_unknown_country_remote_and_truncated_content_omit_schema(
        self,
    ):
        for change in (
            {"posted_at": None},
            {"posted_at": timezone.now() + timedelta(days=1)},
            {"location": "Nairobi"},
            {"location": "Remote, Kenya"},
            {"description": "x" * 12001},
        ):
            with self.subTest(change=list(change)):
                response = self.client.get(job_path(self.job(**change)))
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(self.structured(response))
                if "description" in change:
                    self.assertContains(response, "Description shortened")

    def test_html_jsonld_escape_and_external_link_scheme_are_safe(self):
        job = self.job(
            title="Engineer <script>alert(1)</script>",
            description="A & B </script><script>doBad()</script>",
            source_url="https://example.invalid/safe",
        )
        response = self.client.get(job_path(job))
        body = response.content.decode()
        self.assertNotIn("<script>alert", body)
        self.assertNotIn("<script>doBad", body)
        self.assertEqual(body.count("<script "), 1)
        self.assertIn("A &amp; B", body)
        self.assertIn("A &amp; B", self.structured(response)["description"])
        job.source_url = "javascript:alert(1)"
        job.save()
        response = self.client.get(job_path(job))
        self.assertNotIn("javascript:", response.content.decode())
        self.assertIsNone(self.structured(response))

    def test_inactive_scam_missing_and_disabled_pages_are_unavailable(self):
        for change in (
            {"is_active": False},
            {"is_flagged_scam": True},
            {"title": "   "},
        ):
            self.assertEqual(
                self.client.get(job_path(self.job(**change))).status_code, 404
            )
        self.assertEqual(self.client.get("/vacancies/99999/missing/").status_code, 404)
        job = self.job()
        with override_settings(PUBLIC_JOBS_ENABLED=False):
            for path in (
                job_path(job),
                "/sitemap.xml",
                "/sitemap-jobs-1.xml",
                "/robots.txt",
            ):
                self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.post(job_path(job)).status_code, 405)

    def test_canonical_redirect_does_not_trust_request_host_or_source(self):
        job = self.job()
        response = self.client.get(
            reverse("public-job-detail", kwargs={"pk": job.pk, "slug": "wrong"})
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response["Location"], "https://public.example.invalid" + job_path(job)
        )
        for origin in (
            "http://unsafe.invalid",
            "https://user:pass@example.invalid",
            "https://example.invalid/extra",
        ):
            with override_settings(PUBLIC_JOB_ORIGIN=origin):
                self.assertEqual(self.client.get(job_path(job)).status_code, 404)

    def test_authenticated_visitors_get_identical_job_only_content(self):
        job = self.job()
        anonymous = self.client.get(job_path(job)).content
        user = User.objects.create_user(
            email="private-person@example.invalid", full_name="Private Synthetic Name"
        )
        user.profile.bio = "Private synthetic profile content"
        user.profile.save()
        Application.objects.create(
            user=user, job=job, email_body="Private synthetic application"
        )
        self.client.force_login(user)
        response = self.client.get(job_path(job))
        self.assertEqual(response.content, anonymous)
        for value in (
            "Private Synthetic Name",
            "Private synthetic profile",
            "Private synthetic application",
            user.email,
        ):
            self.assertNotIn(value, response.content.decode())

    def test_sitemaps_page_deterministically_and_exclude_unavailable_jobs(self):
        visible = [self.job(title=f"Visible {number}") for number in range(3)]
        self.job(is_active=False)
        self.job(is_flagged_scam=True)
        self.job(title=" ")
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        with patch("jobs.public_views.PAGE_SIZE", 2):
            root = ElementTree.fromstring(self.client.get("/sitemap.xml").content)
            locations = [x.text for x in root.findall("s:sitemap/s:loc", ns)]
            self.assertEqual(len(locations), 2)
            actual = []
            for page in (1, 2):
                response = self.client.get(f"/sitemap-jobs-{page}.xml")
                self.assertEqual(response.status_code, 200)
                tree = ElementTree.fromstring(response.content)
                actual.extend(x.text for x in tree.findall("s:url/s:loc", ns))
            self.assertEqual(
                actual,
                ["https://public.example.invalid" + job_path(job) for job in visible],
            )
            self.assertEqual(self.client.get("/sitemap-jobs-3.xml").status_code, 404)
        robots = self.client.get("/robots.txt").content.decode()
        self.assertIn("Disallow: /api/", robots)
        self.assertIn("Sitemap: https://public.example.invalid/sitemap.xml", robots)
