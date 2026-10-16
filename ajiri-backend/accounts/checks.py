from django.core.checks import Error, register
from django.core.exceptions import ImproperlyConfigured

from .pilot import configuration, transport


@register()
def check_email_pilot(app_configs, **kwargs):
    try:
        policy = configuration()
        if policy:
            transport(policy)  # Constructs only; never sends or tests connectivity.
    except ImproperlyConfigured:
        return [Error('Owner email pilot configuration is invalid or incomplete.', id='accounts.E001')]
    return []
