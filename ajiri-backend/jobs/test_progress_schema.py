"""Old sent rows gain no inferred personal report or employer outcome."""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class ProgressMigrationTests(TransactionTestCase):
    def restore_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_old_submission_and_snapshots_are_preserved_without_inferred_report(self):
        self.addCleanup(self.restore_latest)
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', '0014_saved_search_windows')])
        old = executor.loader.project_state([('jobs', '0014_saved_search_windows')]).apps
        owner = old.get_model('accounts', 'User').objects.create(email='schema-progress@example.invalid')
        job = old.get_model('jobs', 'Job').objects.create(title='Synthetic retained role', company_name='Synthetic',
            source_name='synthetic', source_url='https://example.invalid/progress-schema')
        sent_at = timezone.now()
        app = old.get_model('jobs', 'Application').objects.create(user_id=owner.pk, job_id=job.pk,
            status='sent', application_method='external_link', sent_at=sent_at, email_body='Retained snapshot')
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', '0015_application_progress')])
        new = executor.loader.project_state([('jobs', '0015_application_progress')]).apps
        retained = new.get_model('jobs', 'Application').objects.get(pk=app.pk)
        self.assertEqual((retained.status, retained.sent_at, retained.email_body), ('sent', sent_at, 'Retained snapshot'))
        self.assertEqual((retained.progress_stage, retained.progress_note, retained.progress_revision), ('not_reported', '', 0))
        self.assertIsNone(retained.progress_reported_at)
