import tempfile
from pathlib import Path

from django.test import SimpleTestCase, override_settings


class FrontendFallbackTests(SimpleTestCase):
    """The catch-all route must serve the React shell for client-side URLs only."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        build_dir = Path(self._tmp.name)
        (build_dir / 'index.html').write_text('<html><body>AJIRI-SHELL</body></html>', encoding='utf-8')
        override = override_settings(FRONTEND_BUILD_DIR=build_dir)
        override.enable()
        self.addCleanup(override.disable)

    def test_client_side_routes_get_index_html(self):
        for path in ('/', '/login', '/jobs/5', '/applications'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertContains(response, 'AJIRI-SHELL')

    def test_index_html_is_never_cached(self):
        self.assertIn('no-cache', self.client.get('/login')['Cache-Control'])

    def test_api_admin_media_and_static_paths_are_not_swallowed(self):
        for path in ('/api/nope/', '/media/missing.docx', '/static/missing.css'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404, path)
            self.assertNotContains(response, 'AJIRI-SHELL', status_code=404)

    def test_post_to_frontend_route_is_rejected(self):
        self.assertEqual(self.client.post('/login').status_code, 405)

    def test_missing_build_gives_helpful_404(self):
        with override_settings(FRONTEND_BUILD_DIR=Path('/nonexistent/build')):
            response = self.client.get('/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'build_frontend', status_code=404)
