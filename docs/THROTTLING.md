# Checkpoint 3A request throttling

Defaults: THROTTLE_LOGIN_RATE=10/min, THROTTLE_REGISTER_RATE=5/hour,
THROTTLE_REFRESH_RATE=60/min, THROTTLE_APPLY_RATE=20/hour,
THROTTLE_SEND_RATE=10/hour. Environment overrides use DRF rate syntax; invalid
rates fail configuration, never silently disable protection. These are request
limits, not accepted-email daily caps. No reset/password API exists; future ones
must explicitly attach an appropriate scope. Admin uses Django's password forms.

Apply/send key by authenticated user; login/register/refresh key by resolved IP.
Shared NAT users can share public quotas. Frontend reports 429 and Retry-After,
without automatically repeating mutations. Registration still shows all field errors.

## Proxy and cache boundary

Current repository has no CACHES override: Django uses LocMemCache, per-process,
not shared. Actual live worker count/cache environment is UNVERIFIED (no production
inspection authorized). DRF read/modify/write counters are approximate even with a
shared cache and are not a brute-force/DDoS or strict email-quota solution.

DRF_NUM_PROXIES defaults to 0, using REMOTE_ADDR and ignoring forwarded headers.
Michael must verify PythonAnywhere's trusted hop count/header sanitation before
setting a positive count; never take an arbitrary client-provided leftmost IP.
PythonAnywhere documents forwarded client headers but not a universal DRF hop count:
https://help.pythonanywhere.com/pages/WebAppClientIPAddresses
Tests cover 0 and 1 hops and malicious prefixes. With 0 behind a proxy, public users
may share a quota, so verification is a deployment prerequisite.

Approved Sprint 3 follow-up: optional built-in FileBasedCache, selected only when
THROTTLE_CACHE_DIR is supplied. It uses a dedicated `throttle` alias; other caching
retains its default. Unset keeps existing development/test LocMemCache behaviour.
Absolute paths outside the backend application tree are required. Independent
subprocess tests prove one worker's request consumes another worker's budget.
Existing expiry/reset and ingestion-exclusion tests still apply. No production
activation, hosting change, dependency or migration has been performed.

This remains approximate: concurrent read/modify/write can lose increments; eviction
at 10,000 entries can reset some counters. It is not an atomic quota or a defence
against large-scale distributed abuse. It works only if all workers use the same
trusted filesystem and directory. Confirm topology before activation. Cache files
are pickled: never allow uploads or untrusted writes into the cache directory.

Michael-only activation, after backup/review and confirming worker topology:
create a dedicated private directory outside every static/media mapping (0700,
owned by the web-app account). Configure THROTTLE_CACHE_DIR privately to that absolute
directory, verify writable access from all workers, then activate the reviewed code.
Do not put it in uploaded media, frontend_build, staticfiles or backups; do not use
chmod 777. Verify counter sharing with synthetic local subprocess tests before
activation, not by exhausting live logins. Django file-cache entries use 0600 on
creation; preserve private directory ownership. Roll back by unsetting the variable
and reloading the prior reviewed configuration; this resets counters and returns to
process-local limits. No database rollback is required. Never delete an arbitrary
directory as part of rollback. DatabaseCache/Redis remain separate proposals.

Michael-only verification: inspect effective cache backend class without printing
cache credentials; establish whether all workers see the same storage; verify trusted
proxy count privately, then use synthetic local tests for exhaustion/reset. Never
load-test production or deliberately lock out real users. Rollback: revert reviewed
rate settings/revision and reload manually; do not change auth/CORS/ingestion keys.
