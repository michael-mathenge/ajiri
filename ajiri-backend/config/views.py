from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@require_safe
@never_cache
def frontend(request):
    """
    Serves the built React app's index.html for any URL that isn't an API,
    admin, media or static route — e.g. /login or /jobs/5. React Router
    handles those paths in the browser, so the server just has to hand back
    the same HTML shell. Without this, refreshing the page on /jobs/5 would
    404. See docs/CONCEPTS.md#spa-fallback-route

    never_cache matters: index.html references hashed asset filenames, so
    the browser must re-fetch it after every deploy to pick up new ones.
    """
    index_file = settings.FRONTEND_BUILD_DIR / 'index.html'
    if not index_file.is_file():
        return HttpResponseNotFound(
            'Frontend build not found. Run scripts/build_frontend.ps1, or use the '
            'Vite dev server (npm run dev) during development.',
            content_type='text/plain',
        )
    return HttpResponse(index_file.read_bytes(), content_type='text/html; charset=utf-8')
