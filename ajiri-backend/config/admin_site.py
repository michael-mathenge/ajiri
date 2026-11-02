"""Admin login uses the established proxy identity policy and shared counters.

see docs/CONCEPTS.md#admin-job-browsing
"""
from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.core.cache import caches
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from accounts.throttles import EndpointThrottle


class AdminLoginThrottle(EndpointThrottle):
    @property
    def cache(self):
        return caches['admin_login']

    def get_cache_key(self, request, view):
        from django.utils.crypto import salted_hmac
        ident = salted_hmac('ajiri.admin-login', self.get_ident(request)).hexdigest()
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class AjiriAdminSite(AdminSite):
    @method_decorator(never_cache)
    def login(self, request, extra_context=None):
        if request.method == 'POST':
            throttle = AdminLoginThrottle()
            try:
                allowed = throttle.allow_request(request, type('Login', (), {'throttle_scope': 'admin_login'})())
                if allowed and not throttle.cache.get(throttle.key):
                    raise OSError('Throttle counter was not stored.')
            except Exception:
                return HttpResponse('Login temporarily unavailable. Try again later.', status=503)
            if not allowed:
                response = HttpResponse('Too many login attempts. Try again later.', status=429)
                response['Retry-After'] = str(max(1, int(throttle.wait() or 60)))
                return response
        return super().login(request, extra_context)


class AjiriAdminConfig(AdminConfig):
    default_site = 'config.admin_site.AjiriAdminSite'
