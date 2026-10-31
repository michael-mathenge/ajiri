"""Bounded local ClamD protocol adapter; no remote vendor transfer or retries.

see docs/CONCEPTS.md#local-malware-scanning
"""
import hashlib
import re
import socket
import struct
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as utc_timezone

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

MAX_BYTES = 5*1024*1024
LIMITS_REVIEW = 'clamd-bounds-v1'


class ScanUnavailable(APIException):
    status_code = 503
    default_detail = 'Private upload scanning is unavailable. Keep your current file and try later.'


@dataclass(frozen=True)
class Verdict:
    state: str
    sha256: str
    version: str = ''


def enabled():
    return getattr(settings, 'MALWARE_SCANNING_ENABLED', False) is True


def version_current(version):
    if (not enabled() or not getattr(settings, 'CLAMD_HOST_UTC_CONFIRMED', False)
            or getattr(settings, 'CLAMD_LIMITS_REVIEW', '') != LIMITS_REVIEW):
        return False
    try:
        match = re.fullmatch(r'ClamAV ([0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?)/[0-9]{1,16}/(.{1,64})', version)
        if match is None or len(version) > 128 or match[1] not in settings.CLAMD_ALLOWED_ENGINE_VERSIONS:
            return False
        at = datetime.strptime(match[2], '%a %b %d %H:%M:%S %Y').replace(tzinfo=utc_timezone.utc)
        now = timezone.now()
        return now-timedelta(hours=24) <= at <= now+timedelta(minutes=5)
    except (AttributeError, TypeError, ValueError):
        return False


def result_current(version, scanned_at):
    now = timezone.now()
    return (version_current(version) and scanned_at is not None
            and now-timedelta(hours=24) <= scanned_at <= now)


def _remaining(deadline):
    left = deadline-time.monotonic()
    if left <= 0:
        raise TimeoutError
    return left


def _connect(deadline):
    path = getattr(settings, 'CLAMD_UNIX_SOCKET', '')
    if path:
        if not path.startswith('/') or '\x00' in path or len(path) > 100:
            raise ValueError
        stream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            stream.settimeout(_remaining(deadline))
            stream.connect(path)
            return stream
        except Exception:
            stream.close()
            raise
    host = getattr(settings, 'CLAMD_HOST', '127.0.0.1')
    port = int(getattr(settings, 'CLAMD_PORT', 3310))
    if host not in ('127.0.0.1', '::1') or not 1 <= port <= 65535:
        raise ValueError
    return socket.create_connection((host, port), timeout=_remaining(deadline))


def _send(stream, data, deadline):
    stream.settimeout(_remaining(deadline))
    stream.sendall(data)


def _read(stream, deadline):
    data = bytearray()
    while len(data) < 4096:
        stream.settimeout(_remaining(deadline))
        chunk = stream.recv(4096-len(data))
        if not chunk:
            if data.endswith(b'\0') and data.count(0) == 1:
                return bytes(data[:-1])
            raise ValueError
        data.extend(chunk)
    raise ValueError


def scan_bytes(data):
    digest = hashlib.sha256(data).hexdigest() if isinstance(data, bytes) else ''
    unavailable = Verdict('unavailable', digest)
    if not enabled() or not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES:
        return unavailable
    try:
        # Reject incomplete deployment attestations before transferring any file.
        if (not settings.CLAMD_HOST_UTC_CONFIRMED or settings.CLAMD_LIMITS_REVIEW != LIMITS_REVIEW
                or not settings.CLAMD_ALLOWED_ENGINE_VERSIONS):
            return unavailable
        deadline = time.monotonic()+10  # One overall deadline for both connections/all chunks.
        with _connect(deadline) as stream:
            _send(stream, b'zVERSIONCOMMANDS\0', deadline)
            reply = _read(stream, deadline).decode('ascii')
        version, separator, commands = reply.partition('| COMMANDS:')
        version = version.strip()
        if not separator or 'INSTREAM' not in commands.split() or not version_current(version):
            return unavailable
        with _connect(deadline) as stream:
            if not enabled():
                return unavailable
            _send(stream, b'zINSTREAM\0', deadline)
            for offset in range(0, len(data), 65536):
                chunk = data[offset:offset+65536]
                _send(stream, struct.pack('!I', len(chunk))+chunk, deadline)
            _send(stream, b'\0\0\0\0', deadline)
            reply = _read(stream, deadline)
        if not version_current(version):
            return unavailable
        if reply == b'stream: OK':
            return Verdict('clean', digest, version)
        if (reply.startswith(b'stream: ') and reply.endswith(b' FOUND')
                and not reply.startswith((b'stream: Heuristics.Limits.', b'stream: Heuristics.Encrypted.'))):
            return Verdict('infected', digest, version)
    except (OSError, ValueError, AttributeError, TypeError):
        pass  # Never log raw daemon replies, private bytes or paths; never retry.
    return unavailable


def require_clean(data):
    result = scan_bytes(data)
    if result.state == 'infected':
        raise ValidationError('The upload was rejected by malware scanning.')
    if result.state != 'clean':
        raise ScanUnavailable()
    return result
