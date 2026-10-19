from pathlib import Path
import tempfile
from urllib.parse import unquote
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient
from jobs.models import Application, Job
from .cv_test_helpers import approved_cv
from .download_names import document_name, name_part
from .upload_fixtures import pdf_bytes


class DownloadNameTests(SimpleTestCase):
    def test_all_name_parts_company_last_and_safe_fallbacks(self):
        self.assertEqual(document_name('First Middle Last', company='Example Company'),
                         'First_Middle_Last_CV_Example_Company.docx')
        self.assertEqual(document_name('', 'Cover_Letter', ''), 'Applicant_Cover_Letter_Company.docx')
        self.assertEqual(document_name('Cher'), 'Cher_CV.docx')
        self.assertEqual(name_part('CON', 'Applicant'), 'CON_')
        self.assertEqual(len(name_part('x' * 200, 'Applicant')), 60)

    def test_unicode_controls_traversal_and_header_characters(self):
        result = document_name('  Zoë / .. \\ " < > | ? * :\r\n\x00\u202e  Name ', company='Unsafe/Company')
        self.assertTrue(result.endswith('_CV_UnsafeCompany.docx'))
        self.assertIn('Zoë', result)
        self.assertFalse(any(c in result for c in '/\\"<>|?*:\r\n\x00\u202e. ' if c != '.'))
        self.assertEqual(result.count('.'), 1)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DownloadHeadersTests(TestCase):
    def test_readable_headers_without_changing_storage_or_bytes(self):
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            user = get_user_model().objects.create_user(email='names@example.invalid', password='test-only', full_name='Current Account Name')
            approval = approved_cv(user)
            client = APIClient()
            client.force_authenticate(user)
            original = Path(approval.document.path).read_bytes()
            personal = client.get(f'/api/profiles/me/cv-versions/{approval.pk}/download/')
            self.assertIn('Test_Applicant_CV.docx', personal['Content-Disposition'])
            self.assertEqual(personal.content, original)
            job = Job.objects.create(title='Synthetic role', company_name='Example Company', description='Synthetic',
                source_name='test', source_url='https://example.invalid/download-names')
            self.assertEqual(client.post(f'/api/jobs/{job.pk}/apply/', {'cv_version': str(approval.pk)}, format='json').status_code, 201)
            application = Application.objects.get()
            names = (application.generated_cv.name, application.generated_cover_letter.name)
            for kind, label in [('cv', 'CV'), ('cover-letter', 'Cover_Letter')]:
                response = client.get(f'/api/jobs/applications/{application.pk}/documents/{kind}/')
                self.assertIn(f'Current_Account_Name_{label}_Example_Company.docx', response['Content-Disposition'])
                self.assertNotIn(Path(names[0]).stem, response['Content-Disposition'])
                data = b''.join(response.streaming_content)
                if kind == 'cv':
                    self.assertEqual(data, original)
            letter = client.get(f'/api/jobs/{job.pk}/generate-cover-letter/')
            self.assertIn('Current_Account_Name_Cover_Letter_Example_Company.docx', letter['Content-Disposition'])
            user.full_name = 'Zoë Name'
            user.save()
            renamed = client.get(f'/api/jobs/applications/{application.pk}/documents/cv/')
            self.assertIn('Zoë_Name_CV_Example_Company.docx', unquote(renamed['Content-Disposition']))
            self.assertEqual(b''.join(renamed.streaming_content), original)
            application.refresh_from_db()
            self.assertEqual((application.generated_cv.name, application.generated_cover_letter.name), names)
            uploaded = client.patch('/api/profiles/me/', {'cv_file': SimpleUploadedFile('original.pdf', pdf_bytes())}, format='multipart')
            self.assertEqual(uploaded.status_code, 200)
            uploaded = client.get('/api/profiles/me/cv/')
            self.assertIn('Uploaded_CV.pdf', uploaded['Content-Disposition'])
            self.assertEqual(b''.join(uploaded.streaming_content), pdf_bytes())
