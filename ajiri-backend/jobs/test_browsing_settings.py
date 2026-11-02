from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import OperationalError, IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from .browsing import supplemental_browsing_enabled, CACHE_KEY, CACHE_SECONDS
from .feed_display import browse_jobs, supplemental_jobs
from .models import Job, JobPublication, JobBrowsingSettings, JobBrowsingSettingsAudit


@override_settings(JOB_FEED_DISPLAY_FORCE_OFF=False, JOB_FRESHNESS_ENFORCED=True,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BrowsingSettingsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.owner = User.objects.create_superuser(email='operator@example.invalid', password='synthetic-only')
        self.row = JobBrowsingSettings.objects.get(pk=1)

    def test_migration_and_missing_row_default_off_without_writing_on_read(self):
        self.assertFalse(self.row.supplemental_browsing_enabled)
        self.assertIsNone(self.row.last_changed_by)
        self.assertFalse(JobBrowsingSettingsAudit.objects.exists())
        self.assertFalse(supplemental_browsing_enabled())
        JobBrowsingSettings.objects.all().delete()
        cache.clear()
        with self.assertNumQueries(1):
            self.assertFalse(supplemental_browsing_enabled())
        self.assertFalse(JobBrowsingSettings.objects.exists())

    def test_read_and_cache_failure_close(self):
        with patch('jobs.models.JobBrowsingSettings.objects.filter', side_effect=OperationalError):
            self.assertFalse(supplemental_browsing_enabled())
        with patch('jobs.browsing.cache.get', side_effect=RuntimeError):
            self.assertFalse(supplemental_browsing_enabled())
        with patch('jobs.browsing.cache.set', side_effect=OSError):
            self.assertFalse(supplemental_browsing_enabled())

    def test_cache_has_sixty_second_expiry_and_kill_switch_precedes_cached_true(self):
        self.assertEqual(CACHE_SECONDS, 60)
        with patch('jobs.browsing.cache.set', wraps=cache.set) as write:
            self.assertFalse(supplemental_browsing_enabled())
            write.assert_called_once_with(CACHE_KEY, False, 60)
        with self.assertNumQueries(0):
            self.assertFalse(supplemental_browsing_enabled())
        cache.set(CACHE_KEY, True, 60)
        with self.settings(JOB_FEED_DISPLAY_FORCE_OFF=True), self.assertNumQueries(0):
            self.assertFalse(supplemental_browsing_enabled())
        with self.settings(JOB_FEED_DISPLAY_FORCE_OFF=True):
            self.assertFalse(browse_jobs(enabled=True).exists())

    def test_cached_value_reloads_after_sixty_seconds(self):
        clock = [1000.0]
        with patch('time.time', side_effect=lambda: clock[0]):
            self.assertFalse(supplemental_browsing_enabled())
            JobBrowsingSettings.objects.filter(pk=1).update(supplemental_browsing_enabled=True)
            clock[0] += 59
            with self.assertNumQueries(0):
                self.assertFalse(supplemental_browsing_enabled())
            clock[0] += 1
            self.assertTrue(supplemental_browsing_enabled())

    @override_settings(JOB_FEED_DISPLAY_ENABLED=True)
    def test_retired_setting_cannot_enable_and_off_equals_eligible(self):
        from .freshness import eligible_jobs
        at = timezone.now()
        verified = Job.objects.create(title='Verified synthetic', company_name='Synthetic',
            source_url='https://example.invalid/verified', source_name='MyJobMag Kenya', posted_at=at)
        JobPublication.objects.create(job=verified, origin='rss', status='published',
            confirmed_at=at, closes_at=at+timedelta(days=1))
        Job.objects.create(title='Unverified synthetic', company_name='Synthetic',
            source_url='https://example.invalid/unverified', source_name='MyJobMag Kenya', posted_at=at)
        self.assertFalse(supplemental_browsing_enabled())
        self.assertEqual(list(browse_jobs()), list(eligible_jobs()))
        self.assertEqual(list(browse_jobs().values_list('pk', flat=True)), [verified.pk])

    def test_atomic_actor_audit_and_cache_invalidation(self):
        cache.set(CACHE_KEY, False, 60)
        self.row.supplemental_browsing_enabled = True
        with self.captureOnCommitCallbacks(execute=True):
            self.row.save(actor=self.owner)
        self.assertTrue(supplemental_browsing_enabled())
        self.row.refresh_from_db()
        self.assertEqual(self.row.last_changed_by, self.owner)
        event = JobBrowsingSettingsAudit.objects.get()
        self.assertEqual((event.actor, event.old_value, event.new_value), (self.owner, False, True))
        self.assertIsNotNone(event.created_at)
        self.row.supplemental_browsing_enabled = False
        with patch('jobs.models.JobBrowsingSettingsAudit.objects.create', side_effect=OperationalError):
            with self.assertRaises(OperationalError):
                self.row.save(actor=self.owner)
        self.row.refresh_from_db()
        self.assertTrue(self.row.supplemental_browsing_enabled)
        self.assertEqual(JobBrowsingSettingsAudit.objects.count(), 1)

    def test_singleton_constraints_and_change_requires_superuser(self):
        with self.assertRaises(ValidationError):
            JobBrowsingSettings(pk=2).save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            JobBrowsingSettings.objects.bulk_create([JobBrowsingSettings(pk=2)])
        self.row.supplemental_browsing_enabled = True
        with self.assertRaises(PermissionDenied):
            self.row.save()

    def test_admin_staff_with_all_permissions_still_cannot_view_or_change(self):
        staff = User.objects.create_user(email='staff@example.invalid', is_staff=True)
        staff.user_permissions.set(Permission.objects.all())
        self.client.force_login(staff)
        for model in ('jobbrowsingsettings', 'jobbrowsingsettingsaudit'):
            self.assertEqual(self.client.get(reverse(f'admin:jobs_{model}_changelist')).status_code, 403)
        path = reverse('admin:jobs_jobbrowsingsettings_change', args=[1])
        self.assertEqual(self.client.post(path, {'supplemental_browsing_enabled': 'on'}).status_code, 403)
        self.row.refresh_from_db()
        self.assertFalse(self.row.supplemental_browsing_enabled)

    def test_superuser_admin_change_audits_and_rejects_add_delete_audit_edits(self):
        self.client.force_login(self.owner)
        path = reverse('admin:jobs_jobbrowsingsettings_change', args=[1])
        self.assertEqual(self.client.get(path).status_code, 200)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.client.post(path, {'supplemental_browsing_enabled': 'on', '_save': 'Save'}).status_code, 302)
        event = JobBrowsingSettingsAudit.objects.get()
        for model, pk in (('jobbrowsingsettings', 1), ('jobbrowsingsettingsaudit', event.pk)):
            self.assertEqual(self.client.get(reverse(f'admin:jobs_{model}_add')).status_code, 403)
            self.assertEqual(self.client.post(reverse(f'admin:jobs_{model}_delete', args=[pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('admin:jobs_jobbrowsingsettingsaudit_change', args=[event.pk]), {'new_value': ''}).status_code, 403)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.client.post(path, {'_save': 'Save'}).status_code, 302)
        self.assertFalse(supplemental_browsing_enabled())
        self.assertEqual(JobBrowsingSettingsAudit.objects.count(), 2)
        off_event = JobBrowsingSettingsAudit.objects.first()
        self.assertEqual((off_event.old_value, off_event.new_value), (True, False))

    def test_exact_recency_edges_and_retained_pilots(self):
        at = timezone.now()
        def job(name, posted, **extra):
            return Job.objects.create(title=name, company_name='Synthetic', source_name=extra.pop('source_name', 'MyJobMag Kenya'),
                source_url=f'https://example.invalid/{name}', posted_at=posted, **extra)
        boundary = job('day14', at-timedelta(days=14), pk=1001)
        for name, posted in [('day15', at-timedelta(days=15)), ('null', None),
                             ('future', at+timedelta(microseconds=1)),
                             ('past-boundary', at-timedelta(days=14, microseconds=1))]:
            job(name, posted)
        pilot_names = ['deployment-check', 'ajiri-owner-alert-pilot', 'ajiri-owner-application-pilot']
        for pk, name in zip((1, 779, 980), pilot_names):
            job(name, None, pk=pk, source_name=name, is_active=False)
        self.assertEqual(list(supplemental_jobs(at=at)), [boundary])
        self.assertEqual(Job.objects.filter(pk__in=(1, 779, 980), source_name__in=pilot_names,
            posted_at__isnull=True, publication__isnull=True, is_active=False).count(), 3)
