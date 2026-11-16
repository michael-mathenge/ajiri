from unittest.mock import patch
from django.core.files.base import ContentFile
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from . import test_certificates as fixtures
from .certificate_scanning import scan_certificate
from .models import CertificateEvidence
from .scanner import Verdict


@override_settings(CERTIFICATE_EVIDENCE_ENABLED=True, MALWARE_SCANNING_ENABLED=True,
    CLAMD_HOST_UTC_CONFIRMED=True, CLAMD_LIMITS_REVIEW='clamd-bounds-v1',
    CLAMD_ALLOWED_ENGINE_VERSIONS=['1.4.3'],
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CertificateScanningTests(TransactionTestCase):
    setUp = fixtures.CertificateTests.setUp
    upload = fixtures.CertificateTests.upload
    create = fixtures.CertificateTests.create
    url = fixtures.CertificateTests.url
    def test_actual_scan_claim_updates_only_the_unchanged_file(self):
        row = self.create()
        version = 'ClamAV 1.4.3/1/'+timezone.now().strftime('%a %b %d %H:%M:%S %Y')
        with patch('profiles.certificate_scanning.scan_bytes', return_value=Verdict('clean', row.sha256, version)) as scan:
            self.assertTrue(scan_certificate(row.pk))
        scan.assert_called_once()
        self.assertEqual(self.client.get(self.url()).status_code, 200)

    def test_replacement_during_scan_cannot_mark_new_bytes_clean(self):
        old = self.create()

        def replace(data):
            from .certificates import put
            put(self.user.profile, self.ids[0], 1, self.upload(), expected_id=old.pk, expected_hash=old.sha256)
            return Verdict('clean', old.sha256, 'synthetic wire result')

        with patch('profiles.certificate_scanning.scan_bytes', side_effect=replace):
            self.assertFalse(scan_certificate(old.pk))
        row = CertificateEvidence.objects.get()
        self.assertNotEqual(row.pk, old.pk)
        self.assertEqual(row.scan_state, 'pending')

    def test_legacy_cv_download_requires_a_current_scan_before_returning_bytes(self):
        from .upload_fixtures import pdf_bytes
        self.user.profile.cv_file.save('legacy.pdf', ContentFile(pdf_bytes()))
        with patch('profiles.scanner.scan_bytes', return_value=Verdict('unavailable', '')):
            self.assertEqual(self.client.get('/api/profiles/me/cv/').status_code, 503)
        with patch('profiles.scanner.scan_bytes', return_value=Verdict('clean', 'synthetic')):
            response = self.client.get('/api/profiles/me/cv/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), pdf_bytes())
