"""Real Chromium + built React + HTTP/JWT/CSRF against a disposable Django DB.

No production URL, provider credential, public inbox or test-only HTTP endpoint.
see docs/CONCEPTS.md#browser-acceptance
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import logging
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
    server_failures = []

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/sw.js' and self.retirement is not None:
            from django.http import HttpResponse
            response = HttpResponse(self.retirement, content_type='application/javascript')
            response['Cache-Control'] = 'no-store'
            return response
        return self.get_response(request)

    def process_exception(self, request, exception):
        self.capture_exception(exception)

    @staticmethod
    def capture_exception(exception):
        # Synthetic test diagnostics only: no message, URL, query or user data.
        allowed = {'OperationalError', 'IntegrityError', 'DatabaseError', 'ValueError',
                   'AttributeError', 'RuntimeError', 'KeyError', 'RelatedObjectDoesNotExist'}
        kind = type(exception).__name__
        frames = []
        trace = exception.__traceback__
        while trace:
            file = Path(trace.tb_frame.f_code.co_filename)
            if file.is_relative_to(settings.BASE_DIR):
                frames.append({'file': file.relative_to(settings.BASE_DIR).as_posix(), 'line': trace.tb_lineno})
            trace = trace.tb_next
        data = {
            'exception_type': kind if kind in allowed else 'other',
            'sqlite_code': getattr(exception.__cause__, 'sqlite_errorcode', None),
            'frames': frames[-3:],
        }
        if type(data['sqlite_code']) is not int:
            data['sqlite_code'] = None
        if data not in WorkerRollbackFixture.server_failures:
            WorkerRollbackFixture.server_failures.append(data)
            print('Synthetic server exception:', data)


class SyntheticExceptionHandler(logging.Handler):
    def emit(self, record):
        if record.exc_info and record.exc_info[1]:
            WorkerRollbackFixture.capture_exception(record.exc_info[1])


@override_settings(MIDDLEWARE=['browser_tests.journey.WorkerRollbackFixture', *settings.MIDDLEWARE],
    DEBUG=False, ALLOWED_HOSTS=['localhost', '127.0.0.1'],
    SECURE_SSL_REDIRECT=False, SECURE_HSTS_SECONDS=0, REFRESH_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False, SESSION_COOKIE_SECURE=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    ACCOUNT_EMAIL_TEST_CAPTURE=True, REAL_EMAIL_ENABLED=False, ALERT_EMAIL_ENABLED=False,
    BREVO_API_KEY='', INGEST_API_KEY='', JOB_FRESHNESS_ENFORCED=True)
class BrowserJourney(LiveServerTestCase):
    host = '127.0.0.1'

    def setUp(self):
        from django.db import connection
        if connection.vendor == "sqlite":
            self.assertFalse(connection.is_in_memory_db(), "Browser HTTP tests require a disposable file database.")
        WorkerRollbackFixture.retirement = None
        WorkerRollbackFixture.server_failures = []
        handler = SyntheticExceptionHandler()
        logger = logging.getLogger('django.request')
        logger.addHandler(handler)
        self.addCleanup(logger.removeHandler, handler)
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
        from jobs.models import JobPublication
        from django.utils import timezone
        from datetime import timedelta
        JobPublication.objects.create(job=self.job, origin='rss', status='published',
            closes_at=timezone.now()+timedelta(days=2), confirmed_at=timezone.now())

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

    @override_settings(JOB_FRESHNESS_ENFORCED=True, EMPLOYER_POSTING_ENABLED=True, PUBLIC_JOB_ORIGIN='https://example.invalid')
    def test_employer_submission_staff_review_and_withdrawal(self):
        from accounts.models import User
        from jobs.models import EmployerJobDraft
        from django.utils import timezone
        owner = User.objects.create_user(email='employer-browser@example.invalid', password='Synthetic-Employer-982!')
        owner.profile.email_verified_at = timezone.now()
        owner.profile.verified_email = owner.email
        owner.profile.save()
        User.objects.create_user(email='reviewer-browser@example.invalid', password='Synthetic-Reviewer-982!', is_staff=True)
        def journey():
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                failures = []
                def login(email, password):
                    context = browser.new_context(viewport={'width':390,'height':844})
                    context.on('response', lambda response: failures.append(response.status) if response.status >= 500 else None)
                    context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(self.live_server_url+'/') else route.abort())
                    page = context.new_page()
                    page.goto(self.live_server_url+'/login')
                    page.get_by_label('Email address', exact=True).fill(email)
                    page.get_by_label('Password', exact=True).fill(password)
                    page.get_by_role('button',name='Log in',exact=True).click()
                    page.wait_for_url(self.live_server_url+'/')
                    return context,page
                employer, page = login('employer-browser@example.invalid','Synthetic-Employer-982!')
                page.goto(self.live_server_url+'/employers')
                page.get_by_label('Organisation name',exact=True).fill('Synthetic Browser Employer')
                page.get_by_label('Official website',exact=True).fill('https://example.invalid')
                page.get_by_role('button',name='Submit organisation for review',exact=True).click()
                expect(page.get_by_text('Synthetic Browser Employer: pending',exact=True)).to_be_visible()
                page.get_by_label('Job title',exact=True).fill('Synthetic reviewed opportunity')
                page.get_by_label('Location (include country)',exact=True).fill('Nairobi, Kenya')
                page.get_by_label('Description',exact=True).fill('Synthetic detailed responsibilities and application requirements. '*8)
                page.get_by_label('Official application URL',exact=True).fill('https://example.invalid/careers/browser')
                from datetime import timedelta
                page.get_by_label('Closing date and time (your local time)',exact=True).fill((timezone.now()+timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'))
                page.get_by_role('button',name='Submit vacancy for review',exact=True).click()
                expect(page.get_by_role('heading',name='Synthetic reviewed opportunity',exact=True)).to_be_visible()
                staff, review = login('reviewer-browser@example.invalid','Synthetic-Reviewer-982!')
                review.goto(self.live_server_url+'/employers/review')
                organisation_form=review.locator('form').filter(has=review.get_by_role('heading',name='Synthetic Browser Employer',exact=True))
                organisation_form.get_by_role('combobox').select_option('approve')
                organisation_form.get_by_label('Review reason and evidence',exact=True).fill('Synthetic independent organisation verification.')
                organisation_form.get_by_role('button').click()
                expect(review.get_by_role('heading',name='Synthetic Browser Employer',exact=True)).not_to_be_visible()
                job_form=review.locator('form').filter(has=review.get_by_role('heading',name='Synthetic reviewed opportunity',exact=True))
                job_form.get_by_role('combobox').select_option('approve')
                job_form.get_by_label('Review reason and evidence',exact=True).fill('Synthetic job source, deadline and absence of applicant fees checked.')
                job_form.get_by_role('button').click()
                expect(review.get_by_role('heading',name='Synthetic reviewed opportunity',exact=True)).not_to_be_visible()
                with page.expect_response(lambda response: '/api/jobs/employers/drafts/' in response.url and response.request.method == 'GET') as own_drafts:
                    page.reload()
                expect(page.get_by_text('published',exact=False).first).to_be_visible()
                published_id = own_drafts.value.json()['results'][0]['job']
                page.goto(self.live_server_url+f'/jobs/{published_id}')
                expect(page.get_by_role('heading',name='Synthetic reviewed opportunity',exact=True)).to_be_visible()
                expect(page.get_by_role('link',name='Open employer application page (opens in a new tab)',exact=True)).to_have_attribute('href','https://example.invalid/careers/browser')
                page.goto(self.live_server_url+'/employers')
                expect(page.get_by_text('published',exact=False).first).to_be_visible()
                audit(self,page,'employer-dashboard-light')
                page.get_by_role('button',name='Withdraw Synthetic reviewed opportunity',exact=True).click()
                expect(page.get_by_text('withdrawn',exact=False).first).to_be_visible()
                page.wait_for_load_state('networkidle')
                review.wait_for_load_state('networkidle')
                assert not failures, f'Unexpected server responses: {WorkerRollbackFixture.server_failures}'
                employer.close(); staff.close(); browser.close()
        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            with ThreadPoolExecutor(max_workers=1) as worker:
                worker.submit(journey).result(timeout=120)
            provider.assert_not_called()
        draft = EmployerJobDraft.objects.get()
        self.assertEqual(draft.status, 'withdrawn')
        self.assertEqual(draft.job.publication.status, 'archived')
        self.assertEqual(mail.outbox, [])

    def test_parallel_authenticated_reads_use_independent_connections(self):
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.tokens import RefreshToken
        from urllib.request import Request, urlopen

        user = get_user_model().objects.create_user(
            email='parallel-browser@example.invalid', password='Synthetic!Read-82-Clouds')
        access = str(RefreshToken.for_user(user).access_token)

        def read(index):
            path = ['/api/profiles/me/', '/api/jobs/'][index % 2]
            request = Request(self.live_server_url + path,
                              headers={'Authorization': 'Bearer ' + access})
            with urlopen(request, timeout=20) as response:
                response.read()
                return response.status

        with ThreadPoolExecutor(max_workers=4) as workers:
            self.assertEqual(list(workers.map(read, range(48))), [200] * 48)
        self.assertEqual(WorkerRollbackFixture.server_failures, [])

    def test_private_progress_update_does_not_submit(self):
        from accounts.models import User
        user = User.objects.create_user(email='progress-browser@example.invalid', password='Synthetic-Progress-982!')
        job = Job.objects.create(title='Synthetic progress role', company_name='Synthetic company',
            source_name='synthetic', source_url='https://example.invalid/progress-browser', is_active=False)
        application = Application.objects.create(user=user, job=job, status='ready_for_review', application_method='external_link')

        def journey():
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page(viewport={'width': 390, 'height': 844})
                page.route('**/*', lambda route: route.continue_()
                    if route.request.url.startswith(self.live_server_url + '/') else route.abort())
                page.goto(self.live_server_url+'/login')
                page.get_by_label('Email address', exact=True).fill(user.email)
                page.get_by_label('Password', exact=True).fill('Synthetic-Progress-982!')
                page.get_by_role('button', name='Log in', exact=True).click()
                page.wait_for_url(self.live_server_url+'/')
                page.goto(self.live_server_url+'/applications')
                page.get_by_text('Track my progress', exact=True).click()
                page.get_by_label('Your progress', exact=True).select_option('interview')
                page.get_by_label('Private note (optional)', exact=True).fill('Synthetic personal report only')
                page.get_by_role('button', name='Save my update', exact=True).click()
                expect(page.get_by_role('status')).to_contain_text('No application was sent')
                expect(page.locator('p').filter(has_text='Interview (your report)')).to_be_visible()
                audit(self, page, 'application-progress-light')
                page.reload()
                page.get_by_text('Track my progress', exact=True).click()
                expect(page.get_by_label('Your progress', exact=True)).to_have_value('interview')
                expect(page.get_by_label('Private note (optional)', exact=True)).to_have_value('Synthetic personal report only')
                browser.close()

        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            with ThreadPoolExecutor(max_workers=1) as worker:
                worker.submit(journey).result(timeout=120)
            provider.assert_not_called()
        application.refresh_from_db()
        self.assertEqual((application.progress_stage, application.progress_revision), ('interview', 1))
        self.assertEqual(application.status, 'ready_for_review')
        self.assertIsNone(application.sent_at)
        self.assertFalse(DeliveryAttempt.objects.exists())
        self.assertFalse(DeliveryDailyBudget.objects.exists())
        self.assertEqual(mail.outbox, [])

    @override_settings(SAVED_SEARCHES_ENABLED=True)
    def test_saved_search_choices_edit_and_remove_never_send(self):
        from django.contrib.auth import get_user_model
        from jobs.models import SavedSearch
        user = get_user_model().objects.create_user(
            email='saved-browser@example.invalid', password='Synthetic-Saved-982!')

        def journey():
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                context = browser.new_context(viewport={'width': 390, 'height': 844})
                failures = []
                context.on('response', lambda response: failures.append(response.status) if response.status >= 500 else None)
                context.route('**/*', lambda route: route.continue_()
                    if route.request.url.startswith(self.live_server_url + '/') else route.abort())
                page = context.new_page()
                page.goto(self.live_server_url+'/login')
                page.get_by_label('Email address', exact=True).fill(user.email)
                page.get_by_label('Password', exact=True).fill('Synthetic-Saved-982!')
                page.get_by_role('button', name='Log in', exact=True).click()
                page.wait_for_url(self.live_server_url+'/')
                page.goto(self.live_server_url+'/saved-searches?q=Python')
                expect(page.get_by_role('heading', name='Saved searches', exact=True)).to_be_visible()
                page.get_by_label('Search name', exact=True).fill('Synthetic saved query')
                page.get_by_label('In-app frequency', exact=True).select_option('daily')
                page.get_by_label('Email frequency (sending disabled)', exact=True).select_option('weekly')
                page.get_by_role('button', name='Save search', exact=True).click()
                expect(page.get_by_role('status')).to_contain_text('does not authorize or send email')
                expect(page.get_by_role('heading', name='Synthetic saved query', exact=True)).to_be_visible()
                page.get_by_role('button', name='Edit Synthetic saved query', exact=True).click()
                page.get_by_label('Job keywords', exact=True).fill('x'*65)
                page.get_by_role('button', name='Save changes', exact=True).click()
                expect(page.get_by_role('alert')).to_contain_text('each at most 64 characters')
                page.get_by_label('Job keywords', exact=True).fill('Testing')
                page.get_by_role('button', name='Save changes', exact=True).click()
                expect(page.get_by_role('heading', name='Edit saved search', exact=True)).not_to_be_visible()
                page.get_by_role('button', name='Show matches for Synthetic saved query', exact=True).click()
                expect(page.get_by_text('No current matches yet.', exact=False)).to_be_visible()
                audit(self, page, 'saved-searches-light')
                page.get_by_role('button', name='Remove Synthetic saved query', exact=True).click()
                expect(page.get_by_role('status')).to_contain_text('future checks are stopped')
                expect(page.get_by_text('No saved searches yet.', exact=True)).to_be_visible()
                page.wait_for_load_state('networkidle')
                self.assertEqual(failures, [], WorkerRollbackFixture.server_failures)
                context.close()
                browser.close()

        with patch('jobs.brevo_transport.BrevoTransport.send') as provider:
            with ThreadPoolExecutor(max_workers=1) as worker:
                worker.submit(journey).result(timeout=120)
            provider.assert_not_called()
        self.assertFalse(SavedSearch.objects.filter(owner=user).exists())
        self.assertFalse(user.profile.alert_consent_events.exists())
        self.assertEqual(DeliveryAttempt.objects.count(), 0)
        self.assertEqual(DeliveryDailyBudget.objects.count(), 0)
        self.assertEqual(mail.outbox, [])

    def test_exception_diagnostics_omit_messages_and_absolute_paths(self):
        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with redirect_stdout(output):
            try:
                raise ValueError('synthetic-do-not-log')
            except ValueError as exception:
                WorkerRollbackFixture.capture_exception(exception)
        self.assertIn('ValueError', output.getvalue())
        self.assertNotIn('synthetic-do-not-log', output.getvalue())
        self.assertNotIn(str(settings.BASE_DIR), output.getvalue())

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
            context.on('response', lambda response: failures.append('Server error response')
                if response.status >= 500 else None)
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
            page.wait_for_load_state('networkidle')
            assert not failures, ('Browser JavaScript or server response errors occurred. '
                f'Server diagnostics: {WorkerRollbackFixture.server_failures}')
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

    def test_managed_pilot_authorization_dispatch_and_receipt_replay(self):
        from accounts.models import User
        from profiles.models import Profile
        from django.utils import timezone
        from jobs.pilot_test_helpers import prepared_pilot, pilot_settings
        from jobs.brevo_transport import Result
        user = User.objects.create_user(email='managed@example.invalid', full_name='Synthetic Managed Applicant',
            password='Synthetic!Forest-82-Clouds')
        Profile.objects.filter(user=user).update(email_verified_at=timezone.now(), verified_email=user.email)
        with override_settings(**pilot_settings(user)), patch('jobs.brevo_transport.BrevoTransport.send',
                return_value=Result('accepted', '<synthetic@invalid>')) as provider:
            app, package = prepared_pilot(user)
            self.assertEqual(DeliveryAttempt.objects.count(), 0)
            provider.assert_not_called()
            with ThreadPoolExecutor(max_workers=1) as worker:
                worker.submit(self.managed_pilot_journey, user.email).result(timeout=120)
            provider.assert_called_once()
            self.assertEqual(DeliveryAttempt.objects.get(application=app).state, 'accepted')
            self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').application_reserved, 1)

    def managed_pilot_journey(self, email):
        import re
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(viewport={'width': 390, 'height': 844})
            context.route('**/*', lambda route: route.continue_()
                if route.request.url.startswith(self.live_server_url + '/') else route.abort())
            failures = []
            context.on('response', lambda response: failures.append('Server error response')
                if response.status >= 500 else None)
            page = context.new_page()
            page.on('pageerror', lambda error: failures.append(str(error)))
            page.goto(self.live_server_url + '/login')
            page.get_by_label('Email address', exact=True).fill(email)
            page.get_by_label('Password', exact=True).fill('Synthetic!Forest-82-Clouds')
            page.get_by_role('button', name='Log in', exact=True).click()
            expect(page.get_by_role('heading', name='Find your next chapter.', exact=True)).to_be_visible()
            page.goto(self.live_server_url + '/applications')

            def review():
                page.get_by_text('Review application', exact=True).click()
                page.get_by_role('button', name=re.compile('Choose CV and edit cover letter|View saved package revisions')).click()
                page.get_by_role('button', name='Review saved package revision 1', exact=True).click()
                page.get_by_role('button', name='Review email plan / check authorization status', exact=True).click()

            review()
            record = page.get_by_role('button', name='Record authorization (does not send)', exact=True)
            expect(record).to_be_disabled()
            expect(page.get_by_role('button', name='Send this authorized application', exact=True)).to_have_count(0)
            audit(self, page, 'application-email-plan')
            page.get_by_label(re.compile('I authorize Ajiri to email this exact application')).check()
            record.click()
            send = page.get_by_role('button', name='Send this authorized application', exact=True)
            expect(send).to_be_enabled()
            send.click()
            receipt = page.get_by_text('Accepted by the email provider. Inbox delivery is not confirmed.', exact=True)
            expect(receipt).to_be_visible()
            expect(send).to_have_count(0)
            page.reload()
            review()
            expect(receipt).to_be_visible()
            expect(page.get_by_role('button', name='Send this authorized application', exact=True)).to_have_count(0)
            page.wait_for_load_state('networkidle')
            self.assertEqual(failures, [], 'Browser or server errors occurred during managed review.')
            context.close()
            browser.close()
