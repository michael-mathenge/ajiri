from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle
from django.conf import settings
from django.core.cache import caches
from django.utils.crypto import salted_hmac


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


class AccountTargetThrottle(EndpointThrottle):
    """Combined reset/verification budget keyed without plaintext email in the cache."""
    def allow_request(self, request, view):
        self.scope = 'account_target'
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return SimpleRateThrottle.allow_request(self, request, view)

    def get_cache_key(self, request, view):
        raw = request.user.email if request.user.is_authenticated else request.data.get('email', '')
        value = raw.strip().casefold() if isinstance(raw, str) else ''
        digest = salted_hmac('ajiri.account-email-throttle', value).hexdigest()
        return self.cache_format % {'scope': 'account_target', 'ident': digest}
