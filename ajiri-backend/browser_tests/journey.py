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
from .accessibility import audit


class WorkerRollbackFixture:
    """Local-only static response swap simulates a reloaded rollback deployment."""
    retirement = None

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/sw.js' and self.retirement is not None:
            from django.http import HttpResponse
            response = HttpResponse(self.retirement, content_type='application/javascript')
            response['Cache-Control'] = 'no-store'
            return response
        return self.get_response(request)


@override_settings(MIDDLEWARE=['browser_tests.journey.WorkerRollbackFixture', *settings.MIDDLEWARE],
    DEBUG=False, ALLOWED_HOSTS=['localhost', '127.0.0.1'],
    SECURE_SSL_REDIRECT=False, SECURE_HSTS_SECONDS=0, REFRESH_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False, SESSION_COOKIE_SECURE=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    ACCOUNT_EMAIL_TEST_CAPTURE=True, REAL_EMAIL_ENABLED=False, ALERT_EMAIL_ENABLED=False,
    BREVO_API_KEY='', INGEST_API_KEY='')
class BrowserJourney(LiveServerTestCase):
    host = '127.0.0.1'

    def setUp(self):
        WorkerRollbackFixture.retirement = None
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
            context = browser.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True, color_scheme='light')
            # Fail closed on any external browser request; fixture source links
            # are not followed. API traffic is real and is never mocked.
            context.route('**/*', lambda route: route.continue_()
                if route.request.url.startswith(self.live_server_url + '/') else route.abort())
            page = context.new_page()
            failures = []
            page.on('pageerror', lambda error: failures.append(str(error)))
            page.goto(self.live_server_url + '/register')
            expect(page.get_by_role('button', name='Register', exact=True)).to_be_visible()
            audit(self, page, 'register-light')
            page.get_by_label('Full name', exact=True).fill('Synthetic Browser Applicant')
            page.get_by_label('Email', exact=True).fill('browser@example.invalid')
            page.get_by_label('Password', exact=True).fill('Synthetic!Forest-82-Clouds')
            page.locator('[name=privacy_consent]').check()
            page.get_by_role('button', name='Register', exact=True).click()
            expect(page.get_by_text('Account created. Log in to continue.')).to_be_visible()
            audit(self, page, 'login-light')
            page.get_by_label('Email address', exact=True).fill('browser@example.invalid')
            page.get_by_label('Password', exact=True).fill('Synthetic!Forest-82-Clouds')
            page.get_by_role('button', name='Log in', exact=True).click()
            expect(page.get_by_role('heading', name='Find your next chapter.')).to_be_visible()
            audit(self, page, 'jobs-light')
            page.goto(self.live_server_url + '/profile')
            page.get_by_label('Professional headline', exact=True).fill('Synthetic developer')
            page.get_by_label('Skills (comma separated)', exact=True).fill('Python, Testing')
            page.get_by_label('About you', exact=True).fill('Builds tested synthetic tools.')
            page.get_by_role('button', name='Save profile', exact=True).click()
            expect(page.get_by_text('Profile saved.', exact=True)).to_be_visible()
            audit(self, page, 'profile-light')
            page.goto(self.live_server_url + '/cv-builder')
            page.get_by_role('button', name='Start my CV', exact=True).click()
            page.get_by_role('button', name='Save and preview CV', exact=True).click()
            expect(page.get_by_role('article', name='Saved CV preview')).to_contain_text('Synthetic Browser Applicant')
            audit(self, page, 'cv-preview-light')
            approve = page.get_by_role('button', name='Approve this CV version', exact=True)
            expect(approve).to_be_disabled()
            page.get_by_label('I have reviewed this CV and approve this version.').check()
            approve.click()
            with page.expect_download() as downloaded:
                page.get_by_role('button', name='Download approved CV (revision 1)', exact=True).click()
            self.cv_bytes = Path(downloaded.value.path()).read_bytes()
            page.goto(self.live_server_url + f'/jobs/{self.job.pk}')
            prepare = page.get_by_role('button', name='Prepare application', exact=True)
            selection = page.get_by_label('Approved CV version', exact=True)
            # Current approved CV is displayed by default. Clearing it must
            # disable preparation; no request is made until explicit submission.
            selection.select_option('')
            expect(prepare).to_be_disabled()
            selection.select_option(label='Revision 1 (current)')
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
            audit(self, page, 'application-review-light')
            # A separate logged-out context must not fetch the private original.
            guest = browser.new_context()
            denied = guest.request.get(self.live_server_url + f'/api/jobs/applications/{application_id}/documents/cv/')
            assert denied.status == 401, 'Anonymous document access must be denied.'
            guest.close()
            assert not failures, 'Browser JavaScript errors occurred.'
            context.close()
            browser.close()

    def test_public_accessibility_light_and_dark(self):
        def check():
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    for theme in ('light', 'dark'):
                        context = browser.new_context(viewport={'width': 390, 'height': 844}, color_scheme=theme)
                        context.route('**/*', lambda route: route.continue_()
                            if route.request.url.startswith(self.live_server_url + '/') else route.abort())
                        page = context.new_page()
                        for route in ('register', 'login', 'privacy', 'forgot-password'):
                            page.goto(self.live_server_url + '/' + route)
                            expect(page.get_by_role('heading').first).to_be_visible()
                            expect(page.locator('html')).to_have_attribute('data-theme', theme)
                            audit(self, page, route + '-' + theme)
                        context.close()
                finally:
                    browser.close()
        with ThreadPoolExecutor(max_workers=1) as worker:
            worker.submit(check).result(timeout=120)

    def test_pwa_installability_offline_fallback_and_private_cache_exclusion(self):
        from accounts.models import User
        from rest_framework_simplejwt.tokens import RefreshToken
        user = User.objects.create_user(email='pwa@example.invalid', full_name='Synthetic Private PWA Owner')
        access = str(RefreshToken.for_user(user).access_token)
        with ThreadPoolExecutor(max_workers=1) as worker:
            worker.submit(self.pwa_journey, access).result(timeout=120)

    def pwa_journey(self, access):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(viewport={'width': 390, 'height': 844})
            page = context.new_page()
            page.goto(self.live_server_url + '/login')
            expect(page.get_by_role('button', name='Log in', exact=True)).to_be_visible()
            page.evaluate("""async () => {
                await navigator.serviceWorker.ready;
                if (!navigator.serviceWorker.controller) await new Promise(resolve =>
                    navigator.serviceWorker.addEventListener('controllerchange', resolve, {once:true}));
            }""")
            session = context.new_cdp_session(page)
            installability = session.send('Page.getInstallabilityErrors')
            self.assertEqual(installability['installabilityErrors'], [])
            manifest = page.evaluate("async () => (await fetch('/manifest.webmanifest')).json()")
            self.assertEqual(manifest['display'], 'standalone')
            self.assertEqual(manifest['start_url'], '/login')
            for size in (192, 512):
                actual = page.evaluate("""async size => {
                    const image = new Image(); image.src = `/icons/icon-${size}.png`;
                    await image.decode(); return [image.naturalWidth, image.naturalHeight];
                }""", size)
                self.assertEqual(actual, [size, size])
            profile = page.evaluate("""async access => {
                const response = await fetch('/api/profiles/me/', {headers:{Authorization:`Bearer ${access}`}});
                return {status:response.status, body:await response.json()};
            }""", access)
            self.assertEqual(profile['status'], 200)
            self.assertEqual(profile['body']['full_name'], 'Synthetic Private PWA Owner')
            cached = page.evaluate("""async () => {
                const result = [];
                for (const key of await caches.keys()) {
                    for (const request of await (await caches.open(key)).keys()) result.push(new URL(request.url).pathname);
                } return result.sort();
            }""")
            self.assertEqual(cached, ['/icons/icon-192.png', '/icons/icon-512.png', '/manifest.webmanifest', '/offline.html'])
            context.set_offline(True)
            api_result = page.evaluate("async () => { try { return (await fetch('/api/profiles/me/')).status; } catch { return 'unavailable'; } }")
            self.assertEqual(api_result, 'unavailable')
            page.goto(self.live_server_url + '/profile')
            expect(page.get_by_role('heading', name="You're offline")).to_be_visible()
            expect(page.get_by_text('Synthetic Private PWA Owner')).to_have_count(0)
            audit(self, page, 'pwa-offline')
            context.set_offline(False)
            page.get_by_role('link', name='Try Ajiri again').click()
            expect(page.get_by_role('button', name='Log in', exact=True)).to_be_visible()
            page.wait_for_load_state('load')
            page.evaluate("async () => { await navigator.serviceWorker.register('/sw.js', {scope:'/', updateViaCache:'none'}); }")
            # Swap the same URL for every browser update request, as after reload.
            # Playwright routing alone misses browser-internal worker soft updates.
            WorkerRollbackFixture.retirement = (settings.FRONTEND_BUILD_DIR / 'sw-retire.js').read_bytes()
            page.evaluate("async () => { await caches.open('unrelated-cache'); const registration = await navigator.serviceWorker.getRegistration('/'); await registration.update(); }")
            # Await asynchronous browser state explicitly; a promise itself is
            # truthy to wait_for_function and must not stand in for its verdict.
            retired = page.evaluate("""async () => {
                const deadline = performance.now() + 10000;
                while (performance.now() < deadline) {
                    const registrations = await navigator.serviceWorker.getRegistrations();
                    const keys = await caches.keys();
                    if (!registrations.length && !keys.some(key => key.startsWith('ajiri-public-'))) return keys.sort();
                    await new Promise(resolve => setTimeout(resolve, 25));
                }
                return {registrations: (await navigator.serviceWorker.getRegistrations()).length, caches: await caches.keys()};
            }""")
            self.assertEqual(retired, ['unrelated-cache'])
            browser.close()
