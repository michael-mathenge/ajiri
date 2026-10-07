import re
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Application, Job, Notification

TEST_KEY = 'test-ingest-key'

# Mimics the shape of the MyJobMag feed: custom <position>/<company>/<location>
# tags beside the standard RSS ones. Written as UTF-8 BYTES (the en-dash is
# three bytes) because the real feed arrives as bytes over HTTP.
SAMPLE_FEED = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Jobs</title>
<item>
  <title>Sales Manager \u2013 Nairobi, Kenya at Acme</title>
  <position>Sales Manager \u2013 Nairobi, Kenya</position>
  <company>Acme Ltd</company>
  <location>Nairobi</location>
  <link>https://example.com/jobs/1</link>
  <description>Lead sales. Send your CV to hr@acme.co.ke</description>
  <pubDate>Fri, 21 Aug 2026 15:33:32 GMT</pubDate>
</item>
<item>
  <title>Receptionist at Beta</title>
  <position>Receptionist</position>
  <company>Beta Ltd</company>
  <location>Mombasa</location>
  <link>https://example.com/jobs/2</link>
  <description>Front desk duties.</description>
  <pubDate>Fri, 21 Aug 2026 16:00:00 GMT</pubDate>
</item>
<item>
  <title>Broken entry with no company</title>
  <link>https://example.com/jobs/3</link>
  <description>Missing company, should be skipped.</description>
</item>
</channel></rss>'''.encode('utf-8')


@override_settings(INGEST_API_KEY=TEST_KEY)
class IngestEndpointTests(TestCase):
    def setUp(self):
        self.url = reverse('ingest-feed')

    def post(self, body=SAMPLE_FEED, key=TEST_KEY, **extra):
        headers = {'HTTP_X_INGEST_KEY': key} if key is not None else {}
        headers.update(extra)
        return self.client.post(
            self.url, data=body, content_type='application/xml', **headers
        )

    def test_missing_key_is_rejected(self):
        self.assertEqual(self.post(key=None).status_code, 403)

    def test_wrong_key_is_rejected(self):
        self.assertEqual(self.post(key='nope').status_code, 403)

    @override_settings(INGEST_API_KEY='')
    def test_unset_server_key_disables_endpoint(self):
        # Even sending an empty key must NOT match an unset server key.
        self.assertEqual(self.post(key='').status_code, 403)

    def test_valid_feed_creates_jobs_and_skips_malformed(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['created'], 2)
        self.assertEqual(response.json()['skipped'], 1)
        self.assertEqual(Job.objects.count(), 2)

    def test_utf8_characters_survive_intact(self):
        self.post()
        job = Job.objects.get(source_url='https://example.com/jobs/1')
        self.assertEqual(job.title, 'Sales Manager \u2013 Nairobi, Kenya')

    def test_email_application_method_is_detected(self):
        self.post()
        job = Job.objects.get(source_url='https://example.com/jobs/1')
        self.assertEqual(job.application_method, 'email')
        self.assertEqual(job.application_email, 'hr@acme.co.ke')

    def test_reposting_same_feed_creates_no_duplicates(self):
        self.post()
        second = self.post()
        self.assertEqual(second.json()['created'], 0)
        self.assertEqual(Job.objects.count(), 2)

    def test_garbage_body_returns_400(self):
        self.assertEqual(self.post(body=b'not a feed at all').status_code, 400)

    def test_stale_user_token_cannot_break_endpoint(self):
        response = self.post(HTTP_AUTHORIZATION='Bearer expired.garbage.token')
        self.assertEqual(response.status_code, 200)


@override_settings(INGEST_API_KEY=TEST_KEY)
class SweepEndpointTests(TestCase):
    def setUp(self):
        self.url = reverse('sweep-matches')

    def post(self, key=TEST_KEY):
        headers = {'HTTP_X_INGEST_KEY': key} if key is not None else {}
        return self.client.post(self.url, **headers)

    def test_missing_or_wrong_key_is_rejected(self):
        self.assertEqual(self.post(key=None).status_code, 403)
        self.assertEqual(self.post(key='nope').status_code, 403)

    @override_settings(INGEST_API_KEY='')
    def test_unset_server_key_disables_endpoint(self):
        self.assertEqual(self.post(key='').status_code, 403)

    def test_valid_key_runs_sweep_and_creates_alert_for_strong_match(self):
        from profiles.models import Skill

        user = get_user_model().objects.create_user(
            email='seeker@example.com', password='pw-12345678',
            full_name='Seeker', phone_number='0700000000',
        )
        skill = Skill.objects.create(name='Django')
        user.profile.skills.add(skill)

        job = Job.objects.create(
            title='Backend Dev', company_name='Acme', description='Build APIs',
            source_url='https://example.com/jobs/sweep-1', source_name='test',
        )
        job.skills_required.add(skill)  # 1/1 skills matched = 100%, above the 70% threshold

        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['notified'], 1)
        self.assertEqual(Notification.objects.filter(user=user, job=job).count(), 1)

        # Running it again must not alert twice for the same (user, job) pair.
        self.assertEqual(self.post().json()['notified'], 0)


class ApplyFilenameTests(TestCase):
    """Generated CVs are served as static files, so names must be unguessable."""

    def test_generated_filenames_contain_a_random_token(self):
        user = get_user_model().objects.create_user(
            email='applicant@example.com', password='pw-12345678',
            full_name='Applicant', phone_number='0700000001',
        )
        job = Job.objects.create(
            title='Receptionist', company_name='Beta Ltd', description='Front desk',
            source_url='https://example.com/jobs/apply-1', source_name='test',
        )
        client = APIClient()
        client.force_authenticate(user=user)

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = client.post(reverse('job-apply', args=[job.pk]))

        self.assertEqual(response.status_code, 201)
        for field in ('generated_cv', 'generated_cover_letter'):
            filename = response.json()[field].rsplit('/', 1)[-1]
            self.assertRegex(filename, r'^[0-9a-f]{32}_', field)


class AdminPagesTests(TestCase):
    """Every admin page we rely on must render, with and without rows in it."""

    def test_admin_pages_render(self):
        admin_user = get_user_model().objects.create_superuser(
            email='root@example.com', password='pw-12345678'
        )
        applicant = get_user_model().objects.create_user(
            email='admin-test@example.com', password='pw-12345678',
            full_name='Admin Test', phone_number='0700000002',
        )
        job = Job.objects.create(
            title='Admin Test Job', company_name='Gamma Ltd', description='x',
            source_url='https://example.com/jobs/admin-1', source_name='test',
        )
        Notification.objects.create(user=applicant, job=job, match_score=80)
        Application.objects.create(
            user=applicant, job=job, application_method='external_link',
            generated_cv='applications/cvs/x.docx',
            generated_cover_letter='applications/cover_letters/x.docx',
        )
        self.client.force_login(admin_user)

        for path in (
            '/admin/',
            '/admin/accounts/user/',
            '/admin/profiles/profile/',
            '/admin/jobs/job/',
            '/admin/jobs/job/add/',
            '/admin/jobs/application/',
            '/admin/jobs/application/add/',
            '/admin/jobs/notification/',
            '/admin/jobs/notification/add/',
        ):
            self.assertEqual(self.client.get(path).status_code, 200, path)
