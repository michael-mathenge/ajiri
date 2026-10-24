from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('storage_rehearsal',
    Path(__file__).resolve().parents[1]/'storage_rehearsal.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FixturePrecisionTests(unittest.TestCase):
    def test_authorization_instant_keeps_all_microseconds(self):
        instant = datetime(2026, 10, 24, 12, 0, 0, 870680, tzinfo=timezone.utc)
        restored = json.loads(MODULE.fixture_json({'authorized_at': instant}))
        self.assertEqual(datetime.fromisoformat(restored['authorized_at']), instant)
