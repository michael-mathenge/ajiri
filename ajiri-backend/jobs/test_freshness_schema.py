"""The employer schema must preserve historical jobs and SQLite FTS triggers."""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class FreshnessMigrationTests(TransactionTestCase):
    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', target)])
        return executor.loader.project_state([('jobs', target)]).apps

    def restore_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_additions_preserve_rows_and_insert_update_delete_search_triggers(self):
        self.addCleanup(self.restore_latest)
        self.migrate('0010_application_send_authorization_schema')
        old = self.migrate('0011_job_full_text_search')
        job = old.get_model('jobs','Job').objects.create(title='Beforeword',company_name='Synthetic',
            description='Synthetic migration data',source_name='test',source_url='https://example.invalid/migration')
        current = self.migrate('0013_job_external_application_url')
        model = current.get_model('jobs','Job')
        restored = model.objects.get(pk=job.pk)
        self.assertEqual(restored.title,'Beforeword')
        self.assertEqual(current.get_model('jobs','JobPublication').objects.count(),0)
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='jobs_job'")
            names = {row[0] for row in cursor.fetchall()}
        self.assertTrue({'jobs_search_insert','jobs_search_update','jobs_search_delete'} <= names)
        model.objects.filter(pk=job.pk).update(title='Afterword')
        with connection.cursor() as cursor:
            cursor.execute('SELECT rowid FROM jobs_job_search WHERE jobs_job_search MATCH %s',['afterword'])
            self.assertEqual(cursor.fetchall(),[(job.pk,)])
        restored.delete()
        with connection.cursor() as cursor:
            cursor.execute('SELECT rowid FROM jobs_job_search WHERE jobs_job_search MATCH %s',['afterword'])
            self.assertEqual(cursor.fetchall(),[])
