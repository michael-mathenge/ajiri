import io
import json
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from accounts.models import User
from .models import Job
from .search import expression, search_jobs


class JobSearchTests(TestCase):
    def job(self, title, **extra):
        return Job.objects.create(title=title, company_name='Synthetic team',
            source_url=f'https://example.invalid/{Job.objects.count()}', **extra)

    def test_ranking_all_fields_prefix_and_filters(self):
        title = self.job('Python developer', description='Build systems', location='Nairobi')
        body = self.job('Support officer', description='Python systems', location='Mombasa')
        self.job('Hidden python', is_active=False)
        self.job('Scam python', is_flagged_scam=True)
        client = APIClient()
        client.force_authenticate(User.objects.create_user(email='search@example.invalid'))
        response = client.get('/api/jobs/', {'q': 'pyth'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['id'] for row in response.data['results']], [title.pk, body.pk])
        response = client.get('/api/jobs/', {'q': 'python', 'location': 'Mombasa'})
        self.assertEqual([row['id'] for row in response.data['results']], [body.pk])
        # Existing title-substring links keep their original semantics.
        response = client.get('/api/jobs/', {'title': 'Support'})
        self.assertEqual([row['id'] for row in response.data['results']], [body.pk])

    def test_unicode_literal_terms_punctuation_and_limits(self):
        job = self.job('Caf\u00e9 manager', description='Operations')
        self.assertEqual(list(search_jobs(Job.objects.all(), 'cafe man').values_list('pk', flat=True)), [job.pk])
        self.assertEqual(expression('python OR sql'), '"python"* AND "OR"* AND "sql"*')
        self.assertFalse(search_jobs(Job.objects.all(), '"; DROP TABLE jobs_job;--').exists())
        self.assertFalse(search_jobs(Job.objects.all(), '!!!').exists())
        self.assertEqual(search_jobs(Job.objects.all(), '').count(), 1)
        with self.assertRaises(ValidationError): expression('x' * 256)
        with self.assertRaises(ValidationError): expression('one ' * 13)
        self.assertEqual(Job.objects.count(), 1)

    def test_bulk_create_update_delete_keep_index_synchronized(self):
        Job.objects.bulk_create([Job(title='Old term', company_name='Team',
            source_url='https://example.invalid/bulk', description='')])
        job = Job.objects.get()
        self.assertTrue(search_jobs(Job.objects.all(), 'old').exists())
        Job.objects.filter(pk=job.pk).update(title='New term', requirements='Kiswahili')
        self.assertFalse(search_jobs(Job.objects.all(), 'old').exists())
        self.assertTrue(search_jobs(Job.objects.all(), 'kiswah').exists())
        job.delete()
        self.assertFalse(search_jobs(Job.objects.all(), 'new').exists())

    def test_large_index_has_stable_pagination_and_weighted_title_relevance(self):
        Job.objects.bulk_create([Job(title=f'Synthetic position {index}', company_name='Team',
            description='Python support for operations', source_url=f'https://example.invalid/scale/{index}')
            for index in range(1000)])
        target = self.job('Python developer', description='Build software')
        matches = search_jobs(Job.objects.all(), 'python')
        self.assertEqual(matches.count(), 1001)
        first = list(matches.values_list('pk', flat=True)[:20])
        second = list(matches.values_list('pk', flat=True)[20:40])
        self.assertEqual(first[0], target.pk)
        self.assertFalse(set(first) & set(second))
        self.assertEqual(first, list(matches.values_list('pk', flat=True)[:20]))
        # Verify the real ORM query plan, not an unrelated hand-written example:
        # broad searches must scan FTS once, without per-row correlated MATCH.
        plan = matches.explain().upper()
        self.assertEqual(plan.count('VIRTUAL TABLE INDEX'), 1)
        self.assertNotIn('CORRELATED', plan)
        self.assertEqual(len(set(matches.values_list('pk', flat=True))), 1001)

    def test_index_is_used_and_benchmark_is_read_only(self):
        self.job('Project manager', description='Planning')
        with connection.cursor() as cursor:
            cursor.execute('EXPLAIN QUERY PLAN SELECT rowid FROM jobs_job_search WHERE jobs_job_search MATCH %s', ['"project"*'])
            self.assertTrue(any('VIRTUAL TABLE INDEX' in str(row) for row in cursor.fetchall()))
        output = io.StringIO()
        before = list(Job.objects.values())
        call_command('benchmark_job_search', runs=5, stdout=output)
        self.assertEqual(before, list(Job.objects.values()))
        summary = json.loads(output.getvalue())
        self.assertEqual(summary['active_jobs'], 1)
        self.assertEqual(len(summary['samples']), 4)
        self.assertTrue(all(row['p95_ms'] >= 0 for row in summary['samples']))
        self.assertNotIn('Project manager', output.getvalue())
        self.assertEqual(summary['known_title_recall'], {'checked': 1, 'found_in_top5': 1, 'skipped': 0})


class SearchMigrationTests(TransactionTestCase):
    def test_rebuild_and_reverse_preserve_job_rows(self):
        executor = MigrationExecutor(connection)
        leaves = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(leaves))
        executor.migrate([('jobs', '0010_application_send_authorization_schema')])
        historical = executor.loader.project_state([('jobs', '0010_application_send_authorization_schema')]).apps.get_model('jobs', 'Job')
        job = historical.objects.create(title='Preserved migration row', company_name='Synthetic',
            description='Content', source_url='https://example.invalid/migration')
        MigrationExecutor(connection).migrate(leaves)
        self.assertTrue(search_jobs(Job.objects.all(), 'preserved').filter(pk=job.pk).exists())
        Job.objects.filter(pk=job.pk).update(description='Newer data')
        MigrationExecutor(connection).migrate([('jobs', '0010_application_send_authorization_schema')])
        self.assertEqual(historical.objects.get(pk=job.pk).description, 'Newer data')
        MigrationExecutor(connection).migrate(leaves)
        self.assertTrue(search_jobs(Job.objects.all(), 'newer').exists())
