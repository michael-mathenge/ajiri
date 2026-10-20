"""Isolated development container, never production or real provider delivery.

see docs/CONCEPTS.md#isolated-container-staging
"""
from .settings import *  # noqa: F403

if not DEBUG:
    raise ImproperlyConfigured('Container staging requires explicit local DEBUG=True.')

DATABASES['default']['NAME'] = '/data/db.sqlite3'
MEDIA_ROOT = Path('/data/private-media')
REAL_EMAIL_ENABLED = False
ACCOUNT_EMAIL_TEST_CAPTURE = False
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
INGEST_API_KEY = ''
TRUST_PROXY_SSL_HEADER = False
SECURE_PROXY_SSL_HEADER = None
