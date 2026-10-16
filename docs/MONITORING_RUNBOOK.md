# WP21 minimal health and private error events

Local implementation only; Michael owns deployment. No migration/new dependency.
GET/HEAD /api/health/ ignores stale JWT headers, checks DB reachability with SELECT 1,
returns 200 {status: ok} or generic 503 {status: unavailable}; HEAD has no body.
All responses are no-store. THROTTLE_HEALTH_RATE defaults to 60/min, uses existing
endpoint cache/IP resolution. Health does not prove migrations, data completeness,
mail delivery, ingestion freshness, backup readiness or external provider access.

The per-process log is JSON lines: UTC time, severity, fixed event category,
server-generated correlation ID, status and matched route name (never parameters).
Messages, args, exception text/tracebacks, paths, identities, headers and bodies
are deliberately excluded. X-Request-ID is generated locally, not trusted from
client input. Django 5xx/security errors use the safe handler, with no email handler.

PRIVATE_LOG_DIR: absolute private directory outside the application/public mappings;
default under the account's home as ajiri-private-logs in DEBUG=False. DEBUG=True
defaults to sanitized stderr. PRIVATE_LOG_MAX_BYTES=1048576 and
PRIVATE_LOG_BACKUP_COUNT=3 (1..10) bound each worker's rotations. Files are 0600,
directory 0700 on Linux; Windows requires account-restricted ACLs. Writer PID is in
the filename and chosen at emit time, so forked workers do not share rollovers.
Pre-create/verify the directory during Michael's approved deployment and confirm
web-account ownership and disk quota. Do not map it publicly or share with uploads.

Daily: read only safe event categories/statuses/correlation IDs, check repeated
5xx alongside the matching deployment date, inspect the latest ingestion/sweep
Actions results, and check private backup recency. Weekly: check disk/CPU quota,
web-app renewal and stale worker files. Per-process rotation does not remove files
from retired PIDs: review their sizes and approved retention manually. No deletion
policy or production cleanup is implemented here. Logs are not backed up by the
new backup command. No paid service, external tracker or new dependency.

IMPORTANT: Django console email writes content directly to platform stdout outside
this formatter. That existing console stream can still contain mail/CV data.
Restrict its access and do not paste it into chat/Jira. Sanitized application logs
are NOT a claim that all platform logs are free of personal data. Email behaviour
is unchanged until Phase B. Host access logs are also outside application formatting.

Proposed GitHub Actions change (NOT applied): retain normal nonzero exits for
ingest/sweep failures, add a short job-summary failure category with no headers,
request bodies or secrets, and document the owner's Actions failure notifications.
Review any workflow edit separately; do not change schedules or X-Ingest-Key.

Manual local checks: GET and HEAD health without login; test DB failure via the
automated suite, not by breaking production DB access. Lower a local health rate
to confirm 429/reset. Run config.test_monitoring to prove sensitive exception text
is absent and rotations stay bounded. Rollback: revert the reviewed app revision
and logging configuration together; preserve existing private logs for review.
No DB rollback, token reset or public mapping is needed.
