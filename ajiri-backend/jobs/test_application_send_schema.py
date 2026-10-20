"""Dormant P4a schema: constraints and non-destructive populated migration."""
from datetime import date, timedelta
from pathlib import Path
import tempfile
import uuid
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import FileField, NOT_PROVIDED
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from profiles.models import CVApproval
from .models import (Application, ApplicationPackage, ApplicationPackageApproval,
    ApplicationSendAuthorization as Authorization, ApplicationSendAttemptLink as Link,
    DeliveryAttempt as Attempt, DeliveryDailyBudget, Job)


class ApplicationSendSchemaTests(TestCase):
    def setUp(self):
        cache.clear()
        self.now = timezone.now()
        self.user = get_user_model().objects.create(email='send-schema@example.invalid')
        self.job = Job.objects.create(title='Synthetic', company_name='Example', description='Test',
            source_url='https://example.invalid/send-schema', source_name='test')
        self.app = Application.objects.create(user=self.user, job=self.job, application_method='email',
            application_email='recipient@example.invalid', status='ready_for_review')
        cv = CVApproval.objects.create(profile=self.user.profile, revision=1, content={'synthetic': True},
            content_sha256='a'*64, template_version='cv-v2', document='synthetic/cv.docx', document_sha256='b'*64)
        package = ApplicationPackage.objects.create(application=self.app, revision=1, cv_approval=cv,
            job_snapshot={'title': 'Synthetic'}, letter_text='Synthetic letter', cv_document='synthetic/package-cv.docx',
            letter_document='synthetic/letter.docx', cv_sha256='b'*64, letter_sha256='c'*64,
            content_sha256='d'*64, cv_size=10, letter_size=10, template_version='application-letter-v1')
        self.proof = ApplicationPackageApproval.objects.create(package=package, approved_by=self.user,
            content_sha256='d'*64, policy_version='application-documents-v1')

    def authorization(self, **changes):
        values = dict(request_key=uuid.uuid4(), application=self.app, owner=self.user,
            document_approval=self.proof, plan={'schema_version': 1}, plan_sha256='e'*64,
            policy_version='application-send-v1', authorized_at=self.now,
            expires_at=self.now+timedelta(hours=24))
        values.update(changes)
        return Authorization.objects.create(**values)

    def closed(self, **changes):
        return self.authorization(state='withdrawn', closed_at=self.now, **changes)

    def attempt(self, **changes):
        values = dict(user=self.user, application=self.app, channel='application',
                      state='definite_failure', recipient_digest='f'*64)
        values.update(changes)
        return Attempt.objects.create(**values)

    def reject(self, action):
        with self.assertRaises(IntegrityError), transaction.atomic():
            action()

    def test_one_active_authorization_and_global_request_key_uniqueness(self):
        active = self.authorization()
        self.assertEqual(active.state, 'authorized')
        self.assertIsNone(active.closed_at)
        self.assertIsNone(active.retry_of)
        self.reject(lambda: self.authorization())
        self.reject(lambda: self.closed(request_key=active.request_key))
        Authorization.objects.filter(pk=active.pk).update(state='withdrawn', closed_at=self.now)
        replacement = self.authorization()
        self.assertNotEqual(active.pk, replacement.pk)
        self.closed()
        self.assertEqual(Authorization.objects.count(), 3)

    def test_valid_state_and_matching_closed_timestamp(self):
        self.reject(lambda: self.authorization(state='invalid', closed_at=self.now))
        self.reject(lambda: self.authorization(closed_at=self.now))
        for state in ('withdrawn', 'superseded', 'expired', 'dispatch_started'):
            self.reject(lambda: self.authorization(state=state))
            self.authorization(state=state, closed_at=self.now)
        self.assertEqual(Authorization.objects.count(), 4)

    def test_expiry_required_fields_and_no_implicit_time_or_request_defaults(self):
        for expiry in (self.now, self.now-timedelta(seconds=1)):
            self.reject(lambda: self.closed(expires_at=expiry))
        for field in ('request_key', 'application', 'owner', 'document_approval', 'plan',
                      'authorized_at', 'expires_at'):
            self.reject(lambda: self.closed(**{field: None}))
        for field in ('request_key', 'authorized_at', 'expires_at', 'plan'):
            self.assertIs(Authorization._meta.get_field(field).default, NOT_PROVIDED)

    def test_attempt_and_authorization_links_unique_and_retry_edges_not_self_or_forked(self):
        auth = self.closed()
        original = self.attempt()
        link = Link.objects.create(authorization=auth, attempt=original)
        self.assertIsNone(link.previous_attempt)
        self.reject(lambda: Link.objects.create(authorization=auth, attempt=self.attempt()))
        self.reject(lambda: Link.objects.create(authorization=self.closed(), attempt=original))
        retry = self.attempt()
        retry_auth = self.closed(retry_of=original)
        Link.objects.create(authorization=retry_auth, attempt=retry, previous_attempt=original)
        self.reject(lambda: Link.objects.create(authorization=self.closed(), attempt=self.attempt(), previous_attempt=original))
        another = self.attempt()
        self.reject(lambda: Link.objects.create(authorization=self.closed(), attempt=another, previous_attempt=another))
        Link.objects.create(authorization=self.closed(), attempt=another)
        self.assertEqual(Link.objects.count(), 3)

    def test_protected_evidence_blocks_deleting_referenced_rows(self):
        previous = self.attempt()
        auth = self.closed(retry_of=previous)
        current = self.attempt()
        Link.objects.create(authorization=auth, attempt=current, previous_attempt=previous)
        for row in (self.app, self.user, self.proof, previous, current, auth):
            with self.assertRaises(ProtectedError):
                row.delete()

    def test_schema_rows_do_not_enable_sender_generate_files_or_reserve_budget(self):
        counts = (Attempt.objects.count(), DeliveryDailyBudget.objects.count())
        client = APIClient()
        client.force_authenticate(self.user)
        with patch('django.core.mail.EmailMessage.send') as send, patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            self.authorization()
            response = client.post(f'/api/jobs/applications/{self.app.pk}/send/')
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.data['code'], 'application_sending_disabled')
            send.assert_not_called()
            provider.assert_not_called()
        self.assertEqual((Attempt.objects.count(), DeliveryDailyBudget.objects.count()), counts)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'ready_for_review')
        for model in (Authorization, Link):
            self.assertNotIn(model, admin.site._registry)
            self.assertFalse(any(isinstance(field, FileField) for field in model._meta.fields))

    def test_service_only_invariants_are_not_misrepresented_as_sql_enforcement(self):
        other = get_user_model().objects.create(email='other-schema@example.invalid')
        auth = self.closed(owner=other, plan={})
        # SQL FKs alone cannot validate ownership, full plan schema/hash or channel correspondence.
        # P4b must reject these cases before exposing any writer/dispatcher.
        account_attempt = self.attempt(application=None, channel='password_reset')
        Link.objects.create(authorization=auth, attempt=account_attempt)
        Authorization.objects.filter(pk=auth.pk).update(state='authorized', closed_at=None)
        self.assertEqual(Authorization.objects.get(pk=auth.pk).state, 'authorized')
        # This also demonstrates lifecycle monotonicity belongs to a future service, not SQL here.


class ApplicationSendMigrationTests(TransactionTestCase):
    def test_populated_upgrade_preserves_existing_schema_rows_files_and_old_readers(self):
        executor = MigrationExecutor(connection)
        leaves = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(leaves))
        before = [('jobs', '0009_application_package_schema'), ('profiles', '0005_cv_workspace_approval')]
        executor.migrate(before)
        old_state = executor.loader.project_state(before)
        old = old_state.apps
        user = old.get_model('accounts', 'User').objects.create(email='old-send@example.invalid', password='unchanged')
        profile = old.get_model('profiles', 'Profile').objects.create(user_id=user.pk,
            headline='Preserve', notify_email=True, notify_in_app=False)
        job = old.get_model('jobs', 'Job').objects.create(title='Preserve', company_name='Synthetic',
            description='Preserve', source_url='https://example.invalid/old-send', source_name='test')
        app = old.get_model('jobs', 'Application').objects.create(user_id=user.pk, job_id=job.pk,
            application_method='email', application_email='recipient@example.invalid', status='sent',
            generated_cv='old/cv.docx', generated_cover_letter='old/letter.docx', email_body='Keep snapshot')
        cv = old.get_model('profiles', 'CVApproval').objects.create(profile_id=profile.pk, revision=1,
            content={'synthetic': True}, content_sha256='a'*64, template_version='cv-v2',
            document='old/approved.docx', document_sha256='b'*64)
        package = old.get_model('jobs', 'ApplicationPackage').objects.create(application_id=app.pk,
            revision=1, cv_approval_id=cv.pk, job_snapshot={'title': 'Preserve'}, letter_text='Keep letter',
            cv_document='old/package-cv.docx', letter_document='old/package-letter.docx', cv_size=10,
            letter_size=10, cv_sha256='b'*64, letter_sha256='c'*64, content_sha256='d'*64,
            template_version='application-letter-v1')
        old.get_model('jobs', 'ApplicationPackageApproval').objects.create(package_id=package.pk,
            approved_by_id=user.pk, content_sha256='d'*64, policy_version='application-documents-v1')
        notification = old.get_model('jobs', 'Notification').objects.create(user_id=user.pk, job_id=job.pk,
            match_score=80, sent_email=True, in_app=False)
        old.get_model('jobs', 'DeliveryDailyBudget').objects.create(scope='global', day=date(2026, 10, 20),
            application_reserved=1, account_reserved=1, alert_reserved=1)
        for channel, links in [('application', {'application_id': app.pk}),
                               ('alert', {'notification_id': notification.pk}), ('password_reset', {})]:
            old.get_model('jobs', 'DeliveryAttempt').objects.create(user_id=user.pk, channel=channel,
                recipient_digest='f'*64, state='accepted', **links)
        labels = [('accounts', 'User'), ('profiles', 'Profile'), ('profiles', 'CVApproval'),
            ('jobs', 'Job'), ('jobs', 'Application'), ('jobs', 'ApplicationPackage'),
            ('jobs', 'ApplicationPackageApproval'), ('jobs', 'Notification'),
            ('jobs', 'DeliveryAttempt'), ('jobs', 'DeliveryDailyBudget')]
        rows = {label: list(old.get_model(*label).objects.order_by('pk').values()) for label in labels}
        with tempfile.TemporaryDirectory() as directory, self.settings(MEDIA_ROOT=directory):
            root = Path(directory)/'old'
            root.mkdir()
            paths = [root/name for name in ('cv.docx', 'letter.docx', 'approved.docx', 'package-cv.docx', 'package-letter.docx')]
            for path in paths:
                path.write_bytes(b'Synthetic persisted bytes: '+path.name.encode())
            saved = [path.read_bytes() for path in paths]
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(leaves)
            self.assertEqual([(migration.app_label, migration.name, backwards) for migration, backwards in plan],
                             [('jobs', '0010_application_send_authorization_schema', False)])
            operations = plan[0][0].operations
            self.assertEqual(sum(type(op).__name__ == 'CreateModel' for op in operations), 2)
            self.assertEqual(sum(type(op).__name__ == 'AddConstraint' for op in operations), 6)
            self.assertTrue(all(type(op).__name__ in ('CreateModel', 'AddConstraint') for op in operations))
            executor.migrate(leaves)
            current_state = executor.loader.project_state(leaves)
            current = current_state.apps
            for key, model in old_state.models.items():
                self.assertEqual({name: field.deconstruct() for name, field in model.fields.items()},
                    {name: field.deconstruct() for name, field in current_state.models[key].fields.items()})
                self.assertEqual(model.options, current_state.models[key].options)
            for label in labels:
                self.assertEqual(list(current.get_model(*label).objects.order_by('pk').values()), rows[label])
            self.assertEqual([path.read_bytes() for path in paths], saved)
        self.assertEqual(Authorization.objects.count(), 0)
        self.assertEqual(Link.objects.count(), 0)
        self.assertEqual(old.get_model('jobs', 'Application').objects.get(pk=app.pk).email_body, 'Keep snapshot')
        self.assertEqual(old.get_model('jobs', 'ApplicationPackageApproval').objects.count(), 1)
