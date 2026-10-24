"""Adding review evidence must not rebuild the historical job/search table."""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ModerationMigrationTests(TransactionTestCase):
    def restore_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_existing_job_application_and_search_triggers_survive(self):
        self.addCleanup(self.restore_latest)
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', '0015_application_progress')])
        old = executor.loader.project_state([('jobs', '0015_application_progress')]).apps
        owner = old.get_model('accounts', 'User').objects.create(email='moderation-schema@example.invalid')
        job = old.get_model('jobs', 'Job').objects.create(title='Moderationbefore', company_name='Synthetic',
            source_name='synthetic', source_url='https://example.invalid/moderation-schema', is_flagged_scam=True)
        app = old.get_model('jobs', 'Application').objects.create(user_id=owner.pk, job_id=job.pk,
            status='ready_for_review', generated_cv='private/retained.docx', email_body='Retained snapshot')
        before_job = old.get_model('jobs', 'Job').objects.filter(pk=job.pk).values().get()
        before_app = old.get_model('jobs', 'Application').objects.filter(pk=app.pk).values().get()
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', '0016_job_moderation_review')])
        new = executor.loader.project_state([('jobs', '0016_job_moderation_review')]).apps
        self.assertEqual(new.get_model('jobs', 'Job').objects.filter(pk=job.pk).values().get(), before_job)
        self.assertEqual(new.get_model('jobs', 'Application').objects.filter(pk=app.pk).values().get(), before_app)
        self.assertEqual(new.get_model('jobs', 'JobModerationReview').objects.count(), 0)
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='jobs_job'")
            self.assertTrue({'jobs_search_insert', 'jobs_search_update', 'jobs_search_delete'} <= {r[0] for r in cursor.fetchall()})
        new.get_model('jobs', 'Job').objects.filter(pk=job.pk).update(title='Moderationafter')
        with connection.cursor() as cursor:
            cursor.execute('SELECT rowid FROM jobs_job_search WHERE jobs_job_search MATCH %s', ['moderationafter'])
            self.assertEqual(cursor.fetchall(), [(job.pk,)])
