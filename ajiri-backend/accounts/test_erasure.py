from io import StringIO
from pathlib import Path
import tempfile
import uuid
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase, override_settings
from jobs.models import Job, Application, DeliveryAttempt, DeliveryDailyBudget
from profiles.models import Skill
from .erasure import read_journal


class AccountErasureTests(TransactionTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.media = self.root / 'media'; self.media.mkdir()
        override = override_settings(MEDIA_ROOT=self.media)
        override.enable(); self.addCleanup(override.disable)
        self.user = get_user_model().objects.create_user(email='erase@example.invalid', password='Synthetic-only-123')
        self.other = get_user_model().objects.create_user(email='keep@example.invalid', password='Synthetic-only-456')
        self.user.profile.cv_file.save('mine.pdf', ContentFile(b'private-owned'), save=True)
        self.other.profile.cv_file.save('other.pdf', ContentFile(b'keep-private'), save=True)
        self.mine = Path(self.user.profile.cv_file.path)
        self.theirs = Path(self.other.profile.cv_file.path)
        self.request = str(uuid.uuid4())
        self.journal = self.root / 'journal'
        ledger_settings = override_settings(ERASURE_LEDGER_DIR=str(self.journal))
        ledger_settings.enable(); self.addCleanup(ledger_settings.disable)
        self.skill = Skill.objects.create(name='Synthetic skill')
        self.user.profile.skills.add(self.skill)
        self.job = Job.objects.create(title='Synthetic', company_name='Example', description='No mail',
            source_name='test', source_url='https://example.invalid/' + self.request)
        self.application = Application.objects.create(user=self.user, job=self.job, application_method='external_link')

    def command(self, mode='dry-run', **extra):
        args = dict(user_id=self.user.pk, request_id=self.request, journal_dir=str(self.journal), mode=mode,
            verified_request=True, writers_paused=True, legal_hold_cleared=True, journal_copied=True, stdout=StringIO())
        args.update(extra)
        call_command('erase_account_data', **args)
        return args['stdout'].getvalue()

    def test_dry_run_has_no_writes_and_execution_requires_attestations(self):
        self.assertIn('no writes', self.command())
        self.assertFalse(self.journal.exists())
        for missing in ('verified_request', 'writers_paused', 'legal_hold_cleared', 'journal_copied'):
            with self.assertRaises(CommandError): self.command('execute', **{missing: False})
        self.assertTrue(self.mine.exists()); self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())

    def test_rows_and_owned_files_removed_shared_data_and_other_owner_preserved(self):
        attempt = DeliveryAttempt.objects.create(user=self.user, channel='email_verification',
            state='accepted', recipient_digest='a' * 64, provider_message_id='private-provider-id')
        self.command('prepare'); self.command('execute')
        self.assertFalse(get_user_model().objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Application.objects.filter(pk=self.application.pk).exists())
        self.assertFalse(self.mine.exists()); self.assertTrue(self.theirs.exists())
        self.assertTrue(Job.objects.filter(pk=self.job.pk).exists()); self.assertTrue(Skill.objects.filter(pk=self.skill.pk).exists())
        attempt.refresh_from_db(); self.assertIsNone(attempt.user_id); self.assertEqual(attempt.provider_message_id, '')
        data = read_journal(self.journal / (self.request + '.signed'))
        self.assertEqual(data['state'], 'complete'); self.assertEqual(data['files'], [])
        self.assertNotIn(self.user.email, str(data))
        self.assertIn('already complete', self.command('execute'))

    def test_file_cleanup_failure_is_resumable_after_database_commit(self):
        self.command('prepare')
        original = Path.unlink
        def unlink(path, *args, **kwargs):
            if path == self.mine: raise PermissionError('synthetic')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'unlink', unlink):
            with self.assertRaisesMessage(CommandError, 'cleanup is pending'): self.command('execute')
        self.assertFalse(get_user_model().objects.filter(pk=self.user.pk).exists())
        self.assertTrue(self.mine.exists())
        self.assertEqual(read_journal(self.journal / (self.request + '.signed'))['state'], 'db_erased')
        self.command('execute'); self.assertFalse(self.mine.exists())

    def test_failed_database_transaction_removes_no_files_and_keeps_user_active(self):
        self.command('prepare')
        with patch('accounts.erasure.erase_rows', side_effect=ValueError('synthetic')):
            with self.assertRaises(CommandError): self.command('execute')
        self.user.refresh_from_db(); self.assertTrue(self.user.is_active); self.assertTrue(self.mine.exists())
        self.assertEqual(read_journal(self.journal / (self.request + '.signed'))['state'], 'prepared')

    def test_unresolved_delivery_and_shared_file_reference_block_before_erasure(self):
        receipt = DeliveryAttempt.objects.create(user=self.user, channel='email_verification', recipient_digest='a' * 64)
        with self.assertRaises(CommandError): self.command()
        receipt.delete()
        other = self.other.profile; other.cv_file = self.user.profile.cv_file.name; other.save()
        with self.assertRaises(CommandError): self.command()
        self.assertTrue(self.mine.exists())

    def test_changed_inventory_or_identity_and_tampering_fail_closed(self):
        self.command('prepare')
        old = self.user.profile; old.cv_file.save('new.pdf', ContentFile(b'new'), save=True)
        with self.assertRaises(CommandError): self.command('execute')
        self.user.refresh_from_db(); self.assertTrue(self.user.is_active)
        path = self.journal / (self.request + '.signed')
        path.write_text('tampered', encoding='utf-8')
        with self.assertRaises(CommandError): self.command('execute')

    def test_completed_ledger_replay_removes_resurrected_account_and_files(self):
        pk, email, filename = self.user.pk, self.user.email, self.user.profile.cv_file.name
        self.command('prepare'); self.command('execute')
        self.user = get_user_model().objects.create_user(id=pk, email=email, password='Synthetic-restored-123')
        profile = self.user.profile; profile.cv_file = filename; profile.save()
        self.mine.write_bytes(b'restored-old-private-file')
        with self.assertRaises(CommandError): self.command('execute')
        self.command('replay')
        self.assertFalse(get_user_model().objects.filter(pk=pk).exists()); self.assertFalse(self.mine.exists())

    def test_replay_never_erases_replacement_identity(self):
        pk = self.user.pk
        self.command('prepare'); self.command('execute')
        self.user = get_user_model().objects.create_user(id=pk, email='replacement@example.invalid', password='Synthetic-only-123')
        with self.assertRaises(CommandError): self.command('replay')
        self.assertTrue(get_user_model().objects.filter(pk=pk).exists())

    @override_settings(EMAIL_PLATFORM_FROM='platform@example.invalid')
    def test_protected_package_authorization_and_session_rows_are_removed(self):
        from datetime import timedelta
        from django.contrib.sessions.backends.db import SessionStore
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        from profiles.cv_test_helpers import approved_cv
        from profiles.cv_builder import content_hash
        from profiles.models import CVApproval
        from jobs.application_packages import save_package, context
        from jobs.package_review import approve_package
        from jobs.send_authorization import plan_response, authorize
        from jobs.models import ApplicationPackage, ApplicationSendAuthorization, ApplicationSendAttemptLink
        profile = self.user.profile
        profile.email_verified_at = timezone.now(); profile.verified_email = self.user.email; profile.save()
        self.application.application_method = 'email'; self.application.application_email = 'synthetic@example.invalid'
        self.application.status = 'ready_for_review'; self.application.save()
        self.job.application_method='email'; self.job.application_email=self.application.application_email; self.job.save()
        cv = approved_cv(self.user)
        package = save_package(self.user, self.application.pk, {'cv_version': cv.pk, 'expected_revision': 0,
            'context_sha256': content_hash(context(self.application)), 'letter_text': 'Synthetic',
            'email_subject': 'Synthetic', 'email_body': 'Synthetic body'})
        approve_package(self.user, self.application.pk, package.pk,1,package.content_sha256)
        plan = plan_response(self.user,self.application)
        auth = authorize(self.user,self.application.pk, {'request_key': uuid.uuid4(), 'package_id': package.pk,
            'expected_revision': 1,'plan_sha256':plan['plan_sha256'],'retry_of':None,'authorization':True})[0]
        receipt = DeliveryAttempt.objects.create(user=self.user,application=self.application,channel='application',
            state='accepted',recipient_digest='a'*64)
        ApplicationSendAttemptLink.objects.create(authorization=auth,attempt=receipt)
        owned = [Path(cv.document.path),Path(package.cv_document.path),Path(package.letter_document.path)]
        RefreshToken.for_user(self.user).blacklist()
        store=SessionStore()
        Session.objects.create(session_key='synthetic-session',session_data=store.encode({'_auth_user_id':str(self.user.pk)}),
            expire_date=timezone.now()+timedelta(days=1))
        self.command('prepare');self.command('execute')
        for model in (CVApproval,ApplicationPackage,ApplicationSendAuthorization,ApplicationSendAttemptLink,OutstandingToken,Session):
            with self.subTest(model=model._meta.label):
                self.assertEqual(model.objects.count(),0)
        self.assertTrue(all(not path.exists() for path in owned))
        receipt.refresh_from_db();self.assertIsNone(receipt.user_id);self.assertIsNone(receipt.application_id)
