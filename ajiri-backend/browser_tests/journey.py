"""Real Chromium + built React + HTTP/JWT/CSRF against a disposable Django DB.

No production URL, provider credential, public inbox or test-only HTTP endpoint.
see docs/CONCEPTS.md#browser-acceptance
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.cache import caches
from django.test import LiveServerTestCase, override_settings
from playwright.sync_api import sync_playwright, expect

from jobs.models import Application, DeliveryAttempt, DeliveryDailyBudget, Job
from profiles.models import CVApproval


@override_settings(DEBUG=False, ALLOWED_HOSTS=['localhost', '127.0.0.1'],
    SECURE_SSL_REDIRECT=False, SECURE_HSTS_SECONDS=0, REFRESH_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False, SESSION_COOKIE_SECURE=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    ACCOUNT_EMAIL_TEST_CAPTURE=True, REAL_EMAIL_ENABLED=False, ALERT_EMAIL_ENABLED=False,
    BREVO_API_KEY='', INGEST_API_KEY='')
class BrowserJourney(LiveServerTestCase):
    host = '127.0.0.1'

    def setUp(self):
        self.assertTrue((settings.FRONTEND_BUILD_DIR / 'index.html').is_file(),
            'Build the React client before running browser acceptance.')
        self.private = tempfile.TemporaryDirectory(prefix='ajiri-browser-')
        self.addCleanup(self.private.cleanup)
        self.isolation = override_settings(MEDIA_ROOT=self.private.name,
            CSRF_TRUSTED_ORIGINS=[self.live_server_url])
        self.isolation.enable()
        self.addCleanup(self.isolation.disable)
        for cache in caches.all():
            cache.clear()
        mail.get_connection()
        self.job = Job.objects.create(title='Synthetic browser developer', company_name='Synthetic team',
            description='Synthetic test vacancy. No employer contact.', source_name='browser-test',
            source_url='https://example.invalid/browser-test', application_method='email',
            application_email='synthetic-employer@example.invalid')

    def test_register_cv_approve_prepare_review_never_sends(self):
        # Playwright's sync event loop lives in a worker: ORM stays on Django's
        # thread, without globally disabling Django's async safety protection.
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            with ThreadPoolExecutor(max_workers=1) as worker:
                worker.submit(self.browser_journey).result(timeout=120)
            provider.assert_not_called()
        approval = CVApproval.objects.get()
        application = Application.objects.get()
        self.assertEqual(Path(approval.document.path).read_bytes(), self.cv_bytes)
        self.assertEqual(Path(application.generated_cv.path).read_bytes(), self.cv_bytes)
        self.assertIsNone(application.sent_at)
        self.assertEqual(DeliveryAttempt.objects.count(), 0)
        self.assertEqual(DeliveryDailyBudget.objects.count(), 0)
        self.assertEqual(mail.outbox, [])

    def browser_journey(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True)
            # Fail closed on any external browser request; fixture source links
            # are not followed. API traffic is real and is never mocked.
            context.route('**/*', lambda route: route.continue_()
                if route.request.url.startswith(self.live_server_url + '/') else route.abort())
            page = context.new_page()
            failures = []
            page.on('pageerror', lambda error: failures.append(str(error)))
            page.goto(self.live_server_url + '/register')
            page.get_by_label('Full name', exact=True).fill('Synthetic Browser Applicant')
            page.get_by_label('Email', exact=True).fill('browser@example.invalid')
            page.get_by_label('Password', exact=True).fill('Synthetic!Forest-82-Clouds')
            page.locator('[name=privacy_consent]').check()
            page.get_by_role('button', name='Register', exact=True).click()
            expect(page.get_by_text('Account created. Log in to continue.')).to_be_visible()
            page.get_by_label('Email address', exact=True).fill('browser@example.invalid')
            page.get_by_label('Password', exact=True).fill('Synthetic!Forest-82-Clouds')
            page.get_by_role('button', name='Log in', exact=True).click()
            expect(page.get_by_role('heading', name='Find your next chapter.')).to_be_visible()
            page.goto(self.live_server_url + '/profile')
            page.get_by_label('Professional headline', exact=True).fill('Synthetic developer')
            page.get_by_label('Skills (comma separated)', exact=True).fill('Python, Testing')
            page.get_by_label('About you', exact=True).fill('Builds tested synthetic tools.')
            page.get_by_role('button', name='Save profile', exact=True).click()
            expect(page.get_by_text('Profile saved.', exact=True)).to_be_visible()
            page.goto(self.live_server_url + '/cv-builder')
            page.get_by_role('button', name='Start my CV', exact=True).click()
            page.get_by_role('button', name='Save and preview CV', exact=True).click()
            expect(page.get_by_role('article', name='Saved CV preview')).to_contain_text('Synthetic Browser Applicant')
            approve = page.get_by_role('button', name='Approve this CV version', exact=True)
            expect(approve).to_be_disabled()
            page.get_by_label('I have reviewed this CV and approve this version.').check()
            approve.click()
            with page.expect_download() as downloaded:
                page.get_by_role('button', name='Download approved CV (revision 1)', exact=True).click()
            self.cv_bytes = Path(downloaded.value.path()).read_bytes()
            page.goto(self.live_server_url + f'/jobs/{self.job.pk}')
            prepare = page.get_by_role('button', name='Prepare application', exact=True)
            expect(prepare).to_be_disabled()
            page.get_by_label('Approved CV version', exact=True).select_option(label='Revision 1 (current)')
            with page.expect_response(lambda response: response.url ==
                    self.live_server_url + f'/api/jobs/{self.job.pk}/apply/'
                    and response.request.method == 'POST') as prepared:
                prepare.click()
            assert prepared.value.status == 201
            application_id = prepared.value.json()['id']
            expect(page.get_by_role('heading', name='My applications', exact=True)).to_be_visible()
            page.get_by_text('Review application', exact=True).click()
            with page.expect_download() as application_download:
                page.get_by_role('button', name='Download CV', exact=True).click()
            assert Path(application_download.value.path()).read_bytes() == self.cv_bytes
            expect(page.get_by_text('Ready for review', exact=True)).to_be_visible()
            # A separate logged-out context must not fetch the private original.
            guest = browser.new_context()
            denied = guest.request.get(self.live_server_url + f'/api/jobs/applications/{application_id}/documents/cv/')
            assert denied.status == 401, 'Anonymous document access must be denied.'
            guest.close()
            assert not failures, 'Browser JavaScript errors occurred.'
            context.close()
            browser.close()
