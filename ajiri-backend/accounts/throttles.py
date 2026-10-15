from rest_framework.throttling import ScopedRateThrottle
from django.conf import settings
from django.core.cache import caches


class EndpointThrottle(ScopedRateThrottle):
    """Public credentials are IP-scoped; authenticated mutations are user-scoped."""
    # see docs/CONCEPTS.md#endpoint-throttling
    @property
    def cache(self):
        # Resolve at request time so every worker uses the configured shared alias.
        # see docs/CONCEPTS.md#shared-throttle-cache
        return caches['throttle' if 'throttle' in settings.CACHES else 'default']

    def get_cache_key(self, request, view):
        if self.scope in {'login', 'register', 'refresh'}:
            ident = self.get_ident(request)
        else:
            ident = request.user.pk if request.user.is_authenticated else self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}
