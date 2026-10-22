import json
import struct
from pathlib import Path
from django.conf import settings
from django.test import SimpleTestCase


class PWAAssetsTests(SimpleTestCase):
    def test_manifest_and_actual_icon_dimensions_are_valid(self):
        root = Path(settings.FRONTEND_BUILD_DIR)
        manifest = json.loads((root / 'manifest.webmanifest').read_text())
        self.assertEqual(manifest['id'], '/')
        self.assertEqual(manifest['scope'], '/')
        self.assertEqual(manifest['display'], 'standalone')
        self.assertEqual(manifest['start_url'], '/login')
        self.assertTrue(manifest['name'] and manifest['short_name'])
        self.assertEqual(len(manifest['icons']), 2)
        for icon in manifest['icons']:
            data = (root / icon['src'].lstrip('/')).read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            width, height = struct.unpack('!II', data[16:24])
            self.assertIn(width, (192, 512))
            self.assertEqual(width, height)
            self.assertEqual(icon['sizes'], f'{width}x{height}')
        self.assertIn('manifest.webmanifest', (root / 'index.html').read_text())

    def test_offline_fallback_is_self_contained_and_contains_no_account_fields(self):
        offline = (Path(settings.FRONTEND_BUILD_DIR) / 'offline.html').read_text()
        self.assertIn("You're offline", offline)
        self.assertNotIn('<script', offline)
        self.assertNotIn('http://', offline)
        self.assertNotIn('https://', offline)
        self.assertNotIn('access_token', offline)
        self.assertNotIn('<form', offline)
