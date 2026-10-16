"""Purpose-bound account links and reset revocation; no real sending integration.

see docs/CONCEPTS.md#account-recovery-links
"""
from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.mail import EmailMessage
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from profiles.models import Profile

VERIFY_SALT = 'ajiri.accounts.verify-email.v1'


def password_fingerprint(user):
    return salted_hmac('ajiri.refresh.password.v1', user.password).hexdigest()


def refresh_owner(refresh):
    user = get_user_model().objects.filter(pk=refresh.get('user_id'), is_active=True).first()
    profile = Profile.objects.filter(user=user).first() if user else None
    if not user or not profile:
        return None
    fingerprint = refresh.get('password_version')
    if fingerprint is None:
        return user if profile.password_reset_at is None else None
    return user if isinstance(fingerprint, str) and constant_time_compare(fingerprint, password_fingerprint(user)) else None


def verification_state(user, profile):
    value = f'{user.pk}:{user.email.casefold()}:{profile.email_verified_at}:{user.password}'
    return salted_hmac('ajiri.verify.state.v1', value).hexdigest()


def verification_token(user, profile):
    return signing.dumps({'uid': user.pk, 'email': user.email.casefold(),
        'state': verification_state(user, profile)}, salt=VERIFY_SALT)


def capture_enabled():
    # A test-only capture path, NOT a real SMTP/Brevo activation switch. In particular
    # console output must never receive password reset or verification credentials.
    return (getattr(settings, 'ACCOUNT_EMAIL_TEST_CAPTURE', False) is True
        and settings.EMAIL_BACKEND == 'django.core.mail.backends.locmem.EmailBackend')


def capture_link(user, purpose):
    if not capture_enabled():
        return
    origin = getattr(settings, 'ACCOUNT_LINK_ORIGIN', 'https://mathenge.pythonanywhere.com')
    parsed = urlsplit(origin)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.path not in ('', '/') or parsed.query or parsed.fragment or parsed.username:
        return  # Never build links from request Host or persist broken configuration.
    if purpose == 'password_reset':
        values = {'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                  'token': default_token_generator.make_token(user)}
        route = '/reset-password'
    else:
        profile = Profile.objects.get(user=user)
        values = {'token': verification_token(user, profile)}
        route = '/verify-email'
    link = origin.rstrip('/') + route + '#' + urlencode(values)
    EmailMessage(subject='Ajiri account security', body=f'Use this account link: {link}',
        from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email]).send(fail_silently=False)
