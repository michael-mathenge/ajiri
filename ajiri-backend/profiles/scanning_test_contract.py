"""Memory-only quarantine fixture, not a scanner or a production upload path.

see docs/CONCEPTS.md#scanner-test-contract
"""
from dataclasses import dataclass, field, replace
import hashlib
from threading import Lock
import uuid

from .upload_validation import validate_cv_upload, MAX_BYTES


class ScanConflict(Exception):
    pass


@dataclass(frozen=True)
class FixtureResult:
    verdict: str
    sha256: str
    engine_version: str = 'fixture-only'


class FixtureScanner:
    def __init__(self, verdict='unavailable'):
        self.verdict = verdict

    def scan(self, data):
        return FixtureResult(self.verdict, hashlib.sha256(data).hexdigest())


@dataclass(frozen=True)
class _Blob:
    id: uuid.UUID
    owner: int
    revision: int
    sha256: str
    state: str
    data: bytes = field(repr=False)


class QuarantineFixture:
    def __init__(self):
        self._rows = {}
        self._lock = Lock()

    def _owned(self, owner, identity):
        row = self._rows.get(identity)
        if type(owner) is not int or owner <= 0 or row is None or row.owner != owner:
            raise LookupError('Private fixture not found.')
        return row

    def stage(self, owner, upload, *, identity=None, expected_revision=None):
        if type(owner) is not int or owner <= 0:
            raise ValueError('A synthetic owner ID is required.')
        if identity is not None:
            with self._lock:
                self._owned(owner, identity)
        validate_cv_upload(upload)
        upload.seek(0)
        data = upload.read(MAX_BYTES+1)
        if not data or len(data) != upload.size or len(data) > MAX_BYTES:
            raise ValueError('Bounded fixture bytes are required.')
        with self._lock:
            revision = 1
            if identity is not None:
                old = self._owned(owner, identity)
                if type(expected_revision) is not int or old.revision != expected_revision or old.state == 'removed':
                    raise ScanConflict('The private fixture changed; reload before replacing.')
                revision = old.revision+1
            elif expected_revision is not None:
                raise ScanConflict('A new fixture has no previous revision.')
            identity = identity or uuid.uuid4()
            self._rows[identity] = _Blob(identity, owner, revision,
                hashlib.sha256(data).hexdigest(), 'pending', bytes(data))
            return identity

    def status(self, owner, identity):
        with self._lock:
            row = self._owned(owner, identity)
            return {'id': row.id, 'revision': row.revision, 'sha256': row.sha256, 'state': row.state}

    def scan(self, owner, identity, scanner, *, expected_revision):
        if type(scanner) is not FixtureScanner:
            raise ValueError('Only the offline scanner fixture is supported.')
        with self._lock:
            row = self._owned(owner, identity)
            if type(expected_revision) is not int or row.revision != expected_revision or row.state not in ('pending', 'unavailable'):
                raise ScanConflict('Review the current fixture state before an explicit scan.')
            self._rows[identity] = replace(row, state='scanning')
        try:
            result = scanner.scan(row.data)
        except Exception:
            # No exception text/private bytes leave this synthetic boundary.
            result = None
        verdict = 'unavailable'
        if (type(result) is FixtureResult and result.sha256 == row.sha256
                and result.engine_version == 'fixture-only'
                and result.verdict in ('clean', 'infected', 'unavailable')):
            verdict = result.verdict
        with self._lock:
            current = self._owned(owner, identity)
            if current.revision != row.revision or current.sha256 != row.sha256 or current.state != 'scanning':
                raise ScanConflict('A stale scan cannot release a changed or removed fixture.')
            self._rows[identity] = replace(current, state=verdict)
            return verdict

    def download(self, owner, identity):
        with self._lock:
            row = self._owned(owner, identity)
            if row.state != 'clean':
                raise ScanConflict('Only a current clean fixture can be read.')
            return bytes(row.data)

    def remove(self, owner, identity, *, expected_revision):
        with self._lock:
            row = self._owned(owner, identity)
            if type(expected_revision) is not int or row.revision != expected_revision:
                raise ScanConflict('The fixture changed; reload before removing.')
            # Logical removal only; this fixture does not implement retention deletion.
            self._rows[identity] = replace(row, revision=row.revision+1, state='removed')
