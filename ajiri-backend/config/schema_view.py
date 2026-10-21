"""Serve only the reviewed source contract; never introspect live private data."""
from pathlib import Path
from django.http import FileResponse
from django.views.decorators.http import require_safe


@require_safe
def schema_document(request):
    # see docs/CONCEPTS.md#api-version-contract
    response = FileResponse(Path(__file__).with_name('openapi.json').open('rb'),
                            content_type='application/vnd.oai.openapi+json')
    response['Cache-Control'] = 'public, max-age=300'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
