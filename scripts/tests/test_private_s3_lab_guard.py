import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('private_s3_rehearsal',
    Path(__file__).resolve().parents[1]/'private_s3_rehearsal.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrivateS3GuardTests(unittest.TestCase):
    def test_ordinary_execution_is_rejected_before_sdk_or_server_setup(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError): MODULE.require_lab()
            with self.assertRaises(RuntimeError): MODULE.main()
