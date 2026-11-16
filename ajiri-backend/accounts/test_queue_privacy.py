"""Synthetic accounts and outbox rows; never activates a worker or transport."""
from io import StringIO
import json
from pathlib import Path
import tempfile
import uuid

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase, override_settings

from accounts.erasure import inventory
from accounts.queue_privacy import owned_tasks
from jobs.models import DeliveryTask, Notification, Job


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class QueuePrivacyTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='queue-owner@example.invalid')
        self.other = get_user_model().objects.create_user(email='queue-other@example.invalid')
        self.job = Job.objects.create(title='Synthetic', company_name='Fixture',
            source_name='fixture', source_url='https://example.invalid/queue-privacy')
        self.notification = Notification.objects.create(user=self.user, job=self.job, match_score=80)
        self.other_notification = Notification.objects.create(user=self.other, job=self.job, match_score=80)

    def task(self, **values):
        return DeliveryTask.objects.create(dedupe_key=uuid.uuid4(), kind='alert',
            **{'owner': self.user, 'notification': self.notification, **values})

    def test_every_nonterminal_state_blocks_inventory_without_account_or_task_writes(self):
        row = self.task()
        for state in ('pending', 'publishing', 'published', 'publication_unknown', 'running',
                      'blocked', 'needs_reconciliation'):
            DeliveryTask.objects.filter(pk=row.pk).update(state=state)
            with self.subTest(state=state), self.assertRaises(CommandError):
                inventory(self.user)
            self.user.refresh_from_db(); row.refresh_from_db()
            self.assertTrue(self.user.is_active)
            self.assertEqual(row.state, state)
        for state in ('succeeded', 'dead'):
            DeliveryTask.objects.filter(pk=row.pk).update(state=state)
            self.assertEqual(inventory(self.user), [])

    def test_cross_owner_or_missing_owner_references_block_before_erasure(self):
        for values in ({'owner': self.other}, {'owner': None},
                       {'notification': self.other_notification}):
            row = self.task(state='succeeded', **values)
            with self.subTest(values=tuple(values)), self.assertRaises(CommandError):
                inventory(self.user)
            DeliveryTask.objects.filter(pk=row.pk).delete()  # Disposable fixture only.

    def test_unrelated_other_owner_work_does_not_block_or_export(self):
        self.task(owner=self.other, notification=self.other_notification)
        self.assertEqual(inventory(self.user), [])
        self.assertFalse(owned_tasks(self.user).exists())

    def test_export_includes_owned_pending_task_but_omits_internal_claim_and_dedupe_keys(self):
        row = self.task(lease_token=uuid.uuid4())
        other = self.task(owner=self.other, notification=self.other_notification)
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)/'export'
            call_command('export_account_data', user_id=self.user.pk, destination=str(destination),
                         verified_request=True, writers_paused=True, stdout=StringIO())
            records = json.loads((destination/'account.json').read_text())['records']['delivery_task']
        self.assertEqual([record['id'] for record in records], [str(row.pk)])
        self.assertNotIn('lease_token', records[0]); self.assertNotIn('dedupe_key', records[0])
        self.assertNotIn(str(other.pk), json.dumps(records))
        row.refresh_from_db()
        self.assertEqual(row.state, 'pending')

    def test_terminal_erasure_retains_pseudonymous_settlement_and_other_owner(self):
        row = self.task(state='succeeded')
        with tempfile.TemporaryDirectory() as folder:
            journal = Path(folder)/'journal'
            with override_settings(ERASURE_LEDGER_DIR=str(journal)):
                options = dict(user_id=self.user.pk, request_id=str(uuid.uuid4()), journal_dir=str(journal),
                    verified_request=True, writers_paused=True, legal_hold_cleared=True,
                    journal_copied=True, stdout=StringIO())
                call_command('erase_account_data', mode='prepare', **options)
                call_command('erase_account_data', mode='execute', **options)
        row.refresh_from_db()
        self.assertEqual(row.state, 'succeeded')
        self.assertIsNone(row.owner_id); self.assertIsNone(row.notification_id)
        self.assertTrue(type(self.other).objects.filter(pk=self.other.pk).exists())

    def test_cross_owner_export_creates_no_completion_or_destination(self):
        self.task(notification=self.other_notification)
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)/'export'
            with self.assertRaises(CommandError):
                call_command('export_account_data', user_id=self.user.pk, destination=str(destination),
                             verified_request=True, writers_paused=True, stdout=StringIO())
            self.assertFalse(destination.exists())
