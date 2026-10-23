from django.contrib import admin
from django.urls import path, re_path, include

from .views import frontend, HealthView
from .schema_view import schema_document
from jobs import public_views

urlpatterns = [
    path('vacancies/<int:pk>/<slug:slug>/', public_views.detail, name='public-job-detail'),
    path('sitemap.xml', public_views.sitemap_index, name='public-job-sitemap-index'),
    path('sitemap-jobs-<int:page>.xml', public_views.sitemap_page, name='public-job-sitemap'),
    path('robots.txt', public_views.robots, name='public-job-robots'),
    path('api/schema/', schema_document, name='openapi-schema'),
    path('api/v1/', include(('config.v1_urls', 'v1'))),
    path('api/health/', HealthView.as_view(), name='health'),
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/profiles/', include('profiles.urls')),
    path('api/jobs/', include('jobs.urls')),
]

# Private documents are served only through authenticated owner endpoints.
# see docs/CONCEPTS.md#private-media-storage

# Catch-all for the React app: anything that isn't API/admin/media/static
# gets index.html, and React Router takes over in the browser. Must stay LAST.
urlpatterns += [
    re_path(r'^(?!api/|admin/|media/|static/).*$', frontend),
]
