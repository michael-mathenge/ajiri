"""Version-one aliases preserve the original views and their security checks."""
from django.urls import include, path
from .views import HealthView
from accounts.urls import urlpatterns as accounts
from profiles.urls import urlpatterns as profiles
from jobs.urls import urlpatterns as jobs

# Operational ingestion URLs stay at their existing stable paths only.
# see docs/CONCEPTS.md#api-version-contract
urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('accounts/', include((accounts, 'accounts'))),
    path('profiles/', include((profiles, 'profiles'))),
    path('jobs/', include(([p for p in jobs if p.name not in ('ingest-feed', 'sweep-matches')], 'jobs'))),
]
