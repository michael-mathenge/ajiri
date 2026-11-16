import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('current_outbox_rehearsal',
    Path(__file__).resolve().parents[1]/'current_outbox_rehearsal.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CurrentOutboxGuardTests(unittest.TestCase):
    def test_default_execution_refused_before_django_or_broker_setup(self):
        with patch.dict(os.environ, {}, clear=True):
            for operation in (MODULE.require_lab, MODULE.setup, MODULE.worker):
                with self.assertRaises(RuntimeError):
                    operation()

    def test_only_isolated_broker_names_allowed(self):
        with patch.object(MODULE.os, 'name', 'posix'), patch.object(MODULE.Path, 'is_file', return_value=True):
            with patch.dict(os.environ, {'AJIRI_QUEUE_REHEARSAL': 'synthetic-only',
                    'AJIRI_QUEUE_LAB_HOST': 'outside.example.invalid'}, clear=True):
                with self.assertRaisesRegex(RuntimeError, 'isolated rehearsal broker'):
                    MODULE.require_lab()
