from rest_framework.throttling import ScopedRateThrottle


class EndpointThrottle(ScopedRateThrottle):
    """Public credentials are IP-scoped; authenticated mutations are user-scoped."""
    # see docs/CONCEPTS.md#endpoint-throttling
    def get_cache_key(self, request, view):
        if self.scope in {'login', 'register', 'refresh'}:
            ident = self.get_ident(request)
        else:
            ident = request.user.pk if request.user.is_authenticated else self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}
