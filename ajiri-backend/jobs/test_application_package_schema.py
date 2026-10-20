"""Dormant additive tables; no package API, document generation or sending."""
import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase

from profiles.models import CVApproval
from .models import Application, ApplicationPackage, ApplicationPackageApproval, Job


class ApplicationPackageSchemaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(email='package@example.invalid')
        job = Job.objects.create(title='Synthetic', company_name='Example', description='Test',
            source_url='https://example.invalid/package', source_name='test')
        self.application = Application.objects.create(user=self.user, job=job, application_method='email')
        self.cv = CVApproval.objects.create(profile=self.user.profile, revision=1,
            content={'name': 'Synthetic'}, content_sha256='a'*64, template_version='cv-v2',
            document='approved-cvs/synthetic.docx', document_sha256='b'*64)

    def package(self, **changes):
        values = dict(application=self.application, revision=1, cv_approval=self.cv,
            job_snapshot={'title': 'Synthetic'}, letter_text='Synthetic letter',
            cv_document='application-packages/cv.docx', letter_document='application-packages/letter.docx',
            cv_sha256='b'*64, letter_sha256='c'*64, content_sha256='d'*64,
            cv_size=20, letter_size=30, template_version='letter-v1')
        values.update(changes)
        return ApplicationPackage.objects.create(**values)

    def assert_rejected(self, action):
        with self.assertRaises(IntegrityError), transaction.atomic():
            action()

    def test_revisions_unique_per_application_and_positive(self):
        self.package()
        self.assert_rejected(lambda: self.package())
        self.assert_rejected(lambda: self.package(revision=0))
        self.package(revision=2)
        other = Application.objects.create(user=get_user_model().objects.create(email='second@example.invalid'),
            job=self.application.job, application_method='external_link')
        self.package(application=other)  # Cross-owner validation is a future service gate, not an SQL FK guarantee.
        self.assertEqual(ApplicationPackage.objects.count(), 3)

    def test_positive_sizes_and_required_provenance(self):
        for field in ('cv_size', 'letter_size'):
            for value in (0, -1, None):
                self.assert_rejected(lambda: self.package(**{field: value}))
        self.assert_rejected(lambda: self.package(cv_approval=None))
        self.assert_rejected(lambda: self.package(application=None))
        self.assert_rejected(lambda: self.package(job_snapshot=None))

    def test_one_approval_and_protected_provenance(self):
        package = self.package()
        evidence = dict(package=package, approved_by=self.user, content_sha256=package.content_sha256,
                        policy_version='documents-v1')
        ApplicationPackageApproval.objects.create(**evidence)
        self.assert_rejected(lambda: ApplicationPackageApproval.objects.create(**evidence))
        with self.assertRaises(ProtectedError):
            self.cv.delete()
        with self.assertRaises(ProtectedError):
            self.user.delete()

    def test_private_random_paths_and_no_email_authorization_fields(self):
        package = self.package()
        names = [package.cv_document.field.generate_filename(package, '../private-name.exe'),
                 package.letter_document.field.generate_filename(package, 'personal.docx')]
        self.assertNotEqual(*names)
        for name in names:
            self.assertRegex(name.replace('\\', '/'), r'^application-packages/[0-9a-f]{32}\.docx$')
        self.assertEqual(package.email_subject, '')
        self.assertEqual(package.email_body, '')
        fields = {f.name for f in ApplicationPackageApproval._meta.fields}
        self.assertTrue(fields.isdisjoint({'send_authorized', 'recipient', 'sent_at', 'token'}))


class ApplicationPackageMigrationTests(TransactionTestCase):
    def test_populated_upgrade_preserves_rows_files_and_old_code_readability(self):
        executor = MigrationExecutor(connection)
        leaves = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(leaves))
        before = [('jobs', '0008_deliverydailybudget_deliveryattempt'),
                  ('profiles', '0005_cv_workspace_approval')]
        after = [('jobs', '0009_application_package_schema'),
                 ('profiles', '0005_cv_workspace_approval')]
        executor.migrate(before)
        old = executor.loader.project_state(before).apps
        User = old.get_model('accounts', 'User')
        Profile = old.get_model('profiles', 'Profile')
        LegacyJob = old.get_model('jobs', 'Job')
        LegacyApplication = old.get_model('jobs', 'Application')
        user = User.objects.create(email='legacy-package@example.invalid', password='unchanged-test-hash')
        profile = Profile.objects.create(user_id=user.pk, headline='Preserve', notify_email=True, notify_in_app=False)
        job = LegacyJob.objects.create(title='Legacy', company_name='Example', description='Preserve',
            source_url='https://example.invalid/legacy-package', source_name='test')
        app = LegacyApplication.objects.create(user_id=user.pk, job_id=job.pk, application_method='email',
            status='sent', generated_cv='legacy/cv.docx', generated_cover_letter='legacy/letter.docx',
            email_body='Existing immutable snapshot')
        old.get_model('profiles', 'CVApproval').objects.create(profile_id=profile.pk, revision=1,
            content={'name': 'Preserve'}, content_sha256='a'*64, template_version='cv-v2',
            document='legacy/approved.docx', document_sha256='b'*64)
        old.get_model('jobs', 'DeliveryDailyBudget').objects.create(scope='global', day=date(2026, 10, 19),
            application_reserved=1)
        old.get_model('jobs', 'DeliveryAttempt').objects.create(user_id=user.pk, application_id=app.pk,
            channel='application', recipient_digest='c'*64, state='accepted')
        labels = [('accounts', 'User'), ('profiles', 'Profile'), ('profiles', 'CVApproval'),
                  ('jobs', 'Application'), ('jobs', 'DeliveryAttempt'), ('jobs', 'DeliveryDailyBudget')]
        rows = {label: list(old.get_model(*label).objects.values()) for label in labels}
        with tempfile.TemporaryDirectory() as directory, self.settings(MEDIA_ROOT=directory):
            (Path(directory)/'legacy').mkdir()
            paths = [Path(directory)/'legacy'/name for name in ('cv.docx', 'letter.docx', 'approved.docx')]
            for path in paths:
                path.write_bytes(b'Synthetic saved bytes: '+path.name.encode())
            saved = [path.read_bytes() for path in paths]
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(after)
            self.assertEqual([(migration.app_label, migration.name, backwards)
                              for migration, backwards in plan],
                             [('jobs', '0009_application_package_schema', False)])
            operations = plan[0][0].operations
            self.assertTrue(all(type(op).__name__ in ('CreateModel', 'AddConstraint') for op in operations))
            executor.migrate(after)
            current = executor.loader.project_state(after).apps
            for label in labels:
                self.assertEqual(list(current.get_model(*label).objects.values()), rows[label])
            self.assertEqual([path.read_bytes() for path in paths], saved)
        self.assertEqual(ApplicationPackage.objects.count(), 0)
        self.assertEqual(ApplicationPackageApproval.objects.count(), 0)
        # Code rollback retains new tables; old models still read existing applications.
        self.assertEqual(LegacyApplication.objects.get(pk=app.pk).email_body, 'Existing immutable snapshot')
        self.assertIn('jobs_applicationpackage', connection.introspection.table_names())
