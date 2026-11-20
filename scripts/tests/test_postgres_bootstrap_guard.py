import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('postgres_bootstrap_rehearsal',
    Path(__file__).resolve().parents[1]/'postgres_bootstrap_rehearsal.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PostgresBootstrapGuardTests(unittest.TestCase):
    def test_ordinary_execution_refused_before_setup_or_migration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError): MODULE.require_lab()
            with self.assertRaises(RuntimeError): MODULE.main()
