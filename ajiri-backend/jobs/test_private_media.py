from profiles.upload_fixtures import pdf_bytes
from profiles.cv_test_helpers import approved_cv
from django.core.cache import cache
import importlib
from io import StringIO
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import clear_url_caches
from rest_framework.test import APIClient

from .models import Application, Job


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PrivateMediaTests(TestCase):
    def setUp(self):
        cache.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'old'
        self.source.mkdir()
        self.destination = self.root / 'private'
        self.override = override_settings(MEDIA_ROOT=self.source)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.user = get_user_model().objects.create_user(email='private@example.com', password='test-password')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.client.patch('/api/profiles/me/', {'cv_file': SimpleUploadedFile('cv.pdf', pdf_bytes())}, format='multipart')
        self.user.profile.refresh_from_db()
        self.job = Job.objects.create(title='Test', company_name='Test', description='Test', source_name='test', source_url='https://example.com/private')
        approval = approved_cv(self.user)
        response = self.client.post(f'/api/jobs/{self.job.pk}/apply/', {'cv_version': str(approval.pk)}, format='json')
        self.assertEqual(response.status_code, 201)
        self.app = Application.objects.get(pk=response.data['id'])

    def command(self, *flags, **kwargs):
        output = StringIO()
        call_command('relocate_private_media', source=str(self.source), destination=str(self.destination), stdout=output, *flags, **kwargs)
        return output.getvalue()

    def test_direct_urls_denied_in_both_debug_modes(self):
        import config.urls
        try:
            for debug in (True, False):
                with self.subTest(debug=debug), override_settings(DEBUG=debug):
                    importlib.reload(config.urls)
                    clear_url_caches()
                    for name in (self.user.profile.cv_file.name, self.app.generated_cv.name, self.app.generated_cover_letter.name, '%2e%2e/cvs/cv.pdf'):
                        for method in (self.client.get, self.client.head):
                            self.assertEqual(method('/media/' + name).status_code, 404)
        finally:
            importlib.reload(config.urls)
            clear_url_caches()

    def test_copy_keeps_names_and_owner_endpoints_and_orphans(self):
        (self.source / 'orphan.pdf').write_bytes(b'orphan')
        names = [self.user.profile.cv_file.name, self.app.generated_cv.name, self.app.generated_cover_letter.name]
        expected = [(self.source / name).read_bytes() for name in names]
        self.command(apply=True, manifest=str(self.root / 'manifest.json'))
        self.command(verify=True)
        self.command(apply=True)  # safe identical rerun
        self.assertEqual((self.destination / 'orphan.pdf').read_bytes(), b'orphan')
        with override_settings(MEDIA_ROOT=self.destination):
            for url, content in zip(['/api/profiles/me/cv/', f'/api/jobs/applications/{self.app.pk}/documents/cv/', f'/api/jobs/applications/{self.app.pk}/documents/cover-letter/'], expected):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b''.join(response.streaming_content), content)
                self.assertIn('no-store', response['Cache-Control'])
                self.assertIn('attachment', response['Content-Disposition'])
                response.close()
            other = get_user_model().objects.create_user(email='other-private@example.com', password='test-password')
            self.client.force_authenticate(other)
            for kind in ('cv', 'cover-letter'):
                self.assertEqual(self.client.get(f'/api/jobs/applications/{self.app.pk}/documents/{kind}/').status_code, 404)
            self.assertEqual(self.client.get('/api/profiles/me/cv/').status_code, 404)
            self.client.force_authenticate(None)
            for url in ['/api/profiles/me/cv/', f'/api/jobs/applications/{self.app.pk}/documents/cv/', f'/api/jobs/applications/{self.app.pk}/documents/cover-letter/']:
                self.assertEqual(self.client.get(url).status_code, 401)
        self.user.profile.refresh_from_db()
        self.app.refresh_from_db()
        self.assertEqual(names, [self.user.profile.cv_file.name, self.app.generated_cv.name, self.app.generated_cover_letter.name])
        for name, content in zip(names, expected):
            self.assertEqual((self.source / name).read_bytes(), content)

    def test_default_dry_run_writes_nothing(self):
        self.assertIn('Dry-run', self.command(manifest=str(self.root / 'plan.json')))
        self.assertFalse(self.destination.exists())
        self.assertFalse((self.root / 'plan.json').exists())

    def test_shared_references_and_verify_missing(self):
        self.app.generated_cv = self.user.profile.cv_file.name
        self.app.save(update_fields=['generated_cv'])
        self.assertIn('referenced names: 2', self.command())
        with self.assertRaises(CommandError):
            self.command(verify=True)
        self.command(apply=True)
        self.command(verify=True)

    def test_conflict_never_overwrites(self):
        target = self.destination / self.user.profile.cv_file.name
        target.parent.mkdir(parents=True)
        target.write_bytes(b'conflicting')
        with self.assertRaises(CommandError):
            self.command(apply=True)
        self.assertEqual(target.read_bytes(), b'conflicting')

    def test_missing_reference_aborts_before_copy(self):
        (self.source / self.user.profile.cv_file.name).unlink()
        with self.assertRaises(CommandError):
            self.command(apply=True)
        self.assertFalse(self.destination.exists())

    def test_unsafe_database_path_aborts(self):
        self.user.profile.cv_file = '../escape.pdf'
        self.user.profile.save()
        with self.assertRaises(CommandError):
            self.command()

    def test_nested_and_public_roots_rejected(self):
        for target in (self.source, self.source / 'nested', self.source.parent, Path(__file__).parent.parent / 'media' / 'private'):
            with self.subTest(target=target), self.assertRaises(CommandError):
                call_command('relocate_private_media', source=str(self.source), destination=str(target), stdout=StringIO())

    def test_interrupted_copy_resumes(self):
        with patch('jobs.management.commands.relocate_private_media.os.link', side_effect=OSError('interrupted')):
            with self.assertRaises(CommandError):
                self.command(apply=True)
        self.assertFalse(list(self.destination.rglob('.relocate-*')))
        self.command(apply=True)
        self.command(verify=True)

    def test_space_and_permission_errors_are_safe(self):
        with patch('jobs.management.commands.relocate_private_media.shutil.disk_usage') as usage:
            usage.return_value.free = 0
            with self.assertRaises(CommandError):
                self.command(apply=True)
        self.assertFalse(self.destination.exists())
        with patch('jobs.management.commands.relocate_private_media.digest', side_effect=PermissionError):
            with self.assertRaises(CommandError):
                self.command(apply=True)

    def test_symlink_is_rejected(self):
        link = self.source / 'linked.pdf'
        try:
            link.symlink_to(self.source / self.user.profile.cv_file.name)
        except OSError:
            self.skipTest('Creating symlinks requires Windows developer mode or privileges.')
        with self.assertRaises(CommandError):
            self.command(apply=True)

    def test_unreadable_directory_aborts_instead_of_silently_skipping(self):
        def fail_walk(*args, **kwargs):
            kwargs['onerror'](PermissionError('unreadable directory'))
            return iter(())
        with patch('jobs.management.commands.relocate_private_media.os.walk', side_effect=fail_walk):
            with self.assertRaises(CommandError):
                self.command(apply=True)
        self.assertFalse(self.destination.exists())
