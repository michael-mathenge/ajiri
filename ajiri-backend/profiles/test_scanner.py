import hashlib
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .scanner import ScanUnavailable, Verdict, require_clean, scan_bytes
from .upload_fixtures import pdf_bytes
from .upload_validation import validate_cv_upload


@override_settings(MALWARE_SCANNING_ENABLED=True, CLAMD_HOST_UTC_CONFIRMED=True,
    CLAMD_ALLOWED_ENGINE_VERSIONS=['1.4.3'], CLAMD_LIMITS_REVIEW='clamd-bounds-v1',
    CLAMD_UNIX_SOCKET='', CLAMD_HOST='127.0.0.1', CLAMD_PORT='3310')
class ScannerProtocolTests(SimpleTestCase):
    def socket(self, reply):
        stream = MagicMock()
        stream.__enter__.return_value = stream
        stream.recv.side_effect = [reply+b'\0', b'']
        return stream

    def version(self, at=None):
        return ('ClamAV 1.4.3/1/'+(at or timezone.now()).strftime('%a %b %d %H:%M:%S %Y')).encode()

    def scan(self, verdict=b'stream: OK', *, at=None):
        version = self.socket(self.version(at)+b'| COMMANDS: INSTREAM VERSIONCOMMANDS')
        content = self.socket(verdict)
        with patch('profiles.scanner.socket.create_connection', side_effect=[version, content]) as connect:
            result = scan_bytes(pdf_bytes())
        return result, version, content, connect

    def test_clean_protocol_binds_exact_bytes_and_uses_framed_bounded_stream(self):
        result, version, content, connect = self.scan()
        self.assertEqual(result.state, 'clean')
        self.assertEqual(result.sha256, hashlib.sha256(pdf_bytes()).hexdigest())
        self.assertEqual(connect.call_count, 2)
        version.sendall.assert_called_once_with(b'zVERSIONCOMMANDS\0')
        sent = [call.args[0] for call in content.sendall.call_args_list]
        self.assertEqual(sent[0], b'zINSTREAM\0')
        self.assertEqual(sent[-1], b'\0\0\0\0')
        self.assertEqual(int.from_bytes(sent[1][:4], 'big'), len(pdf_bytes()))
        self.assertEqual(sent[1][4:], pdf_bytes())

    def test_infected_limits_error_and_malformed_responses_never_become_clean(self):
        for reply, state in [(b'stream: Eicar-Test-Signature FOUND', 'infected'),
                (b'stream: Heuristics.Limits.Exceeded.MaxScanSize FOUND', 'unavailable'),
                (b'stream: Heuristics.Encrypted.PDF FOUND', 'unavailable'),
                (b'INSTREAM size limit exceeded ERROR', 'unavailable'), (b'OK', 'unavailable')]:
            with self.subTest(reply=reply):
                self.assertEqual(self.scan(reply)[0].state, state)

    def test_stale_database_stops_before_any_document_transfer(self):
        result, _, content, connect = self.scan(at=timezone.now()-timedelta(days=2))
        self.assertEqual(result.state, 'unavailable')
        self.assertEqual(connect.call_count, 1)
        content.sendall.assert_not_called()

    def test_disabled_unapproved_version_remote_host_or_missing_review_fail_closed(self):
        for values in ({'MALWARE_SCANNING_ENABLED': False}, {'CLAMD_ALLOWED_ENGINE_VERSIONS': []},
                       {'CLAMD_HOST': 'remote.example.invalid'}, {'CLAMD_HOST_UTC_CONFIRMED': False},
                       {'CLAMD_LIMITS_REVIEW': ''}):
            with self.subTest(values=values), override_settings(**values), patch('profiles.scanner.socket.create_connection') as connect:
                self.assertEqual(scan_bytes(pdf_bytes()).state, 'unavailable')
                connect.assert_not_called()

    def test_timeout_has_no_automatic_retry_and_invalid_size_has_no_socket(self):
        with patch('profiles.scanner.socket.create_connection', side_effect=TimeoutError) as connect:
            self.assertEqual(scan_bytes(pdf_bytes()).state, 'unavailable')
            connect.assert_called_once()
        with patch('profiles.scanner.socket.create_connection') as connect:
            self.assertEqual(scan_bytes(b'x'*(5*1024*1024+1)).state, 'unavailable')
            connect.assert_not_called()

    def test_upload_content_validation_invokes_real_boundary_and_preserves_cursor(self):
        upload = SimpleUploadedFile('test.pdf', pdf_bytes())
        with patch('profiles.scanner.scan_bytes', return_value=Verdict('unavailable', '')):
            with self.assertRaises(ScanUnavailable):
                validate_cv_upload(upload)
        self.assertEqual(upload.tell(), 0)
        with patch('profiles.scanner.scan_bytes', return_value=Verdict('infected', '')):
            with self.assertRaises(ValidationError):
                require_clean(pdf_bytes())
