"""Offline schema tooling only; not a production settings module."""
from .settings import *  # noqa: F403
from .settings import INSTALLED_APPS, REST_FRAMEWORK

INSTALLED_APPS = [*INSTALLED_APPS, 'drf_spectacular']
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_SCHEMA_CLASS': 'config.schema_contract.ContractSchema'}
SPECTACULAR_SETTINGS = {
    'DEFAULT_GENERATOR_CLASS': 'config.schema_contract.ContractGenerator',
    'TITLE': 'Ajiri API', 'VERSION': '1.0.0',
    'DESCRIPTION': 'Version-one aliases. Existing /api routes remain supported. Private endpoints require owner authentication. Drafting never sends email. Custom response objects not fully typed here are explicitly marked; consult endpoint guides.',
    'SERVE_INCLUDE_SCHEMA': False,
    'APPEND_COMPONENTS': {'securitySchemes': {'refreshCookie': {'type': 'apiKey', 'in': 'cookie', 'name': 'refresh_token', 'description': 'httpOnly cookie; CSRF token and valid Origin required.'}}},
    'DISABLE_DOCSTRING_DESCRIPTIONS': True,
    'COMPONENT_SPLIT_REQUEST': True,
    'PREPROCESSING_HOOKS': ['config.schema_contract.version_one_only'],
}

# Generation must never inspect a developer or production database.
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
