import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
import threading
from unittest.mock import patch

from docx import Document
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.db import OperationalError, close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient

from profiles.cv_test_helpers import approved_cv
from .application_packages import context, render_letter, save_package, PackageConflict
from profiles.cv_builder import content_hash
from .models import Application, ApplicationPackage, ApplicationPackageApproval, DeliveryAttempt, DeliveryDailyBudget, Job


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ApplicationPackageTests(TestCase):
    def setUp(self):
        cache.clear()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        settings = override_settings(MEDIA_ROOT=temporary.name,
            REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
                            'DEFAULT_THROTTLE_RATES': {'apply': '1000/min'}})
        settings.enable()
        self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_user(email='package@example.invalid', password='synthetic')
        self.other = get_user_model().objects.create_user(email='other@example.invalid', password='synthetic')
        self.job = Job.objects.create(title='Engineer', company_name='Example', description='<script>not executable</script>',
            requirements='Synthetic requirements', source_url='https://example.invalid/job', source_name='test')
        self.app = Application.objects.create(user=self.user, job=self.job, status='ready_for_review',
            application_method='external_link', generated_cv='legacy.docx', generated_cover_letter='legacy-letter.docx')
        self.cv = approved_cv(self.user)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f'/api/jobs/applications/{self.app.pk}/packages/'
        self.draft_url = f'/api/jobs/applications/{self.app.pk}/package-draft/'
        mail.get_connection()

    def payload(self, **changes):
        data = {'cv_version': str(self.cv.pk), 'expected_revision': 0,
            'context_sha256': content_hash(context(self.app)), 'letter_text': 'My exact\nletter <literal>',
            'email_subject': '', 'email_body': ''}
        data.update(changes)
        return data

    def save(self, **changes):
        return self.client.post(self.url, self.payload(**changes), format='json')

    def files(self):
        return {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}

    def test_save_has_exact_cv_literal_letter_and_no_mail_provider_or_ledger_side_effects(self):
        original = Application.objects.values().get(pk=self.app.pk)
        counts = (DeliveryAttempt.objects.count(), DeliveryDailyBudget.objects.count())
        mail.outbox.clear()
        with patch('django.core.mail.EmailMessage.send') as send, patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            draft = self.client.post(self.draft_url, {'cv_version': str(self.cv.pk)}, format='json')
            self.assertEqual(draft.status_code, 200)
            self.assertIn('Synthetic CV.', draft.data['letter_text'])
            self.assertNotIn('strong match', draft.data['letter_text'])
            self.assertEqual(ApplicationPackage.objects.count(), 0)
            response = self.save()
            self.assertEqual(response.status_code, 201)
            send.assert_not_called()
            provider.assert_not_called()
        package = ApplicationPackage.objects.get()
        with self.cv.document.open('rb') as stream:
            expected = stream.read()
        with package.cv_document.open('rb') as stream:
            self.assertEqual(stream.read(), expected)
        with package.letter_document.open('rb') as stream:
            data = stream.read()
        self.assertEqual(hashlib.sha256(data).hexdigest(), package.letter_sha256)
        self.assertEqual([p.text for p in Document(BytesIO(data)).paragraphs], ['My exact', 'letter <literal>'])
        self.assertEqual(Application.objects.values().get(pk=self.app.pk), original)
        self.assertEqual((DeliveryAttempt.objects.count(), DeliveryDailyBudget.objects.count()), counts)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(ApplicationPackageApproval.objects.count(), 0)
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertNotIn('cv_document', response.data)

    def test_new_revisions_do_not_mutate_prior_rows_or_file_bytes(self):
        self.assertEqual(self.save().status_code, 201)
        first = ApplicationPackage.objects.values().get()
        files = self.files()
        self.user.profile.bio = 'Later profile edit'
        self.user.profile.save()
        self.assertEqual(self.save(expected_revision=1, letter_text='New letter').status_code, 201)
        self.assertEqual(ApplicationPackage.objects.values().get(pk=first['id']), first)
        for name, data in files.items():
            self.assertEqual(self.files()[name], data)
        self.assertEqual(list(ApplicationPackage.objects.order_by('revision').values_list('revision', flat=True)), [1, 2])

    def test_stale_revision_or_changed_job_conflicts_and_cleans_staged_files(self):
        self.assertEqual(self.save().status_code, 201)
        files = self.files()
        self.assertEqual(self.save().status_code, 409)
        self.assertEqual(self.files(), files)
        stale_context = self.payload()['context_sha256']
        self.job.description = 'Job changed'
        self.job.save()
        self.assertEqual(self.save(expected_revision=1, context_sha256=stale_context).status_code, 409)
        self.assertEqual(self.files(), files)

    def test_cross_owner_and_anonymous_cannot_read_save_or_draft(self):
        self.client.force_authenticate(self.other)
        for response in [self.client.get(self.url), self.save(), self.client.post(self.draft_url, {'cv_version': str(self.cv.pk)}, format='json')]:
            self.assertEqual(response.status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.assertEqual(self.save().status_code, 401)
        self.client.force_authenticate(self.user)
        foreign = approved_cv(self.other)
        self.assertEqual(self.save(cv_version=str(foreign.pk)).status_code, 404)

    def test_invalid_text_unknown_fields_and_types_are_rejected_without_files(self):
        files = self.files()
        for changes in [{'expected_revision': True}, {'expected_revision': '0'}, {'letter_text': ' '},
                        {'letter_text': '\x00'}, {'letter_text': 'x'*10001}, {'email_body': []},
                        {'recipient': 'unexpected@example.invalid'}, {'approval': True}]:
            self.assertEqual(self.save(**changes).status_code, 400, changes.keys())
        self.assertEqual(self.files(), files)

    def test_missing_or_changed_cv_bytes_fail_closed(self):
        with self.cv.document.open('wb') as stream:
            stream.write(b'Changed')
        self.assertEqual(self.save().status_code, 503)
        self.cv.document.storage.delete(self.cv.document.name)
        self.assertEqual(self.save().status_code, 503)
        self.assertEqual(ApplicationPackage.objects.count(), 0)

    def test_transaction_failure_cleans_only_own_staged_files(self):
        files = self.files()
        with patch.object(ApplicationPackage, 'save', side_effect=OperationalError('synthetic failure')):
            self.assertEqual(self.save().status_code, 503)
        self.assertEqual(self.files(), files)
        self.assertEqual(ApplicationPackage.objects.count(), 0)

    def test_status_delivery_and_job_blockers(self):
        for state in ['sent', 'dismissed']:
            Application.objects.filter(pk=self.app.pk).update(status=state)
            self.assertEqual(self.save().status_code, 409)
        Application.objects.filter(pk=self.app.pk).update(status='ready_for_review')
        for state in ['reserved', 'unknown', 'accepted']:
            receipt = DeliveryAttempt.objects.create(user=self.user, application=self.app,
                channel='application', state=state, recipient_digest='a'*64)
            self.assertEqual(self.save().status_code, 409)
            self.assertFalse(self.client.get(self.url).data['editable'])
            receipt.delete()
        self.job.is_flagged_scam = True
        self.job.save()
        self.assertEqual(self.save().status_code, 409)

    def test_paginated_private_context_without_storage_paths_or_sending_permission(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['latest_revision'], 0)
        self.assertTrue(response.data['editable'])
        self.assertEqual(self.save().status_code, 201)
        first = ApplicationPackage.objects.get()
        rows = []
        for revision in range(2, 23):
            row = ApplicationPackage.objects.get(pk=first.pk)
            row.pk = None
            row.revision = revision
            rows.append(row)
        ApplicationPackage.objects.bulk_create(rows)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['results']), 20)
        self.assertEqual(response.data['latest_revision'], 22)
        self.assertIsNotNone(response.data['next'])
        self.assertEqual(len(self.client.get(self.url+'?page=2').data['results']), 2)
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_legacy_send_is_blocked_before_claim_even_with_new_package(self):
        self.app.application_method = 'email'
        self.app.save()
        self.assertEqual(self.save().status_code, 201)
        with patch('django.core.mail.EmailMessage.send') as send:
            self.assertEqual(self.client.post(f'/api/jobs/applications/{self.app.pk}/send/').status_code, 409)
            send.assert_not_called()
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'ready_for_review')


class PackageConcurrencyTests(TransactionTestCase):
    setUp = ApplicationPackageTests.setUp
    payload = ApplicationPackageTests.payload
    files = ApplicationPackageTests.files

    def test_overlapping_saves_one_revision_and_loser_cleans_only_its_files(self):
        barrier = threading.Barrier(2)
        results, errors = [], []
        data = self.payload()
        # Synchronize AFTER initial reads, BEFORE transaction claims, with separate DB connections.
        def stage(text):
            result = render_letter(text)
            barrier.wait(10)
            return result

        def save():
            close_old_connections()
            try:
                save_package(self.user, self.app.pk, data)
                results.append('saved')
            except PackageConflict:
                results.append('conflict')
            except BaseException as error:
                errors.append(error)
            finally:
                close_old_connections()

        with patch('jobs.application_packages.render_letter', side_effect=stage):
            threads = [threading.Thread(target=save) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(15)
            self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(sorted(results), ['conflict', 'saved'])
        self.assertEqual(ApplicationPackage.objects.count(), 1)
        self.assertEqual(len(self.files()), 3)  # approved source plus winner's two documents
