"""Schema guarantees only; no transport or quota reservation service is enabled."""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings

from profiles.models import Profile
from profiles.serializers import ProfileSerializer
from .models import Application, DeliveryAttempt, DeliveryDailyBudget, Job, Notification


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DeliverySchemaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='schema@example.invalid', password='strong-schema-pass')
        self.other = get_user_model().objects.create_user(email='other@example.invalid', password='strong-other-pass')
        self.job = Job.objects.create(title='Schema', company_name='Example', description='Synthetic',
                                      source_url='https://example.invalid/schema', source_name='test')
        self.application = Application.objects.create(user=self.user, job=self.job, application_method='email')
        self.notification = Notification.objects.create(user=self.user, job=self.job, match_score=90)

    def attempt(self, **changes):
        values = dict(user=self.user, application=self.application, channel='application', recipient_digest='a' * 64)
        values.update(changes)
        return DeliveryAttempt(**values)

    def assert_db_rejects(self, operation):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                operation()

    def test_new_profiles_unverified_and_api_cannot_set_proof(self):
        profile = Profile.objects.get(user=self.user)
        self.assertIsNone(profile.email_verified_at)
        self.assertEqual(profile.verified_email, '')
        serializer = ProfileSerializer(profile, data={'verified_email': self.user.email,
            'email_verified_at': '2026-10-16T00:00:00Z'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        profile.refresh_from_db()
        self.assertIsNone(profile.email_verified_at)
        self.assertEqual(profile.verified_email, '')
        self.assertNotIn('verified_email', serializer.data)

    def test_account_categories_have_no_document_links_or_token_fields(self):
        for channel in ('email_verification', 'password_reset'):
            attempt = self.attempt(channel=channel, application=None)
            attempt.full_clean()
            attempt.save()
            self.assertEqual(attempt.state, 'reserved')
        fields = {field.name for field in DeliveryAttempt._meta.fields}
        self.assertTrue(fields.isdisjoint({'token', 'body', 'subject', 'recipient_email', 'password'}))

    def test_creation_validation_owner_digest_and_required_links(self):
        for changes in ({'user': None}, {'user': self.other}, {'application': None},
                        {'recipient_digest': 'raw-address@example.invalid'},
                        {'channel': 'alert', 'application': None},
                        {'channel': 'alert', 'application': None, 'notification': self.notification, 'user': self.other}):
            with self.subTest(changes=list(changes)):
                with self.assertRaises(ValidationError):
                    self.attempt(**changes).full_clean()

    def test_database_enforces_channel_state_and_link_shape(self):
        for changes in ({'channel': 'unexpected'}, {'state': 'unexpected'},
                        {'failure_category': 'raw-provider-text'}, {'notification': self.notification},
                        {'channel': 'email_verification'}):
            with self.subTest(changes=changes):
                self.assert_db_rejects(lambda: self.attempt(**changes).save())

    def test_unique_idempotency_and_unresolved_application(self):
        first = self.attempt()
        first.save()
        self.assert_db_rejects(lambda: self.attempt(state='unknown').save())
        first.state = 'definite_failure'
        first.save(update_fields=['state'])
        self.assert_db_rejects(lambda: self.attempt(idempotency_key=first.idempotency_key).save())
        self.attempt().save()  # A definite failure permits a separately reviewed retry.

    def test_unresolved_notification_unique_and_independent_account_purposes(self):
        DeliveryAttempt.objects.create(user=self.user, notification=self.notification,
            channel='alert', recipient_digest='b' * 64, state='unknown')
        self.assert_db_rejects(lambda: DeliveryAttempt.objects.create(user=self.user,
            notification=self.notification, channel='alert', recipient_digest='c' * 64))
        for channel in ('email_verification', 'password_reset'):
            self.attempt(channel=channel, application=None).save()

    def test_erasure_retains_receipt_with_null_links(self):
        attempt = self.attempt()
        attempt.save()
        self.user.delete()
        attempt.refresh_from_db()
        self.assertIsNone(attempt.user_id)
        self.assertIsNone(attempt.application_id)
        self.assertEqual(attempt.recipient_digest, 'a' * 64)
        attempt.full_clean()  # Historical orphan receipt remains representable.

    def test_budget_unique_day_nonnegative_and_defaults(self):
        day = date(2026, 10, 16)
        budget = DeliveryDailyBudget.objects.create(scope='global', day=day)
        self.assertEqual((budget.application_reserved, budget.account_reserved, budget.alert_reserved), (0, 0, 0))
        self.assert_db_rejects(lambda: DeliveryDailyBudget.objects.create(scope='global', day=day))
        for field in ('application_reserved', 'alert_reserved', 'account_reserved'):
            self.assert_db_rejects(lambda: DeliveryDailyBudget.objects.filter(pk=budget.pk).update(**{field: -1}))
        DeliveryDailyBudget.objects.create(scope='global', day=date(2026, 10, 17))
        DeliveryDailyBudget.objects.create(scope=f'user:{self.user.pk}', day=day)
        with self.assertRaises(ValidationError):
            DeliveryDailyBudget(scope='invalid', day=day).full_clean()


class DeliveryMigrationTests(TransactionTestCase):
    def test_existing_rows_preserved_and_old_model_can_read_new_schema(self):
        before = [('profiles', '0002_profile_notify_email_profile_notify_in_app'),
                  ('jobs', '0007_notification_in_app')]
        executor = MigrationExecutor(connection)
        leaves = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(leaves))
        executor.migrate(before)
        old = executor.loader.project_state(before).apps
        user = old.get_model('accounts', 'User').objects.create(email='legacy@example.invalid', password='unchanged-hash')
        profile = old.get_model('profiles', 'Profile').objects.create(user_id=user.pk, headline='Keep me', notify_email=True)
        job = old.get_model('jobs', 'Job').objects.create(title='Legacy', company_name='Example',
            description='Keep', source_url='https://example.invalid/legacy', source_name='test')
        application = old.get_model('jobs', 'Application').objects.create(user_id=user.pk, job_id=job.pk,
            application_method='email', status='sent', email_body='Synthetic snapshot')
        old.get_model('jobs', 'Notification').objects.create(user_id=user.pk, job_id=job.pk,
            match_score=88, sent_email=True, in_app=False)
        MigrationExecutor(connection).migrate(leaves)
        current = Profile.objects.get(pk=profile.pk)
        self.assertIsNone(current.email_verified_at)
        self.assertIsNone(current.password_reset_at)
        self.assertEqual(current.verified_email, '')
        self.assertEqual(current.headline, 'Keep me')
        self.assertTrue(current.notify_email)
        self.assertEqual(get_user_model().objects.get(pk=user.pk).password, 'unchanged-hash')
        self.assertEqual(Application.objects.get(pk=application.pk).email_body, 'Synthetic snapshot')
        self.assertTrue(Notification.objects.get(user_id=user.pk).sent_email)
        self.assertFalse(Notification.objects.get(user_id=user.pk).in_app)
        self.assertEqual(DeliveryAttempt.objects.count(), 0)
        self.assertEqual(DeliveryDailyBudget.objects.count(), 0)
        # Routine rollback keeps additive schema: historical code still reads rows.
        self.assertEqual(old.get_model('profiles', 'Profile').objects.get(pk=profile.pk).headline, 'Keep me')
        self.assertEqual(old.get_model('jobs', 'Application').objects.get(pk=application.pk).status, 'sent')
