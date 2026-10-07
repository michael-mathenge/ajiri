from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path, include

from .views import frontend

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/profiles/', include('profiles.urls')),
    path('api/jobs/', include('jobs.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Catch-all for the React app: anything that isn't API/admin/media/static
# gets index.html, and React Router takes over in the browser. Must stay LAST.
urlpatterns += [
    re_path(r'^(?!api/|admin/|media/|static/).*$', frontend),
]
