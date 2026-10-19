"""The public account-to-CV journey, with no production data or real email."""
from io import BytesIO
from pathlib import Path
import tempfile
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch
import uuid

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import caches
from django.test import TransactionTestCase, override_settings
from docx import Document
from rest_framework.test import APIClient

from jobs.models import Application, DeliveryAttempt, Job
from .models import CVApproval, CVWorkspace


@override_settings(ALLOWED_HOSTS=['testserver'], ACCOUNT_LINK_ORIGIN='https://testserver',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    ACCOUNT_EMAIL_TEST_CAPTURE=True, REAL_EMAIL_ENABLED=False, REFRESH_COOKIE_SECURE=True)
class RegistrationCVJourneyTests(TransactionTestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        settings = override_settings(MEDIA_ROOT=self.media.name)
        settings.enable()
        self.addCleanup(settings.disable)
        for cache in caches.all():
            cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        self.access = None
        mail.get_connection()

    def csrf(self):
        response = self.client.get('/api/accounts/csrf/', secure=True)
        self.assertEqual(response.status_code, 200)
        headers = {'HTTP_ORIGIN': 'https://testserver', 'HTTP_X_CSRFTOKEN': response.data['csrfToken']}
        if self.access:
            headers['HTTP_AUTHORIZATION'] = 'Bearer ' + self.access
        self.client.credentials(**headers)

    def test_register_verify_build_approve_download_prepare_and_review_without_sending(self):
        # Use actual endpoints/JWT/CSRF rather than force_authenticate or ORM account setup.
        self.assertEqual(self.client.get('/api/profiles/me/', secure=True).status_code, 401)
        self.csrf()
        account = {'email': 'journey@example.invalid', 'full_name': 'Synthetic Applicant',
                   'password': 'Forest!River-82-Clouds', 'phone_number': '0700000000'}
        weak = self.client.post('/api/accounts/register/', {**account, 'password': '123'}, format='json', secure=True)
        self.assertEqual(weak.status_code, 400)
        self.assertIn('password', weak.data)
        self.assertFalse(get_user_model().objects.exists())
        registered = self.client.post('/api/accounts/register/', account, format='json', secure=True)
        self.assertEqual(registered.status_code, 201)
        self.assertNotIn('password', registered.data)
        self.assertFalse(mail.outbox)
        login = self.client.post('/api/accounts/login/', account, format='json', secure=True)
        self.assertEqual(login.status_code, 200)
        self.assertEqual(set(login.data), {'access'})
        self.assertTrue(login.cookies['refresh_token']['httponly'])
        self.access = login.data['access']
        self.csrf()  # Login rotates the CSRF secret, just as the browser client handles.
        self.assertFalse(self.client.get('/api/accounts/verification/status/', secure=True).data['verified'])
        requested = self.client.post('/api/accounts/verification/request/',
            {'request_id': str(uuid.uuid4())}, format='json', secure=True)
        self.assertEqual(requested.status_code, 202)
        self.assertTrue(requested.data['delivery_available'])
        self.assertEqual(len(mail.outbox), 1)
        token = parse_qs(urlsplit(mail.outbox[0].body.split()[-1]).fragment)['token'][0]
        confirmed = self.client.post('/api/accounts/verification/confirm/', {'token': token}, format='json', secure=True)
        self.assertEqual(confirmed.status_code, 200)
        self.assertTrue(self.client.get('/api/accounts/verification/status/', secure=True).data['verified'])
        # Building a CV requires no uploaded CV, job selection or application.
        profile = self.client.patch('/api/profiles/me/', {'headline': 'Software developer',
            'bio': 'Builds reliable tools.', 'location': 'Nairobi', 'skill_names': ['Python', 'Testing'],
            'notify_email': False, 'notify_in_app': False},
            format='json', secure=True)
        self.assertEqual(profile.status_code, 200)
        self.assertFalse(profile.data['notify_email'])
        self.assertIsNone(profile.data['cv_file'])
        self.assertEqual(self.client.get('/api/profiles/me/cv-draft/', secure=True).data, {'content': None})
        self.assertFalse(CVWorkspace.objects.exists())
        started = self.client.post('/api/profiles/me/cv-draft/', {}, format='json', secure=True)
        self.assertEqual(started.status_code, 200)
        self.assertEqual(started.data['content']['contact']['name'], account['full_name'])
        self.assertEqual(started.data['content']['summary'], 'Builds reliable tools.')
        self.assertCountEqual(started.data['content']['skills'], ['Python', 'Testing'])
        bad = self.client.patch('/api/profiles/me/cv-draft/', {'expected_revision': 1,
            'content': {'employment': [{'title': '', 'organisation': ''}]}}, format='json', secure=True)
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(CVWorkspace.objects.get().revision, 1)
        saved = self.client.patch('/api/profiles/me/cv-draft/', {'expected_revision': 1, 'content': {
            'employment': [{'title': 'Developer', 'organisation': 'Synthetic Team', 'start': '2024-01',
                            'current': True, 'achievements': ['Shipped a tested tool.']}],
            'education': [{'qualification': 'Computing', 'institution': 'Synthetic College', 'end': '2023-12'}],
            'certifications': [{'name': 'Test certificate', 'issuer': 'Synthetic Institute'}],
            'projects': [{'name': 'Demo project', 'url': 'https://example.invalid/project'}],
        }}, format='json', secure=True)
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.data['revision'], 2)
        self.assertEqual(self.client.get('/api/profiles/me/generate-cv/', secure=True).status_code, 409)
        approval = {'expected_revision': 2, 'content_sha256': saved.data['content_sha256'], 'approval': True}
        self.assertEqual(self.client.post('/api/profiles/me/cv-draft/approve/',
            {**approval, 'approval': False}, format='json', secure=True).status_code, 400)
        self.assertFalse(CVApproval.objects.exists())
        approved = self.client.post('/api/profiles/me/cv-draft/approve/', approval, format='json', secure=True)
        self.assertEqual(approved.status_code, 200)
        url = f"/api/profiles/me/cv-versions/{approved.data['approval_id']}/download/"
        download = self.client.get(url, secure=True)
        self.assertEqual(download.status_code, 200)
        self.assertIn('private, no-store', download['Cache-Control'])
        self.assertIn('attachment;', download['Content-Disposition'])
        snapshot = CVApproval.objects.get()
        self.assertEqual(download.content, Path(snapshot.document.path).read_bytes())
        text = ' '.join(' '.join(p.text for p in Document(BytesIO(download.content)).paragraphs).split())
        preview = saved.data['preview']
        expected = [preview['name'], preview['headline'], preview['contact']]
        for section in preview['sections']:
            expected.append(section['title'])
            for entry in section['entries']:
                expected.extend([entry['heading'], *entry['paragraphs'], *entry['bullets']])
        self.assertEqual(text, ' '.join(' '.join(expected).split()))
        # A fresh JWT after cookie refresh still downloads the exact approved bytes.
        self.access = None
        self.csrf()
        refreshed = self.client.post('/api/accounts/refresh/', {}, format='json', secure=True)
        self.assertEqual(refreshed.status_code, 200)
        self.access = refreshed.data['access']
        self.csrf()
        self.assertEqual(self.client.get(url, secure=True).content, download.content)
        self.assertFalse(Application.objects.exists())
        self.assertEqual(list(DeliveryAttempt.objects.values_list('channel', flat=True)), ['email_verification'])
        self.assertEqual(len(mail.outbox), 1)
        versions = self.client.get('/api/profiles/me/cv-versions/', secure=True)
        self.assertEqual(str(versions.data['approval_id']), str(snapshot.pk))
        job = Job.objects.create(title='Synthetic Developer', company_name='Synthetic Company',
            description='Synthetic role', source_name='journey', source_url='https://example.invalid/journey',
            application_method=Job.ApplicationMethod.EMAIL, application_email='employer@example.invalid')
        mail.outbox.clear()
        ledger_before = list(DeliveryAttempt.objects.order_by('pk').values())
        # Preparation and review are read/draft operations, not authorization to send.
        # see docs/CONCEPTS.md#acceptance-journey
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider, patch('django.core.mail.EmailMessage.send') as send:
            prepared = self.client.post(f'/api/jobs/{job.pk}/apply/',
                {'cv_version': str(snapshot.pk)}, format='json', secure=True)
            self.assertEqual(prepared.status_code, 201)
            application = Application.objects.get()
            review = self.client.get('/api/jobs/applications/', secure=True)
            self.assertEqual(review.status_code, 200)
            self.assertEqual(review.data['results'][0]['status'], 'ready_for_review')
            document_url = f'/api/jobs/applications/{application.pk}/documents/cv/'
            document = self.client.get(document_url, secure=True)
            self.assertEqual(b''.join(document.streaming_content), download.content)
            self.assertIn('no-store', document['Cache-Control'])
            self.client.patch('/api/profiles/me/', {'headline': 'Later profile edit'}, format='json', secure=True)
            repeated = self.client.get(document_url, secure=True)
            self.assertEqual(b''.join(repeated.streaming_content), download.content)
            intruder = get_user_model().objects.create_user(email='intruder@example.invalid', password='test-only')
            other = APIClient()
            other.force_authenticate(intruder)
            self.assertEqual(other.get(document_url, secure=True).status_code, 404)
            self.assertEqual(other.get(url, secure=True).status_code, 404)
            provider.assert_not_called()
            send.assert_not_called()
        self.assertEqual(mail.outbox, [])
        self.assertEqual(list(DeliveryAttempt.objects.order_by('pk').values()), ledger_before)
        application.refresh_from_db()
        self.assertIsNone(application.sent_at)
        self.assertEqual(self.client.post('/api/accounts/logout/', {}, format='json', secure=True).status_code, 200)
        self.client.credentials()
        self.assertEqual(self.client.get(url, secure=True).status_code, 401)
