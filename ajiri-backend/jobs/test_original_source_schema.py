"""Forward/reverse rehearsal on a disposable DB; production rollback keeps the column."""
from datetime import timedelta
import uuid

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class OriginalSubmissionMigrationTests(TransactionTestCase):
    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', target)])
        return executor.loader.project_state([('jobs', target)]).apps

    def restore_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_forward_and_disposable_reverse_preserve_historical_rows_and_job_search(self):
        self.addCleanup(self.restore_latest)
        old = self.migrate('0017_job_browsing_settings')
        user = old.get_model('accounts', 'User').objects.create(email='migration-owner@example.invalid')
        organisation = old.get_model('jobs', 'EmployerOrganisation').objects.create(
            owner_id=user.pk, name='Synthetic historical employer', website='https://example.invalid')
        draft = old.get_model('jobs', 'EmployerJobDraft').objects.create(
            organisation_id=organisation.pk, title='Historical title', description='Historical private submission',
            location='Nairobi, Kenya', application_url='https://example.invalid/apply',
            closes_at=timezone.now() + timedelta(days=3))
        job = old.get_model('jobs', 'Job').objects.create(title='Beforeword', company_name='Synthetic',
            description='Synthetic migration job', source_name='test', source_url='https://example.invalid/historical')
        old.get_model('jobs', 'EmployerJobDraft').objects.filter(pk=draft.pk).update(job_id=job.pk)
        reviewer = old.get_model('accounts', 'User').objects.create(email='migration-reviewer@example.invalid', is_staff=True)
        review = old.get_model('jobs', 'EmployerReview').objects.create(
            draft_id=draft.pk, actor_id=reviewer.pk, revision=1, decision='approved', reason='Historical synthetic evidence')
        current = self.migrate('0018_original_employer_submission')
        restored = current.get_model('jobs', 'EmployerJobDraft').objects.get(pk=draft.pk)
        self.assertIsNone(restored.submission_id)
        self.assertEqual(restored.description, 'Historical private submission')
        self.assertEqual(restored.job_id, job.pk)
        self.assertEqual(current.get_model('jobs', 'EmployerReview').objects.get(pk=review.pk).draft_id, draft.pk)
        current.get_model('jobs', 'EmployerJobDraft').objects.filter(pk=draft.pk).update(submission_id=uuid.uuid4())
        current.get_model('jobs', 'Job').objects.filter(pk=job.pk).update(title='Afterword')
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='jobs_job'")
            self.assertTrue({'jobs_search_insert', 'jobs_search_update', 'jobs_search_delete'} <= {row[0] for row in cursor.fetchall()})
            cursor.execute('SELECT rowid FROM jobs_job_search WHERE jobs_job_search MATCH %s', ['afterword'])
            self.assertIn(job.pk, {row[0] for row in cursor.fetchall()})
        reversed_apps = self.migrate('0017_job_browsing_settings')
        self.assertEqual(reversed_apps.get_model('jobs', 'EmployerJobDraft').objects.get(pk=draft.pk).title, 'Historical title')
        self.assertEqual(reversed_apps.get_model('jobs', 'Job').objects.get(pk=job.pk).title, 'Afterword')
