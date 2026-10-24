"""Synthetic staff reviews preserve source evidence and applicant documents."""
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import CommandError
from django.db import OperationalError, connections
from django.test import Client, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.erasure import inventory
from .freshness import eligible_jobs
from .models import Application, Job, JobModerationReview, JobPublication
from .moderation import fingerprint, review, snapshot, StaleReview


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
                   JOB_FRESHNESS_ENFORCED=True)
class ModerationTests(TransactionTestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(email='reviewer@example.invalid', is_staff=True)
        self.staff.user_permissions.add(Permission.objects.get(codename='change_job'))
        self.other = User.objects.create_user(email='applicant@example.invalid')
        self.job = Job.objects.create(title='Synthetic analyst', company_name='Synthetic employer',
            source_url='https://example.invalid/review', source_name='synthetic',
            is_flagged_scam=True, scam_flags='Requires source review')
        self.pub = JobPublication.objects.create(job=self.job, origin='rss', status='published',
            closes_at=timezone.now()+timedelta(days=2), confirmed_at=timezone.now())
        self.url = reverse('admin:jobs_job_moderate', args=[self.job.pk])
        self.client.force_login(self.staff)

    def data(self, **changes):
        self.job.refresh_from_db()
        data = {'expected': fingerprint(snapshot(self.job)), 'decision': 'clear', 'reason': 'Checked synthetic source evidence.'}
        return {**data, **changes}

    def test_single_clear_is_audited_and_does_not_change_publication_or_application(self):
        app = Application.objects.create(user=self.other, job=self.job, generated_cv='private/unchanged.docx')
        publication = dict(JobPublication.objects.filter(pk=self.pub.pk).values().get())
        self.assertFalse(eligible_jobs().exists())
        response = self.client.post(self.url, self.data())
        self.assertEqual(response.status_code, 302)
        row = JobModerationReview.objects.get()
        self.assertEqual(row.actor, self.staff)
        self.assertTrue(row.before['is_flagged_scam'])
        self.assertFalse(row.after['is_flagged_scam'])
        self.assertEqual(row.reason, 'Checked synthetic source evidence.')
        self.assertEqual(dict(JobPublication.objects.filter(pk=self.pub.pk).values().get()), publication)
        app.refresh_from_db(); self.assertEqual(app.generated_cv.name, 'private/unchanged.docx')
        self.assertTrue(eligible_jobs().filter(pk=self.job.pk).exists())

    def test_keep_flag_remains_hidden_and_cannot_repeat_stale_decision(self):
        data = self.data(decision='uphold')
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.assertEqual(self.client.post(self.url, data).status_code, 409)
        self.assertEqual(JobModerationReview.objects.count(), 1)
        self.assertFalse(eligible_jobs().exists())

    def test_changed_source_or_deadline_requires_new_review(self):
        for target, changes in [(Job, {'description': 'Changed source text'}),
                                (JobPublication, {'closes_at': timezone.now()-timedelta(days=1)})]:
            data = self.data()
            target.objects.filter(pk=self.job.pk if target is Job else self.pub.pk).update(**changes)
            self.assertEqual(self.client.post(self.url, data).status_code, 409)
        self.assertFalse(JobModerationReview.objects.exists())

    def test_clear_does_not_reopen_expired_archived_or_inactive_listing(self):
        for status, active in [('archived', True), ('published', False)]:
            JobPublication.objects.filter(pk=self.pub.pk).update(status=status)
            Job.objects.filter(pk=self.job.pk).update(is_flagged_scam=True, is_active=active)
            self.assertEqual(self.client.post(self.url, self.data()).status_code, 302)
            self.assertFalse(eligible_jobs().exists())
        Job.objects.filter(pk=self.job.pk).update(is_active=True, is_flagged_scam=True)
        JobPublication.objects.filter(pk=self.pub.pk).update(closes_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.client.post(self.url, self.data()).status_code, 302)
        self.assertFalse(eligible_jobs().exists())

    def test_reason_required_and_input_is_escaped(self):
        for reason in ['', '   ', 'x'*1001]:
            self.assertEqual(self.client.post(self.url, self.data(reason=reason)).status_code, 200)
        self.assertFalse(JobModerationReview.objects.exists())
        Job.objects.filter(pk=self.job.pk).update(description='<script>bad()</script>')
        response = self.client.get(self.url)
        self.assertContains(response, '&lt;script&gt;bad()&lt;/script&gt;')
        self.assertIn('private', response['Cache-Control'])
        self.assertIn('no-store', response['Cache-Control'])

    def test_permissions_csrf_and_no_bulk_release(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url, self.data()).status_code, 302)
        self.other.is_staff=True; self.other.save(update_fields=['is_staff'])
        self.assertEqual(self.client.get(self.url).status_code, 403)
        with self.assertRaises(PermissionDenied):
            review(self.other, self.job.pk, **self.data())
        strict = Client(enforce_csrf_checks=True); strict.force_login(self.staff)
        self.assertEqual(strict.post(self.url, self.data()).status_code, 403)
        self.assertFalse(JobModerationReview.objects.exists())

    @patch('jobs.admin.review', side_effect=OperationalError('busy'))
    def test_contention_has_honest_retry_response_without_audit(self, _):
        self.assertEqual(self.client.post(self.url, self.data()).status_code, 503)
        self.assertFalse(JobModerationReview.objects.exists())

    def test_protected_audit_requires_reviewed_erasure_plan(self):
        review(self.staff, self.job.pk, **self.data())
        with self.assertRaisesMessage(CommandError, 'moderation records'):
            inventory(self.staff)

    def test_nonflagged_or_invalid_service_decision_has_no_effect(self):
        with self.assertRaises(ValidationError):
            review(self.staff, self.job.pk, **self.data(decision='publish'))
        data=self.data(); Job.objects.filter(pk=self.job.pk).update(is_flagged_scam=False)
        with self.assertRaises(StaleReview):
            review(self.staff, self.job.pk, **data)
        self.assertFalse(JobModerationReview.objects.exists())

    def test_concurrent_same_evidence_records_at_most_one_decision(self):
        data = self.data(); barrier = Barrier(2)

        def decide():
            try:
                actor = get_user_model().objects.get(pk=self.staff.pk)
                barrier.wait(timeout=10)
                review(actor, self.job.pk, **data)
                return 'recorded'
            except StaleReview:
                return 'stale'
            except OperationalError:
                return 'busy'
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: decide(), range(2)))
        self.assertEqual(outcomes.count('recorded'), 1)
        self.assertEqual(JobModerationReview.objects.count(), 1)
