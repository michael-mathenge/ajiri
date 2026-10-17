"""Schema/validation only. No routes, real personal data or provider requests."""
from copy import deepcopy
import hashlib
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.contrib.auth import get_user_model
from django.db import IntegrityError, OperationalError, close_old_connections, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import F
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from rest_framework.exceptions import ValidationError
from .cv_validation import validate_content, MAX_CONTENT_BYTES
from .models import CVWorkspace, CVApproval, approved_cv_path


def content():
    return {'schema_version': 1, 'contact': {'name': 'Test Applicant'}, 'skills': ['Python']}


class CVValidationTests(SimpleTestCase):
    def test_optional_sections_and_json_round_trip(self):
        data = content()
        data['projects'] = [{'name': 'Test project'}]
        validated = validate_content(data, for_approval=True)
        self.assertEqual(validated['employment'], [])
        self.assertEqual(validated['contact']['email'], '')
        uuid.UUID(validated['projects'][0]['id'])
        self.assertEqual(validate_content(json.loads(json.dumps(validated))), validated)
        self.assertNotIn('employment', data)  # Input is never modified.

    def test_minimal_draft_is_incomplete_not_invented(self):
        data = {'schema_version': 1, 'contact': {}}
        result = validate_content(data)
        self.assertEqual(result['contact']['name'], '')
        with self.assertRaises(ValidationError) as error:
            validate_content(data, for_approval=True)
        self.assertIn('contact', error.exception.detail)
        self.assertIn('non_field_errors', error.exception.detail)

    def test_unknown_fields_and_wrong_nested_types_rejected(self):
        variants = [
            {**content(), 'national_id': 'not-allowed'},
            {**content(), 'contact': {'name': 123}},
            {**content(), 'contact': {'name': 'Test', 'street_address': 'not-allowed'}},
            {**content(), 'employment': 'invalid'},
            {**content(), 'skills': [123]},
            {**content(), 'schema_version': True},
            {**content(), 'schema_version': '1'},
            {**content(), 'schema_version': 2},
            {**content(), 'projects': [{'name': 'Test', 'secret': 'not-allowed'}]},
            {**content(), 'employment': [{'title': 'Test', 'organisation': 'Test', 'current': 'true'}]},
            {**content(), 'contact': {'email': 'invalid'}},
        ]
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_content(value)

    def test_section_and_string_limits(self):
        for section, limit, row in [
            ('employment', 20, {'title': 'Test', 'organisation': 'Test'}),
            ('education', 15, {'qualification': 'Test', 'institution': 'Test'}),
            ('certifications', 20, {'name': 'Test', 'issuer': 'Test'}),
            ('projects', 20, {'name': 'Test'}),
        ]:
            self.assertEqual(len(validate_content({**content(), section: [row] * limit})[section]), limit)
            with self.subTest(section=section), self.assertRaises(ValidationError):
                validate_content({**content(), section: [row] * (limit + 1)})
        self.assertEqual(len(validate_content({**content(), 'summary': 'a' * 3000})['summary']), 3000)
        for field, value in [('summary', 'x' * 3001), ('skills', ['x'] * 51), ('headline', 'x' * 256)]:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_content({**content(), field: value})
        with self.assertRaises(ValidationError):
            validate_content({**content(), 'employment': [{'title': 'Test', 'organisation': 'Test', 'achievements': ['x'] * 11}]})

    def test_dates_and_safe_project_url(self):
        employment = {'title': 'Test', 'organisation': 'Test', 'start': '2020-01'}
        for dates in [{'end': '2019-12'}, {'end': '2020-13'}, {'end': '2021-01', 'current': True}, {'start': '20-01'}]:
            with self.subTest(dates=dates), self.assertRaises(ValidationError):
                validate_content({**content(), 'employment': [{**employment, **dates}]})
        validate_content({**content(), 'employment': [{**employment, 'current': True}]})
        with self.assertRaises(ValidationError):
            validate_content({**content(), 'certifications': [{'name': 'Test', 'issuer': 'Test', 'issued': '2022-01', 'expiry': '2020-01'}]})
        for url in ['javascript:alert(1)', 'file:///private', 'ftp://example.invalid/test', '/relative']:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                validate_content({**content(), 'projects': [{'name': 'Test', 'url': url}]})
        validate_content({**content(), 'projects': [{'name': 'Test', 'url': 'https://example.com/project'}]})

    def test_duplicate_ids_size_and_non_json(self):
        identifier = str(uuid.uuid4())
        with self.assertRaises(ValidationError):
            validate_content({**content(), 'projects': [{'id': identifier, 'name': 'Test'}] * 2})
        for value in [{**content(), 'summary': 'x' * MAX_CONTENT_BYTES}, {'invalid': float('nan')}, {'invalid': object()}]:
            with self.assertRaises(ValidationError):
                validate_content(value)


class CVSchemaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='cv-schema@example.invalid', password='test-only')

    def approval(self, **overrides):
        data = validate_content(content(), for_approval=True)
        values = dict(profile=self.user.profile, revision=1, content=data,
                      content_sha256=hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
                      template_version='cv-v1', document='approved-cvs/test.docx', document_sha256='0' * 64)
        values.update(overrides)
        return CVApproval.objects.create(**values)

    def test_no_implicit_workspace_or_approval(self):
        self.assertFalse(CVWorkspace.objects.exists())
        self.assertFalse(CVApproval.objects.exists())
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, '')

    def test_defaults_and_database_constraints(self):
        workspace = CVWorkspace.objects.create(profile=self.user.profile)
        self.assertEqual((workspace.content, workspace.revision), ({}, 1))
        for operation in [
            lambda: CVWorkspace.objects.create(profile=self.user.profile),
            lambda: CVWorkspace.objects.filter(pk=workspace.pk).update(revision=0),
        ]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                operation()
        approval = self.approval()
        self.assertIsNotNone(approval.approved_at)
        for changes in [{}, {'revision': 0}]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                self.approval(**changes)

    def test_snapshot_separation_private_path_and_cascade(self):
        data = validate_content(content())
        workspace = CVWorkspace.objects.create(profile=self.user.profile, content=data)
        approval = self.approval(content=deepcopy(data))
        workspace.content['contact']['name'] = 'Edited'
        workspace.save()
        approval.refresh_from_db()
        self.assertEqual(approval.content['contact']['name'], 'Test Applicant')
        path = approved_cv_path(approval, '../../personal-name.docx')
        self.assertTrue(path.startswith('approved-cvs/'))
        self.assertNotIn('personal', path)
        self.assertNotEqual(path, approved_cv_path(approval, 'same.docx'))
        self.user.delete()
        self.assertFalse(CVWorkspace.objects.exists())
        self.assertFalse(CVApproval.objects.exists())


class CVConcurrencyTests(TransactionTestCase):
    def test_conditional_revision_write_admits_only_one_concurrent_editor(self):
        user = get_user_model().objects.create_user(email='cv-race@example.invalid', password='test-only')
        workspace = CVWorkspace.objects.create(profile=user.profile, content=content())
        barrier = Barrier(2)

        def edit():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return CVWorkspace.objects.filter(pk=workspace.pk, revision=1).update(revision=F('revision') + 1)
            except OperationalError as error:
                if 'locked' not in str(error).lower():
                    raise
                return 0  # SQLite may reject a concurrent writer rather than wait.
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: edit(), range(2)))
        self.assertEqual(sum(results), 1)
        workspace.refresh_from_db()
        self.assertEqual(workspace.revision, 2)


class CVMigrationTests(TransactionTestCase):
    def test_additive_migration_preserves_existing_profile_and_user(self):
        before = [('profiles', '0004_profile_password_reset_at')]
        executor = MigrationExecutor(connection)
        leaves = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(leaves))
        executor.migrate(before)
        old = executor.loader.project_state(before).apps
        user = old.get_model('accounts', 'User').objects.create(
            email='legacy-cv@example.invalid', password='unchanged-hash', full_name='Existing Name')
        profile = old.get_model('profiles', 'Profile').objects.create(
            user_id=user.pk, headline='Keep headline', cv_file='cvs/existing.docx')
        MigrationExecutor(connection).migrate(leaves)
        self.assertEqual(CVWorkspace.objects.count(), 0)
        self.assertEqual(CVApproval.objects.count(), 0)
        unchanged = get_user_model().objects.get(pk=user.pk)
        self.assertEqual((unchanged.full_name, unchanged.password), ('Existing Name', 'unchanged-hash'))
        # Old application models remain able to read after forward migration.
        previous = old.get_model('profiles', 'Profile').objects.get(pk=profile.pk)
        self.assertEqual(previous.headline, 'Keep headline')
        self.assertEqual(previous.cv_file.name, 'cvs/existing.docx')
