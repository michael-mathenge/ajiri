from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import APIException


class CSRFRejected(APIException):
    status_code = 403
    default_detail = 'CSRF verification failed. Reload and try again.'
    default_code = 'csrf_failed'


class _CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return only a verdict: CSRF internals/hostnames do not belong in logs.
        return True


class CookieCSRFViewMixin:
    # see docs/CONCEPTS.md#cookie-csrf
    def initial(self, request, *args, **kwargs):
        raw = request._request
        # Match Django's normal test-client exemption; attack tests enforce checks.
        if raw.method not in {'GET', 'HEAD', 'OPTIONS'} and not getattr(raw, '_dont_enforce_csrf_checks', False):
            origin = raw.META.get('HTTP_ORIGIN')
            allowed = {f'{raw.scheme}://{raw.get_host()}', *settings.CSRF_TRUSTED_ORIGINS}
            if not origin or origin == 'null' or origin not in allowed:
                raise CSRFRejected()
            check = _CSRFCheck(lambda req: None)
            check.process_request(raw)
            if check.process_view(raw, lambda req: None, (), {}):
                raise CSRFRejected()
        return super().initial(request, *args, **kwargs)

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if isinstance(exc, CSRFRejected):
            response.data['code'] = 'csrf_failed'
        return response
