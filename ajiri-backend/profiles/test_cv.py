from .upload_fixtures import pdf_bytes, docx_bytes, doc_bytes
from django.core.cache import cache
import tempfile
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from jobs.models import Application, Job


class ProfileCVTests(TestCase):
    def setUp(self):
        cache.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        override = override_settings(MEDIA_ROOT=self.tmp.name)
        override.enable()
        self.addCleanup(override.disable)
        self.user = get_user_model().objects.create_user(email='cv@example.com', password='test-password')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_edit_contact_skills_and_clear_skills(self):
        data = {'full_name': 'Test Name', 'phone_number': '0700000000', 'headline': 'Developer', 'bio': 'Build things', 'location': 'Nairobi', 'years_of_experience': 3, 'skill_names': ['Python', 'React']}
        response = self.client.patch('/api/profiles/me/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['full_name'], 'Test Name')
        self.assertEqual({skill['name'] for skill in response.data['skills']}, {'Python', 'React'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '0700000000')
        self.assertEqual(self.client.patch('/api/profiles/me/', {'skill_names': []}, format='json').data['skills'], [])

    def test_other_profile_and_read_only_email_are_preserved(self):
        other = get_user_model().objects.create_user(email='other-cv@example.com', password='test-password')
        self.client.patch('/api/profiles/me/', {'full_name': 'Owner', 'email': other.email}, format='json')
        other.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(other.full_name, '')
        self.assertEqual(self.user.email, 'cv@example.com')

    def test_allowed_uploads_and_private_download(self):
        for extension in ['pdf', 'doc', 'docx', 'PDF']:
            content = {'pdf': pdf_bytes, 'doc': doc_bytes, 'docx': docx_bytes}[extension.lower()]()
            with self.subTest(extension=extension):
                response = self.client.patch('/api/profiles/me/', {'cv_file': SimpleUploadedFile(f'cv.{extension}', content)}, format='multipart')
                self.assertEqual(response.status_code, 200)
                download = self.client.get('/api/profiles/me/cv/')
                self.assertEqual(download.status_code, 200)
                self.assertEqual(b''.join(download.streaming_content), content)
                self.assertIn('no-store', download['Cache-Control'])
                download.close()

    def test_invalid_type_and_size_preserve_existing_cv(self):
        self.client.patch('/api/profiles/me/', {'cv_file': SimpleUploadedFile('good.pdf', pdf_bytes())}, format='multipart')
        self.user.profile.refresh_from_db()
        original = self.user.profile.cv_file.name
        for name, content in [('bad.txt', b'bad'), ('large.pdf', b'x' * (5 * 1024 * 1024 + 1)), ('empty.pdf', b'')]:
            response = self.client.patch('/api/profiles/me/', {'cv_file': SimpleUploadedFile(name, content)}, format='multipart')
            self.assertEqual(response.status_code, 400)
            self.assertIn('cv_file', response.data)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.cv_file.name, original)

    def test_five_mb_boundary_is_accepted(self):
        file = SimpleUploadedFile('boundary.pdf', pdf_bytes(5 * 1024 * 1024))
        self.assertEqual(self.client.patch('/api/profiles/me/', {'cv_file': file}, format='multipart').status_code, 200)

    def test_validation_of_contact_and_experience(self):
        response = self.client.patch('/api/profiles/me/', {'full_name': 'x' * 256, 'phone_number': 'x' * 21, 'years_of_experience': -1, 'skill_names': ['  ']}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data), {'full_name', 'phone_number', 'years_of_experience', 'skill_names'})

    def test_uploaded_cv_missing_and_authentication(self):
        self.assertEqual(self.client.get('/api/profiles/me/cv/').status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/profiles/me/cv/').status_code, 401)
        self.assertEqual(self.client.get('/api/profiles/me/generate-cv/').status_code, 401)

    def test_generated_documents_are_docx(self):
        job = Job.objects.create(title='Developer', company_name='Example', description='Build', source_url='https://example.com/cv', source_name='test')
        for url in ['/api/profiles/me/generate-cv/', f'/api/jobs/{job.pk}/generate-cover-letter/']:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content.startswith(b'PK'))
            self.assertIn('attachment', response['Content-Disposition'])
            self.assertIn('no-store', response['Cache-Control'])

    def test_application_document_download_keeps_owner_snapshot(self):
        job = Job.objects.create(title='Developer', company_name='Example', description='Build', source_url='https://example.com/snapshot', source_name='test')
        app = Application.objects.create(user=self.user, job=job, application_method='external_link', generated_cv='snapshots/cv.docx', generated_cover_letter='snapshots/letter.docx')
        target = Path(self.tmp.name) / 'snapshots'
        target.mkdir()
        (target / 'cv.docx').write_bytes(b'original-cv')
        (target / 'letter.docx').write_bytes(b'original-letter')
        self.user.full_name = 'Updated name'
        self.user.save()
        for kind, expected in [('cv', b'original-cv'), ('cover-letter', b'original-letter')]:
            response = self.client.get(f'/api/jobs/applications/{app.pk}/documents/{kind}/')
            self.assertEqual(b''.join(response.streaming_content), expected)
            response.close()
        self.assertEqual(self.client.get(f'/api/jobs/applications/{app.pk}/documents/unknown/').status_code, 404)
        other = get_user_model().objects.create_user(email='document-other@example.com', password='test-password')
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(f'/api/jobs/applications/{app.pk}/documents/cv/').status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f'/api/jobs/applications/{app.pk}/documents/cv/').status_code, 401)
