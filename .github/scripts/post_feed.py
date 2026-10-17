"""Check Ajiri readiness, then submit once. Python standard library only.

see ajiri-backend/docs/CONCEPTS.md#ingestion-readiness
"""
import json
import os
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        # Never forward the ingestion credential to a redirect target.
        return None


class IngestFailure(Exception):
    pass


def configuration(base, key):
    base = base.strip().rstrip('/')
    try:
        url = urlsplit(base)
        valid = (url.scheme == 'https' and url.hostname and not url.username and
                 not url.password and not url.query and not url.fragment and
                 not url.path and url.port in (None, 443))
    except ValueError:
        valid = False
    if not valid or not key or key != key.strip() or '\r' in key or '\n' in key:
        raise IngestFailure('Configuration invalid: check AJIRI_BASE_URL (HTTPS origin only) and INGEST_API_KEY privately.')
    return base


def json_response(response):
    if response.headers.get_content_type() != 'application/json':
        raise ValueError('Not JSON')
    raw = response.read(4097)
    if len(raw) > 4096:
        raise ValueError('Response too large')
    return json.loads(raw)


def submit(base, key, feed, *, opener=None, sleep=time.sleep, report=print):
    base = configuration(base, key)
    if not feed:
        raise IngestFailure('Feed file is empty; nothing was submitted.')
    opener = opener or build_opener(NoRedirect())
    healthy = False
    reason = 'No healthy response'
    for attempt in range(3):
        try:
            # Read-only retries are safe, including temporary host 404s/reloads.
            with opener.open(Request(base + '/api/health/'), timeout=10) as response:
                if response.status == 200 and json_response(response) == {'status': 'ok'}:
                    healthy = True
                    break
                reason = f'Unexpected health HTTP {response.status}'
        except HTTPError as error:
            reason = f'Health HTTP {error.code}'
            error.close()
        except (URLError, OSError, ValueError):
            reason = 'Health network error or non-JSON response'
        if attempt < 2:
            report('Ajiri is not ready; retrying the read-only health check in 5 seconds.')
            sleep(5)
    if not healthy:
        raise IngestFailure(reason + ': Ajiri is not ready. No feed was posted. Check PythonAnywhere web-app availability, expiry and the configured hostname; do not change parser code or rotate keys on this evidence alone.')

    request = Request(base + '/api/jobs/ingest/', data=feed, method='POST',
                      headers={'X-Ingest-Key': key, 'Content-Type': 'application/xml'})
    try:
        with opener.open(request, timeout=120) as response:
            if response.status != 200:
                raise IngestFailure('Unexpected ingestion response. Outcome may be uncertain; no automatic POST retry.')
            result = json_response(response)
            fields = ('created', 'skipped', 'flagged', 'notified')
            if not isinstance(result, dict) or any(type(result.get(field)) is not int or result[field] < 0 for field in fields):
                raise ValueError('Invalid ingestion result')
            report('Ingestion succeeded: ' + ', '.join(f'{field}={result[field]}' for field in fields))
    except HTTPError as error:
        status = error.code
        error.close()
        if status == 403:
            raise IngestFailure('Ingestion HTTP 403: verify the GitHub/server key match privately. No POST retry.') from None
        if status == 404:
            raise IngestFailure('Ingestion HTTP 404 after health passed: check host routing and the deployed endpoint. No POST retry.') from None
        raise IngestFailure(f'Ingestion HTTP {status}. Outcome may be uncertain; inspect the server before a manual retry.') from None
    except (URLError, OSError, ValueError):
        raise IngestFailure('Ingestion outcome is uncertain (network or invalid response). Check server state before a manual retry; no automatic POST retry.') from None


def main():
    try:
        submit(os.environ.get('AJIRI_BASE_URL', ''), os.environ.get('INGEST_API_KEY', ''), Path('feed.xml').read_bytes())
    except (IngestFailure, OSError) as error:
        # Emit only our fixed messages; never environment values, response bodies
        # or raw network exceptions, which may contain addresses/credentials.
        message = str(error) if isinstance(error, IngestFailure) else 'Feed file unavailable; nothing was submitted.'
        print('::error::' + message, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
