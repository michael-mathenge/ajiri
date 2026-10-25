import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('queue_broker_rehearsal',
    Path(__file__).resolve().parents[1]/'queue_broker_rehearsal.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class QueueLabGuardTests(unittest.TestCase):
    def test_default_closed_before_database_or_broker_setup(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                MODULE.setup()
            with self.assertRaises(RuntimeError):
                MODULE.make_app()

    def test_arbitrary_broker_host_is_rejected_before_connecting(self):
        with patch.object(MODULE, 'require_lab'), patch.dict(os.environ,
                {'AJIRI_QUEUE_LAB_HOST': 'outside.example.invalid'}):
            with self.assertRaisesRegex(RuntimeError, 'isolated rehearsal broker'):
                MODULE.make_app()
