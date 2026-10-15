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

Least-invasive shared-counter proposal (NOT applied): a dedicated built-in Django
FileBasedCache in a private trusted writable directory shared by all workers on the
same host/filesystem. It needs no dependency/migration, but remains approximate,
adds disk I/O and is unsuitable across nonshared hosts. Confirm platform topology
first. DatabaseCache needs a new table (ask first); Redis needs service/config approval.
No cache table, cache configuration or hosting change is part of this package.

Michael-only verification: inspect effective cache backend class without printing
cache credentials; establish whether all workers see the same storage; verify trusted
proxy count privately, then use synthetic local tests for exhaustion/reset. Never
load-test production or deliberately lock out real users. Rollback: revert reviewed
rate settings/revision and reload manually; do not change auth/CORS/ingestion keys.
