from unittest.mock import patch
import importlib.util
from pathlib import Path
import tempfile
import uuid
from django.conf import settings
from django.db import connection
from django.test import SimpleTestCase
from .models import Job
from .search import search_jobs
from .postgres_search import SCHEMA_SQL


class PostgresSearchContractTests(SimpleTestCase):
    def test_postgres_candidate_uses_bound_literal_terms_and_stable_ordering(self):
        with patch.object(connection, 'vendor', 'postgresql'):
            queryset = search_jobs(Job.objects.all(), "python OR sql'; DROP")
            sql, params = queryset.query.sql_with_params()
        self.assertIn('ajiri_job_vector', sql)
        self.assertNotIn('DROP', sql)
        self.assertTrue(any("'python':* & 'or':* & 'sql':* & 'drop':*" == p for p in params))
        self.assertEqual(queryset.query.order_by, ('-search_rank', '-posted_at', '-pk'))

    def test_sqlite_retains_fts_join_and_candidate_schema_is_not_implicitly_run(self):
        sql, _ = search_jobs(Job.objects.all(), 'Python').query.sql_with_params()
        self.assertIn('jobs_job_search MATCH', sql)
        self.assertNotIn('ajiri_job_vector', sql)
        self.assertIn('CREATE INDEX jobs_job_pg_search_gin', SCHEMA_SQL)

    def test_latin_accents_fold_without_expanding_literal_ligatures_or_stroked_letters(self):
        from .postgres_search import LATIN_FOLD
        self.assertEqual('Café Résumé'.translate(LATIN_FOLD).lower(), 'cafe resume')
        self.assertEqual('Æther Straße Łódź Cœur'.translate(LATIN_FOLD).lower(), 'æther straße łodz cœur')
        self.assertNotIn('CREATE EXTENSION', SCHEMA_SQL)

    def test_alternate_target_graph_matches_models_without_database_or_history_writes(self):
        path = settings.BASE_DIR.parent/'scripts/postgres_bootstrap_rehearsal.py'
        spec = importlib.util.spec_from_file_location('postgres_bootstrap_test', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        protected = {p: p.read_bytes() for label in ('accounts', 'profiles', 'jobs')
            for p in (settings.BASE_DIR/label/'migrations').glob('*.py')}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/('bootstrap_'+uuid.uuid4().hex)
            modules = module.prepare_target_graph(root)
            self.assertEqual(set(modules), {'accounts', 'profiles', 'jobs'})
            self.assertGreater(len(list(root.rglob('0*.py'))), 2)
            with self.assertRaises(RuntimeError): module.prepare_target_graph(root)
        self.assertEqual(protected, {p: p.read_bytes() for p in protected})
