"""Additive preference migration must not rebuild jobs or infer old-user choices."""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class SavedSearchMigrationTests(TransactionTestCase):
    def restore_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_new_tables_preserve_historical_job_and_search_triggers(self):
        self.addCleanup(self.restore_latest)
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', '0013_job_external_application_url')])
        old = executor.loader.project_state([('jobs', '0013_job_external_application_url')]).apps
        job = old.get_model('jobs', 'Job').objects.create(title='Preservedword', company_name='Synthetic',
            source_name='synthetic', source_url='https://example.invalid/saved-migration')
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', '0014_saved_search_windows')])
        state = executor.loader.project_state([('jobs', '0014_saved_search_windows')]).apps
        self.assertEqual(state.get_model('jobs', 'Job').objects.get(pk=job.pk).title, 'Preservedword')
        self.assertEqual(state.get_model('jobs', 'SavedSearch').objects.count(), 0)
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='jobs_job'")
            self.assertTrue({'jobs_search_insert', 'jobs_search_update', 'jobs_search_delete'} <= {x[0] for x in cursor.fetchall()})
            cursor.execute('SELECT rowid FROM jobs_job_search WHERE jobs_job_search MATCH %s', ['preservedword'])
            self.assertEqual(cursor.fetchall(), [(job.pk,)])
