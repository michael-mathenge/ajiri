"""Disposable forward/reverse rehearsal; real rollback retains owner choices."""
from django.db import connection, IntegrityError, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class RecommendationSchemaTests(TransactionTestCase):
    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate([('jobs', target)])
        return executor.loader.project_state([('jobs', target)]).apps

    def restore_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_new_table_infers_no_choices_and_preserves_existing_jobs_applications_and_fts(self):
        self.addCleanup(self.restore_latest)
        old = self.migrate('0019_normalized_vacancy_filters')
        owner = old.get_model('accounts', 'User').objects.create(email='choice-migration@example.invalid')
        other = old.get_model('accounts', 'User').objects.create(email='other-choice-migration@example.invalid')
        job = old.get_model('jobs', 'Job').objects.create(title='Choiceword', company_name='Synthetic',
            description='Preserve original', source_name='synthetic', source_url='https://example.invalid/choice-schema',
            county='nairobi-city', min_experience_years=0)
        application = old.get_model('jobs', 'Application').objects.create(user_id=owner.pk, job_id=job.pk,
            progress_stage='applied', progress_note='Preserve private progress')
        new = self.migrate('0020_owner_recommendation_choices')
        model = new.get_model('jobs', 'RecommendationChoice')
        self.assertEqual(model.objects.count(), 0)
        model.objects.create(owner_id=owner.pk, job_id=job.pk, revision=1)
        model.objects.create(owner_id=other.pk, job_id=job.pk, revision=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            model.objects.create(owner_id=owner.pk, job_id=job.pk)
        for apps in (new, self.migrate('0019_normalized_vacancy_filters')):
            kept = apps.get_model('jobs', 'Job').objects.get(pk=job.pk)
            self.assertEqual((kept.description, kept.county, kept.min_experience_years), ('Preserve original', 'nairobi-city', 0))
            self.assertEqual(apps.get_model('jobs', 'Application').objects.get(pk=application.pk).progress_note, 'Preserve private progress')
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='jobs_job'")
                self.assertEqual(len(cursor.fetchall()), 3)
                cursor.execute('SELECT rowid FROM jobs_job_search WHERE jobs_job_search MATCH %s', ['choiceword'])
                self.assertIn(job.pk, {r[0] for r in cursor.fetchall()})
