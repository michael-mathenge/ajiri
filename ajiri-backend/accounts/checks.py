from django.core.checks import Error, register
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from .pilot import configuration, transport
from . import general_email


@register()
def check_email_pilot(app_configs, **kwargs):
    try:
        if getattr(settings, 'ACCOUNT_SECURITY_EMAIL_ENABLED', False):
            general_email.configuration()
            return []
        policy = configuration()
        if policy:
            transport(policy)  # Constructs only; never sends or tests connectivity.
    except ImproperlyConfigured:
        return [Error('Owner email pilot configuration is invalid or incomplete.', id='accounts.E001')]
    return []
