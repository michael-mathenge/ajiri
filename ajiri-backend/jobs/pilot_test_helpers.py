"""Synthetic prepared documents for isolated pilot tests; never imported by runtime."""
import uuid
from .models import Job, Application
from .application_dispatch import SOURCE, LIMIT_REVIEW, DISCLAIMER
from .application_packages import save_package, context
from .package_review import approve_package
from profiles.cv_test_helpers import approved_cv
from profiles.cv_builder import content_hash


def pilot_settings(user):
    return dict(APPLICATION_EMAIL_ENABLED=True, APPLICATION_PILOT_LIMIT_REVIEW=LIMIT_REVIEW,
        REAL_EMAIL_ENABLED=True, EMAIL_DELIVERY_MODE='owner_pilot', EMAIL_PILOT_OWNER_ID=str(user.pk),
        EMAIL_PILOT_RECIPIENT=user.email, EMAIL_PILOT_DAILY_LIMIT='5', BREVO_TIMEOUT_SECONDS='10',
        EMAIL_PLATFORM_FROM='platform@example.invalid', EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
        ACCOUNT_EMAIL_TEST_CAPTURE=False, ACCOUNT_LINK_ORIGIN='https://example.invalid',
        BREVO_API_KEY='synthetic-placeholder-not-a-key')


def prepared_pilot(user):
    job = Job.objects.create(title='Ajiri synthetic application pilot', company_name='Synthetic example',
        description='Synthetic vacancy, no employer contact.', is_active=False, source_name=SOURCE,
        source_url=f'https://example.invalid/{SOURCE}/{user.pk}/{uuid.uuid4()}',
        application_method='email', application_email=user.email)
    app = Application.objects.create(user=user, job=job, status='ready_for_review',
        application_method='email', application_email=user.email)
    cv = approved_cv(user)
    package = save_package(user, app.pk, {'cv_version': cv.pk, 'expected_revision': 0,
        'context_sha256': content_hash(context(app)), 'letter_text': 'Synthetic letter for owner test.',
        'email_subject': '[AJIRI PILOT] Synthetic application', 'email_body': DISCLAIMER})
    approve_package(user, app.pk, package.pk, 1, package.content_sha256)
    return app, package
