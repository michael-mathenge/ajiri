"""No real malware, actual scanner or private upload transfer is used."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from .scanning_test_contract import QuarantineFixture, FixtureScanner, FixtureResult, ScanConflict
from .upload_fixtures import pdf_bytes, docx_bytes
from .upload_validation import MAX_BYTES


class ScannerContractTests(SimpleTestCase):
    def setUp(self):
        self.store = QuarantineFixture()
        self.data = pdf_bytes()
        self.identity = self.store.stage(1, SimpleUploadedFile('synthetic.pdf', self.data))

    def scan(self, verdict='clean'):
        return self.store.scan(1, self.identity, FixtureScanner(verdict), expected_revision=1)

    def test_pending_is_private_and_not_downloadable_before_an_explicit_scan(self):
        self.assertEqual(self.store.status(1, self.identity)['state'], 'pending')
        with self.assertRaises(ScanConflict): self.store.download(1, self.identity)
        self.assertEqual(self.scan(), 'clean')
        self.assertEqual(self.store.download(1, self.identity), self.data)

    def test_owner_isolation_for_status_download_scan_remove_and_replace(self):
        for action in [lambda: self.store.status(2, self.identity),
                       lambda: self.store.download(2, self.identity),
                       lambda: self.store.scan(2, self.identity, FixtureScanner('clean'), expected_revision=1),
                       lambda: self.store.remove(2, self.identity, expected_revision=1),
                       lambda: self.store.stage(2, SimpleUploadedFile('x.pdf', self.data), identity=self.identity, expected_revision=1)]:
            with self.assertRaises(LookupError): action()
        self.assertEqual(self.store.status(1, self.identity)['state'], 'pending')

    def test_infected_unavailable_timeout_and_bad_receipts_fail_closed(self):
        for result in [FixtureResult('infected', self.store.status(1, self.identity)['sha256']),
                       FixtureResult('unavailable', self.store.status(1, self.identity)['sha256']),
                       FixtureResult('clean', self.store.status(1, self.identity)['sha256'], 'unreviewed-engine'),
                       FixtureResult('clean', '0'*64), FixtureResult('other', '0'*64), None]:
            identity=self.store.stage(1, SimpleUploadedFile('fresh.pdf', self.data))
            with patch.object(FixtureScanner, 'scan', return_value=result):
                outcome=self.store.scan(1, identity, FixtureScanner(), expected_revision=1)
            self.assertIn(outcome, ('infected', 'unavailable'))
            with self.assertRaises(ScanConflict): self.store.download(1, identity)
        with patch.object(FixtureScanner, 'scan', side_effect=TimeoutError):
            self.assertEqual(self.scan(), 'unavailable')
        with self.assertRaises(ScanConflict): self.store.download(1, self.identity)

    def test_existing_format_and_size_checks_precede_quarantine(self):
        for name, data in [('spoof.pdf', b'not PDF'), ('empty.docx', b''),
                           ('large.pdf', b'x'*(MAX_BYTES+1)), ('fake.docx', self.data)]:
            with self.assertRaises(ValidationError):
                self.store.stage(1, SimpleUploadedFile(name, data))
        identity=self.store.stage(1, SimpleUploadedFile('synthetic.docx', docx_bytes()))
        self.assertEqual(self.store.status(1, identity)['state'], 'pending')

    def test_replacement_invalidates_clean_state_and_old_revision(self):
        self.scan()
        replacement=pdf_bytes()+b'\nSynthetic replacement\n'
        self.store.stage(1, SimpleUploadedFile('new.pdf', replacement), identity=self.identity, expected_revision=1)
        with self.assertRaises(ScanConflict): self.store.download(1, self.identity)
        with self.assertRaises(ScanConflict): self.scan()
        self.assertEqual(self.store.scan(1, self.identity, FixtureScanner('clean'), expected_revision=2), 'clean')
        self.assertEqual(self.store.download(1, self.identity), replacement)

    def test_inflight_scan_cannot_release_replacement_or_removed_bytes(self):
        for remove in (False, True):
            store=QuarantineFixture(); identity=store.stage(1, SimpleUploadedFile('race.pdf', self.data))
            started=Event(); finish=Event()

            def delayed(data):
                started.set(); self.assertTrue(finish.wait(10))
                import hashlib
                return FixtureResult('clean', hashlib.sha256(data).hexdigest())

            with patch.object(FixtureScanner, 'scan', side_effect=delayed), ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(store.scan,1,identity,FixtureScanner(),expected_revision=1)
                self.assertTrue(started.wait(10))
                with self.assertRaises(ScanConflict): store.download(1, identity)
                if remove: store.remove(1, identity, expected_revision=1)
                else: store.stage(1, SimpleUploadedFile('new.pdf', self.data), identity=identity, expected_revision=1)
                finish.set()
                with self.assertRaises(ScanConflict): future.result(timeout=10)
            self.assertEqual(store.status(1,identity)['state'], 'removed' if remove else 'pending')
            with self.assertRaises(ScanConflict): store.download(1,identity)

    def test_actual_adapter_and_client_clean_assertion_cannot_release_fixture(self):
        with self.assertRaises(ValueError):
            self.store.scan(1,self.identity,object(),expected_revision=1)
        with self.assertRaises(TypeError):
            self.store.stage(1,SimpleUploadedFile('x.pdf',self.data),clean=True)
        self.assertEqual(self.store.status(1,self.identity)['state'],'pending')

    def test_removing_clean_fixture_blocks_read_and_resurrection(self):
        self.scan()
        self.store.remove(1,self.identity,expected_revision=1)
        with self.assertRaises(ScanConflict): self.store.download(1,self.identity)
        with self.assertRaises(ScanConflict):
            self.store.stage(1,SimpleUploadedFile('x.pdf',self.data),identity=self.identity,expected_revision=2)
        self.assertEqual(self.store.status(1,self.identity)['state'],'removed')
