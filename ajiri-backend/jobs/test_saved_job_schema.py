"""Disposable recovery rehearsal preserves old documents and personal progress."""
from django.db import connection, IntegrityError, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class SavedJobSchemaTests(TransactionTestCase):
    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', target)])
        return executor.loader.project_state([('jobs', target)]).apps

    def restore_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_nullable_date_and_new_shortlist_preserve_legacy_application_documents_and_search(self):
        self.addCleanup(self.restore_latest)
        old = self.migrate('0020_owner_recommendation_choices')
        user = old.get_model('accounts', 'User').objects.create(email='shortlist-schema@example.invalid')
        job = old.get_model('jobs', 'Job').objects.create(title='Savedword', company_name='Synthetic',
            description='Keep source', source_name='synthetic', source_url='https://example.invalid/saved-schema')
        app = old.get_model('jobs', 'Application').objects.create(user_id=user.pk, job_id=job.pk,
            progress_note='Keep private note', generated_cv='historical/cv.docx', generated_cover_letter='historical/letter.docx')
        current = self.migrate('0021_saved_jobs_and_follow_up')
        restored = current.get_model('jobs', 'Application').objects.get(pk=app.pk)
        self.assertIsNone(restored.follow_up_at)
        self.assertEqual(restored.generated_cv.name, 'historical/cv.docx')
        self.assertEqual(restored.generated_cover_letter.name, 'historical/letter.docx')
        saved = current.get_model('jobs', 'SavedJob')
        self.assertEqual(saved.objects.count(), 0)
        saved.objects.create(owner_id=user.pk, job_id=job.pk)
        with self.assertRaises(IntegrityError), transaction.atomic():
            saved.objects.create(owner_id=user.pk, job_id=job.pk)
        reversed_apps = self.migrate('0020_owner_recommendation_choices')
        kept = reversed_apps.get_model('jobs', 'Application').objects.get(pk=app.pk)
        self.assertEqual(kept.progress_note, 'Keep private note')
        self.assertEqual(kept.generated_cv.name, 'historical/cv.docx')
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='jobs_job'")
            self.assertEqual(len(cursor.fetchall()), 3)
            cursor.execute('SELECT rowid FROM jobs_job_search WHERE jobs_job_search MATCH %s', ['savedword'])
            self.assertIn(job.pk, {r[0] for r in cursor.fetchall()})
