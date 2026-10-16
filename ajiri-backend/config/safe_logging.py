"""Allowlisted diagnostics: never format arbitrary log messages or exceptions."""
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
from datetime import datetime, timezone
import uuid
import sys


class SafeJSONFormatter(logging.Formatter):
    # see docs/CONCEPTS.md#sanitized-error-logging
    def format(self, record):
        request = getattr(record, 'request', None)
        correlation = getattr(request, '_ajiri_correlation_id', None)
        match = getattr(request, 'resolver_match', None)
        route = getattr(match, 'url_name', None)
        status = getattr(record, 'status_code', 500)
        return json.dumps({
            'timestamp': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            'severity': 'ERROR' if record.levelno >= logging.ERROR else 'WARNING',
            'event': 'security_error' if record.name.startswith('django.security') else 'application_error',
            'correlation_id': correlation if isinstance(correlation, str) and re.fullmatch(r'[0-9a-f]{32}', correlation) else None,
            'status': status if type(status) is int and 100 <= status <= 599 else 500,
            'route': route if isinstance(route, str) and re.fullmatch(r'[A-Za-z0-9_:-]{1,64}', route) else None,
        })


class _PrivateRotatingFileHandler(RotatingFileHandler):
    def _open(self):
        # Rollover creates a fresh file too; preserve 0600 rather than OS umask.
        fd = os.open(self.baseFilename, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        return os.fdopen(fd, self.mode, encoding=self.encoding)

    def handleError(self, record):
        # logging's default failure report dumps raw message/args/exception text.
        sys.stderr.write(SafeJSONFormatter().format(record) + '\n')


class PrivateProcessRotatingHandler(logging.Handler):
    """Each process owns a rotating file; never race workers on one rollover."""
    def __init__(self, directory, max_bytes=1048576, backup_count=3):
        super().__init__()
        self.directory = Path(directory)
        self.max_bytes, self.backup_count = max_bytes, backup_count
        self._writer = None
        self._pid = None

    def emit(self, record):
        try:
            self._write(record)
        except (OSError, ValueError):
            sys.stderr.write(SafeJSONFormatter().format(record) + '\n')

    def _write(self, record):
        pid = os.getpid()
        if self._pid != pid:
            if self._writer:
                self._writer.close()
            self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            if self.directory.is_symlink():
                raise ValueError('Log directory must be private, not a symlink.')
            if os.name != 'nt' and (self.directory.stat().st_mode & 0o077 or self.directory.stat().st_uid != os.getuid()):
                raise ValueError('Log directory permissions must be private to its owner.')
            path = self.directory / f'errors-{pid}.jsonl'
            if path.is_symlink():
                raise ValueError('Log file must not be a symlink.')
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            os.close(fd)
            self._writer = _PrivateRotatingFileHandler(path, maxBytes=self.max_bytes,
                                               backupCount=self.backup_count, encoding='utf-8', delay=True)
            self._writer.setFormatter(SafeJSONFormatter())
            self._pid = pid
        self._writer.emit(record)

    def close(self):
        if self._writer:
            self._writer.close()
        super().close()


class CorrelationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate locally; never trust a client correlation header or log paths.
        request._ajiri_correlation_id = uuid.uuid4().hex
        response = self.get_response(request)
        response['X-Request-ID'] = request._ajiri_correlation_id
        # Django's request logger records 5xx responses once, through our safe handler.
        return response
