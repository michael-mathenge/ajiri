"""Rehearse new nullable metadata on disposable legacy data, preserving SQLite FTS."""
from datetime import timedelta
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class VacancyMetadataMigrationTests(TransactionTestCase):
    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', target)])
        return executor.loader.project_state([('jobs', target)]).apps

    def restore_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def assert_search(self, job_id, word):
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='jobs_job'")
            self.assertTrue({'jobs_search_insert', 'jobs_search_update', 'jobs_search_delete'} <= {r[0] for r in cursor.fetchall()})
            cursor.execute('SELECT rowid FROM jobs_job_search WHERE jobs_job_search MATCH %s', [word])
            self.assertIn(job_id, {r[0] for r in cursor.fetchall()})

    def test_additive_fields_preserve_legacy_jobs_drafts_searches_and_search_triggers(self):
        self.addCleanup(self.restore_latest)
        old = self.migrate('0018_original_employer_submission')
        owner = old.get_model('accounts', 'User').objects.create(email='filter-migration@example.invalid')
        org = old.get_model('jobs', 'EmployerOrganisation').objects.create(owner_id=owner.pk,
            name='Synthetic historical', website='https://example.invalid')
        job = old.get_model('jobs', 'Job').objects.create(title='Beforeword', company_name='Synthetic',
            description='Preserve this historical prose', location='Nairobi', source_name='Synthetic',
            source_url='https://example.invalid/filter-migration')
        draft = old.get_model('jobs', 'EmployerJobDraft').objects.create(organisation_id=org.pk,
            title='Legacy draft', description='Unchanged', location='Nairobi',
            application_url='https://example.invalid/apply', closes_at=timezone.now()+timedelta(days=2), job_id=job.pk)
        search = old.get_model('jobs', 'SavedSearch').objects.create(owner_id=owner.pk,
            name='Legacy search', q='Beforeword', location='Nairobi', in_app_cursor=timezone.now(), email_cursor=timezone.now())
        current = self.migrate('0019_normalized_vacancy_filters')
        for model, pk in [('Job', job.pk), ('EmployerJobDraft', draft.pk), ('SavedSearch', search.pk)]:
            record = current.get_model('jobs', model).objects.get(pk=pk)
            self.assertIsNone(record.county)
            self.assertIsNone(record.work_arrangement)
            self.assertIsNone(getattr(record, 'max_experience_years' if model == 'SavedSearch' else 'min_experience_years'))
        self.assertEqual(current.get_model('jobs', 'EmployerJobDraft').objects.get(pk=draft.pk).job_id, job.pk)
        current.get_model('jobs', 'Job').objects.filter(pk=job.pk).update(title='Afterword',
            county='nairobi-city', work_arrangement='remote', min_experience_years=0)
        self.assert_search(job.pk, 'afterword')
        reverted = self.migrate('0018_original_employer_submission')
        self.assertEqual(reverted.get_model('jobs', 'Job').objects.get(pk=job.pk).description, 'Preserve this historical prose')
        self.assertEqual(reverted.get_model('jobs', 'SavedSearch').objects.get(pk=search.pk).q, 'Beforeword')
        self.assertEqual(reverted.get_model('jobs', 'EmployerJobDraft').objects.get(pk=draft.pk).job_id, job.pk)
        self.assert_search(job.pk, 'afterword')
