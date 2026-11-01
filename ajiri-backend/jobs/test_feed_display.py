import json
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from .feed_display import NOTICE, browse_jobs, supplemental_jobs
from .freshness import eligible_jobs
from .models import Job, JobPublication, Application


@override_settings(JOB_FRESHNESS_ENFORCED=True, JOB_FEED_DISPLAY_ENABLED=True)
class FeedDisplayTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='feed@example.invalid')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.at = timezone.now()

    def job(self, **values):
        return Job.objects.create(title='Python developer', company_name='Synthetic',
            description='Synthetic role', source_name='MyJobMag Kenya',
            source_url=f'https://example.invalid/{Job.objects.count()}', **values)

    def test_switch_changes_only_browsing_and_serialized_contract(self):
        job = self.job(external_application_url='https://example.invalid/apply-elsewhere')
        eligible = list(eligible_jobs().values_list('pk', flat=True))
        for enabled in (False, True):
            with self.settings(JOB_FEED_DISPLAY_ENABLED=enabled):
                self.assertEqual(list(eligible_jobs().values_list('pk', flat=True)), eligible)
                response = self.client.get('/api/jobs/')
                self.assertEqual(response.data['count'], int(enabled))
                detail = self.client.get(f'/api/jobs/{job.pk}/')
                self.assertEqual(detail.status_code, 200 if enabled else 404)
                if enabled:
                    for data in (response.data['results'][0], detail.data):
                        self.assertTrue(data['display_only'])
                        self.assertFalse(data['can_apply'])
                        self.assertEqual(data['display_notice'], NOTICE)
                        self.assertEqual(data['original_source_url'], job.source_url)
                        self.assertIsNone(data['posted_at'])
                for path in ('apply/', 'generate-cover-letter/'):
                    method = self.client.post if path == 'apply/' else self.client.get
                    self.assertEqual(method(f'/api/jobs/{job.pk}/{path}').status_code, 404)

    def test_candidate_boundaries_and_archive_allowlist(self):
        missing = self.job()
        stale = self.job(posted_at=self.at-timedelta(days=40))
        JobPublication.objects.create(job=stale, origin='rss', status='published',
            closes_at=self.at+timedelta(days=1), confirmed_at=self.at-timedelta(days=40))
        allowed = {missing.pk, stale.pk}
        for reason in ('availability_not_verified', 'deadline_or_confirmation_expired',
                       'source_closed', 'source_closed_or_deadline_passed', 'employer_withdrew', 'unknown'):
            job = self.job()
            JobPublication.objects.create(job=job, origin='rss', status='archived', archive_reason=reason)
            if reason in ('availability_not_verified', 'deadline_or_confirmation_expired'):
                allowed.add(job.pk)
        for values in ({'is_active': False}, {'is_flagged_scam': True},
                       {'posted_at': self.at+timedelta(seconds=1)}):
            self.job(**values)
        for origin, closes in (('employer', None), ('rss', self.at), ('rss', self.at-timedelta(days=1))):
            job = self.job()
            JobPublication.objects.create(job=job, origin=origin, closes_at=closes)
        unrelated = self.job()
        unrelated.source_name = 'unrecognized'
        unrelated.save()
        self.assertEqual(set(supplemental_jobs(at=self.at).values_list('pk', flat=True)), allowed)

    def test_eligible_rows_not_duplicated_and_filters_paginate(self):
        job = self.job(posted_at=self.at)
        JobPublication.objects.create(job=job, origin='rss', status='published',
            closes_at=self.at+timedelta(days=1), confirmed_at=self.at)
        for _ in range(21):
            self.job(posted_at=self.at)
        response = self.client.get('/api/jobs/?title=Python')
        self.assertEqual(response.data['count'], 22)
        rows = response.data['results'] + self.client.get(response.data['next']).data['results']
        self.assertEqual(len({row['id'] for row in rows}), 22)
        eligible = next(row for row in rows if row['id'] == job.pk)
        self.assertFalse(eligible['display_only'])
        self.assertTrue(eligible['can_apply'])
        self.assertEqual(eligible['display_notice'], '')
        self.assertEqual(self.client.get('/api/jobs/?title=Absent').data['count'], 0)

    def test_switch_preserves_positive_and_negative_eligibility(self):
        self.job()
        verified = self.job()
        JobPublication.objects.create(job=verified, origin='rss', status='published',
            closes_at=self.at+timedelta(days=1), confirmed_at=self.at)
        for enabled in (False, True):
            with self.settings(JOB_FEED_DISPLAY_ENABLED=enabled):
                self.assertEqual(set(eligible_jobs(at=self.at).values_list('pk', flat=True)), {verified.pk})

    def test_existing_package_authorization_and_email_send_stay_blocked(self):
        from .application_packages import require_editable, PackageConflict
        from .send_authorization import build_plan
        job = self.job()
        app = Application.objects.create(user=self.user, job=job, status='ready_for_review',
            application_method='email')
        for enabled in (False, True):
            with self.settings(JOB_FEED_DISPLAY_ENABLED=enabled):
                with self.assertRaises(PackageConflict):
                    require_editable(app)
                with self.assertRaises(PackageConflict):
                    build_plan(self.user, app)
                self.assertEqual(self.client.post(f'/api/jobs/applications/{app.pk}/send/').status_code, 409)

    def test_matching_cannot_create_or_send_alerts(self):
        from .matching import notify_matching_profiles
        job = self.job()
        for enabled in (False, True):
            with self.settings(JOB_FEED_DISPLAY_ENABLED=enabled), patch('jobs.matching.send_match_email') as send:
                self.assertEqual(notify_matching_profiles(job), 0)
                send.assert_not_called()

    @override_settings(SAVED_SEARCHES_ENABLED=True, SAVED_SEARCH_EMAIL_TEST_CAPTURE=True,
        ACCOUNT_EMAIL_TEST_CAPTURE=True, REAL_EMAIL_ENABLED=False,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_unverified_jobs_never_enter_saved_search_or_email(self):
        import uuid
        from profiles.alert_consent import record_choice
        from .models import SavedSearch, SavedSearchMatch, DeliveryAttempt
        from .saved_searches import reset_windows, collect_due
        from .saved_search_email import capture_due_email
        profile = self.user.profile
        profile.email_verified_at = self.at
        profile.verified_email = self.user.email
        profile.notify_in_app = True
        profile.save()
        record_choice(self.user, True, uuid.uuid4())
        start = self.at-timedelta(days=3)
        profile.alert_consent_events.update(created_at=start-timedelta(days=1))
        job = self.job()
        Job.objects.filter(pk=job.pk).update(scraped_at=start+timedelta(hours=1))
        for enabled in (False, True):
            search = SavedSearch(owner=self.user, name='Synthetic', q='Python',
                in_app_frequency='daily', email_frequency='daily')
            reset_windows(search, start)
            search.save()
            with self.settings(JOB_FEED_DISPLAY_ENABLED=enabled), patch('jobs.brevo_transport.BrevoTransport.send') as send:
                self.assertEqual(collect_due(search.pk), [])
                self.assertEqual(capture_due_email(search.pk), [])
                send.assert_not_called()
        self.assertFalse(SavedSearchMatch.objects.exists())
        self.assertFalse(DeliveryAttempt.objects.exists())

    def test_counts_are_select_only_and_match_browse(self):
        self.job(posted_at=self.at-timedelta(days=1))
        self.job()
        self.job(is_flagged_scam=True)
        def select_only(execute, sql, params, many, context):
            self.assertTrue(sql.lstrip().upper().startswith('SELECT'), sql)
            return execute(sql, params, many, context)
        out = StringIO()
        with connection.execute_wrapper(select_only):
            call_command('job_feed_display_counts', stdout=out)
        data = json.loads(out.getvalue())
        self.assertEqual(data['total'], 3)
        self.assertEqual(data['scam_flagged'], 1)
        self.assertEqual(data['eligible'], 0)
        self.assertEqual(data['supplemental_unverified'], 2)
        self.assertEqual(data['browse_off'], 0)
        self.assertEqual(data['browse_on'], browse_jobs().count())
        self.assertEqual(data['supplemental_posted_within_14_days'], 1)

    def test_anonymous_cannot_browse(self):
        job = self.job()
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/jobs/').status_code, 401)
        self.assertEqual(self.client.get(f'/api/jobs/{job.pk}/').status_code, 401)

    def test_scam_is_hidden_on_both_endpoints(self):
        job = self.job(is_flagged_scam=True)
        self.assertEqual(self.client.get('/api/jobs/').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/jobs/{job.pk}/').status_code, 404)

    def test_public_pages_and_sitemaps_stay_on_eligibility(self):
        from .public_views import listings
        job = self.job()
        self.assertTrue(browse_jobs().filter(pk=job.pk).exists())
        self.assertFalse(listings().filter(pk=job.pk).exists())


# Exercise established consent, provider and employer decisions with the switch
# on as well as the existing suite's default-off coverage.
from . import test_alert_delivery as alert_cases
from . import test_saved_searches as search_cases
from . import test_freshness as freshness_cases


@override_settings(JOB_FEED_DISPLAY_ENABLED=True)
class FeedDisplayAlertRegressionTests(alert_cases.AlertDeliveryTests):
    pass


@override_settings(JOB_FEED_DISPLAY_ENABLED=True)
class FeedDisplaySearchRegressionTests(search_cases.SavedSearchEmailTests):
    pass


@override_settings(JOB_FEED_DISPLAY_ENABLED=True, JOB_FRESHNESS_ENFORCED=True,
    EMPLOYER_POSTING_ENABLED=True, PUBLIC_JOBS_ENABLED=True, PUBLIC_JOB_ORIGIN='https://jobs.example.invalid')
class FeedDisplayEmployerRegressionTests(TestCase):
    setUp = freshness_cases.JobFreshnessTests.setUp
    job = freshness_cases.JobFreshnessTests.job
    # Reuse only employer checks: browse visibility is intentionally different.
    test_staff_reviews_and_owner_withdrawal = freshness_cases.JobFreshnessTests.test_staff_reviews_and_owner_withdrawal
    test_unverified_account_and_other_owner_cannot_submit = freshness_cases.JobFreshnessTests.test_unverified_account_and_other_owner_cannot_submit
