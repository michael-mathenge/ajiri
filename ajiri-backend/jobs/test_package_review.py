from io import BytesIO
import threading
from unittest.mock import patch

from docx import Document
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings

from .application_packages import save_package, PackageConflict
from .package_review import approve_package, POLICY_VERSION
from . import test_application_packages as fixtures
from .models import Application, ApplicationPackage, ApplicationPackageApproval, DeliveryAttempt, DeliveryDailyBudget


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PackageReviewTests(TestCase):
    payload = fixtures.ApplicationPackageTests.payload
    save = fixtures.ApplicationPackageTests.save
    files = fixtures.ApplicationPackageTests.files

    def setUp(self):
        fixtures.ApplicationPackageTests.setUp(self)
        self.assertEqual(self.save().status_code, 201)
        self.package = ApplicationPackage.objects.get()
        self.review_url = self.url + str(self.package.pk) + '/'
        self.approve_url = self.review_url + 'approve/'

    def approve(self, **changes):
        data = {'approval': True, 'expected_revision': self.package.revision,
                'content_sha256': self.package.content_sha256}
        data.update(changes)
        return self.client.post(self.approve_url, data, format='json')

    def test_preview_and_downloads_use_actual_saved_bytes_and_never_regenerate(self):
        with patch('jobs.application_packages.render_letter', side_effect=AssertionError('No regeneration')):
            preview = self.client.get(self.review_url)
            self.assertEqual(preview.status_code, 200)
            for kind, field in [('cv', self.package.cv_document), ('cover-letter', self.package.letter_document)]:
                with field.open('rb') as stream:
                    expected = stream.read()
                download = self.client.get(self.review_url+f'documents/{kind}/')
                self.assertEqual(download.status_code, 200)
                self.assertEqual(download.content, expected)
                self.assertEqual([row['text'] for row in preview.data['previews'][kind]],
                                 [row.text for row in Document(BytesIO(expected)).paragraphs])
                head = self.client.head(self.review_url+f'documents/{kind}/')
                self.assertEqual(head.content, b'')
                self.assertEqual(int(head['Content-Length']), len(expected))
                self.assertEqual(head['Cache-Control'], 'private, no-store')
        self.assertIsNone(preview.data['approval'])
        self.assertNotIn('application-packages/', str(preview.data))
        self.assertNotIn('approved-cvs/', str(preview.data))
        self.assertEqual(preview['Cache-Control'], 'private, no-store')

    def test_explicit_approval_is_bound_to_latest_revision_and_idempotent_without_side_effects(self):
        counts = (DeliveryAttempt.objects.count(), DeliveryDailyBudget.objects.count())
        files = self.files()
        app = Application.objects.values().get(pk=self.app.pk)
        with patch('django.core.mail.EmailMessage.send') as send, patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            first = self.approve()
            self.assertEqual(first.status_code, 201)
            second = self.approve()
            self.assertEqual(second.status_code, 200)
            self.assertEqual(first.data, second.data)
            send.assert_not_called()
            provider.assert_not_called()
        proof = ApplicationPackageApproval.objects.get()
        self.assertEqual(proof.approved_by, self.user)
        self.assertEqual(proof.policy_version, POLICY_VERSION)
        self.assertEqual(proof.content_sha256, self.package.content_sha256)
        self.assertEqual((DeliveryAttempt.objects.count(), DeliveryDailyBudget.objects.count()), counts)
        self.assertEqual(Application.objects.values().get(pk=self.app.pk), app)
        self.assertEqual(self.files(), files)

    def test_explicit_true_and_exact_input_types_required(self):
        for changes in [{'approval': False}, {'approval': 'true'}, {'approval': 1}, {'approval': None},
                        {'expected_revision': True}, {'expected_revision': '1'}, {'send_authorized': True}]:
            self.assertEqual(self.approve(**changes).status_code, 400)
        self.assertEqual(self.client.post(self.approve_url, {}, format='json').status_code, 400)
        self.assertEqual(ApplicationPackageApproval.objects.count(), 0)

    def test_stale_hash_revision_and_newer_package_do_not_reuse_approval(self):
        self.assertEqual(self.approve(content_sha256='0'*64).status_code, 409)
        self.assertEqual(self.approve(expected_revision=2).status_code, 409)
        self.assertEqual(self.approve().status_code, 201)
        old = ApplicationPackageApproval.objects.values().get()
        self.assertEqual(self.save(expected_revision=1, letter_text='A new letter').status_code, 201)
        self.assertEqual(self.approve().status_code, 409)
        history = self.client.get(self.review_url).data
        self.assertFalse(history['is_latest'])
        self.assertFalse(history['approvable'])
        self.assertIsNotNone(history['approval'])
        self.assertEqual(ApplicationPackageApproval.objects.values().get(), old)
        latest = ApplicationPackage.objects.latest('revision')
        self.assertFalse(ApplicationPackageApproval.objects.filter(package=latest).exists())

    def test_profile_and_job_edits_leave_snapshots_and_approval_unchanged(self):
        self.assertEqual(self.approve().status_code, 201)
        files = self.files()
        self.user.full_name = '../Current / Name'
        self.user.save()
        self.user.profile.bio = 'Changed profile'
        self.user.profile.save()
        self.job.title = 'Changed role'
        self.job.company_name = '../New / Company'
        self.job.save()
        preview = self.client.get(self.review_url)
        self.assertEqual(preview.data['job_context']['title'], 'Engineer')
        self.assertIsNotNone(preview.data['approval'])
        download = self.client.get(self.review_url+'documents/cv/')
        self.assertEqual(download.status_code, 200)
        self.assertNotIn('../', download['Content-Disposition'])
        self.assertEqual(self.files(), files)

    def test_owner_scope_for_preview_approval_get_head_and_application_path(self):
        routes = [self.review_url, self.review_url+'documents/cv/', self.review_url+'documents/cover-letter/']
        self.client.force_authenticate(self.other)
        for route in routes:
            self.assertEqual(self.client.get(route).status_code, 404)
            self.assertEqual(self.client.head(route).status_code, 404)
        self.assertEqual(self.approve().status_code, 404)
        self.client.force_authenticate(None)
        for route in routes:
            self.assertEqual(self.client.get(route).status_code, 401)
        self.assertEqual(self.approve().status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(self.review_url.replace(f'/{self.app.pk}/packages/', '/999999/packages/')).status_code, 404)
        self.assertEqual(self.client.get(self.review_url+'documents/unknown/').status_code, 404)
        self.assertEqual(self.client.patch(self.review_url, {}, format='json').status_code, 405)
        self.assertEqual(self.client.delete(self.review_url).status_code, 405)

    def test_missing_or_corrupt_either_file_blocks_entire_package_and_approval(self):
        for field in (self.package.cv_document, self.package.letter_document):
            with field.open('rb') as stream:
                original = stream.read()
            for payload in [b'corrupt', None]:
                if payload is None:
                    field.storage.delete(field.name)
                else:
                    with field.open('wb') as stream:
                        stream.write(payload)
                for url in [self.review_url, self.review_url+'documents/cv/', self.review_url+'documents/cover-letter/']:
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 503)
                    self.assertNotIn(field.name, str(response.data))
                    self.assertEqual(response['Cache-Control'], 'private, no-store')
                self.assertEqual(self.approve().status_code, 503)
                self.assertEqual(ApplicationPackageApproval.objects.count(), 0)
                field.storage.delete(field.name)
                field.storage.save(field.name, BytesIO(original))

    def test_metadata_hash_provenance_sizes_and_approval_corruption_fail_closed(self):
        for changes in [{'letter_text': 'tampered'}, {'cv_size': self.package.cv_size + 1},
                        {'letter_size': 2*1024*1024+1}, {'content_sha256': '0'*64}]:
            original = {key: getattr(self.package, key) for key in changes}
            ApplicationPackage.objects.filter(pk=self.package.pk).update(**changes)
            self.assertEqual(self.client.get(self.review_url).status_code, 503)
            self.assertEqual(self.approve().status_code, 409 if 'content_sha256' in changes else 503)
            ApplicationPackage.objects.filter(pk=self.package.pk).update(**original)
        self.assertEqual(self.approve().status_code, 201)
        ApplicationPackageApproval.objects.filter(package=self.package).update(approved_by=self.other)
        self.assertEqual(self.client.get(self.review_url).status_code, 503)

    def test_saved_snapshot_does_not_require_source_file_to_still_exist(self):
        self.cv.document.storage.delete(self.cv.document.name)
        self.assertEqual(self.client.get(self.review_url).status_code, 200)
        self.assertEqual(self.approve().status_code, 201)
        self.assertEqual(self.client.get(self.review_url+'documents/cv/').status_code, 200)

    def test_blocked_status_or_delivery_receipt_prevents_approval_but_not_history_reads(self):
        for state in ['sent', 'dismissed']:
            Application.objects.filter(pk=self.app.pk).update(status=state)
            self.assertEqual(self.approve().status_code, 409)
            self.assertFalse(self.client.get(self.review_url).data['approvable'])
        Application.objects.filter(pk=self.app.pk).update(status='ready_for_review')
        for state in ['reserved', 'unknown', 'accepted']:
            receipt = DeliveryAttempt.objects.create(application=self.app, user=self.user, channel='application',
                                                     recipient_digest='a'*64, state=state)
            self.assertEqual(self.approve().status_code, 409)
            self.assertFalse(self.client.get(self.review_url).data['approvable'])
            receipt.delete()
        self.assertEqual(ApplicationPackageApproval.objects.count(), 0)

    def test_parser_failure_is_generic_and_no_claim_is_recorded(self):
        with patch('jobs.package_review.Document', side_effect=ValueError('sensitive malicious exception text')):
            response = self.client.get(self.review_url)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('sensitive', str(response.data))
            self.assertEqual(self.approve().status_code, 503)
        self.assertEqual(ApplicationPackageApproval.objects.count(), 0)


class PackageApprovalConcurrencyTests(TransactionTestCase):
    payload = fixtures.ApplicationPackageTests.payload
    save = fixtures.ApplicationPackageTests.save

    def setUp(self):
        fixtures.ApplicationPackageTests.setUp(self)
        self.assertEqual(self.save().status_code, 201)
        self.package = ApplicationPackage.objects.get()

    def race(self, actions):
        from django.db.models.query import QuerySet
        original = QuerySet.update
        barrier = threading.Barrier(2)
        errors, results = [], []

        def update(queryset, **kwargs):
            if queryset.model is Application and kwargs.get('status') is not None:
                barrier.wait(10)
            return original(queryset, **kwargs)

        def run(action):
            close_old_connections()
            try:
                action()
                results.append('committed')
            except PackageConflict:
                results.append('conflict')
            except BaseException as error:
                errors.append(error)
            finally:
                close_old_connections()

        with patch.object(QuerySet, 'update', update):
            threads = [threading.Thread(target=run, args=(action,)) for action in actions]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(15)
            self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertIn('committed', results)

    def approve(self):
        return approve_package(self.user, self.app.pk, self.package.pk, 1, self.package.content_sha256)

    def test_simultaneous_identical_approvals_create_only_one_proof(self):
        self.race([self.approve, self.approve])
        self.assertEqual(ApplicationPackageApproval.objects.count(), 1)

    def test_new_revision_and_approval_race_never_approves_the_new_unreviewed_package(self):
        data = self.payload(expected_revision=1, letter_text='New unreviewed revision')
        self.race([self.approve, lambda: save_package(self.user, self.app.pk, data)])
        for proof in ApplicationPackageApproval.objects.select_related('package'):
            self.assertEqual(proof.package.revision, 1)
            self.assertEqual(proof.content_sha256, self.package.content_sha256)
        if ApplicationPackage.objects.filter(revision=2).exists():
            self.assertFalse(ApplicationPackageApproval.objects.filter(package__revision=2).exists())
