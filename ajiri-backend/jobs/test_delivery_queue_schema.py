"""Additive queue migration on populated synthetic historical data."""
import hashlib
import tempfile
from pathlib import Path

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class DeliveryQueueMigrationTests(TransactionTestCase):
    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', target)])
        return executor.loader.project_state([('jobs', target)]).apps

    def restore_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def snapshot(self):
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            result = {}
            for table in tables:
                if table in ('django_migrations', 'jobs_deliverytask'):
                    continue
                cursor.execute('SELECT * FROM ' + connection.ops.quote_name(table))
                result[table] = (tuple(col[0] for col in cursor.description), sorted(map(repr, cursor.fetchall())))
            return result

    def test_new_table_preserves_all_existing_tables_private_bytes_and_search_triggers(self):
        self.addCleanup(self.restore_latest)
        old = self.migrate('0021_saved_jobs_and_follow_up')
        owner = old.get_model('accounts', 'User').objects.create(email='queue-migration@example.invalid')
        job = old.get_model('jobs', 'Job').objects.create(title='Queuebeforeword', company_name='Synthetic',
            description='Historical synthetic text', source_url='https://example.invalid/queue-migration')
        app = old.get_model('jobs', 'Application').objects.create(user_id=owner.pk, job_id=job.pk,
            generated_cv='applications/synthetic-cv.docx')
        with tempfile.TemporaryDirectory() as media:
            private = Path(media) / app.generated_cv.name
            private.parent.mkdir(parents=True)
            private.write_bytes(b'Synthetic immutable document bytes')
            digest = hashlib.sha256(private.read_bytes()).digest()
            before = self.snapshot()
            current = self.migrate('0022_durable_delivery_queue')
            self.assertEqual(self.snapshot(), before)
            self.assertEqual(hashlib.sha256(private.read_bytes()).digest(), digest)
            self.assertEqual(current.get_model('jobs', 'Application').objects.get(pk=app.pk).job_id, job.pk)
            self.assertEqual(current.get_model('jobs', 'DeliveryTask').objects.count(), 0)
            current.get_model('jobs', 'Job').objects.filter(pk=job.pk).update(title='Queueafterword')
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='jobs_job'")
                self.assertEqual({r[0] for r in cursor.fetchall()},
                    {'jobs_search_insert', 'jobs_search_update', 'jobs_search_delete'})
                cursor.execute('SELECT rowid FROM jobs_job_search WHERE jobs_job_search MATCH %s', ['queueafterword'])
                self.assertIn(job.pk, {r[0] for r in cursor.fetchall()})
