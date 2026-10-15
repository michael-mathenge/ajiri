# Sprint 3 release review and activation gates

Prepared on 15 October 2026 from remote main 1ef6159, branch
codex/sprint3-release-review. This contains only the shared-cache follow-up and
Sprint 3 evidence. No push, PR merge or production deployment is implied.

## Review change

Optional THROTTLE_CACHE_DIR selects a dedicated built-in FileBasedCache for
endpoint counters. Default caching and local behaviour remain unchanged.
Separate-process tests prove sequential workers consume the same budget.
Rates remain approximate under concurrent updates; do not use as an atomic quota.
No migrations, dependency changes, auth/cookie/CORS/ingestion or CI changes.
The existing frontend package matches the freshly built dist byte for byte.

## Required release sequence

1. Michael explicitly authorizes a push and PR for this branch; current AGENTS
   requires authorization for those exact GitHub actions. Michael reviews and
   merges only after frontend and Python 3.12/3.13/3.14 CI pass. No agent merge.
2. Record the resulting reviewed main SHA; do not deploy the local branch tip or
   silently substitute a newer revision. Reconfirm clean server checkout and retain
   current production SHA 2d5d175 for rollback.
3. Reconfirm the backup window: verified manual-20261015-181545 snapshot and restore
   rehearsal exist, but any subsequent writes require a fresh backup before cutover.
   Pause writers using the existing maintenance procedure. No credential files in chat.
4. Stage the approved code with no traffic activation, run check and migrate --plan.
   No new migration is expected from this change. Stop on an unexpected plan.
   Complete the approved migrations before reloading new code.
5. Create /home/Mathenge/ajiri-throttle-cache as a dedicated private 0700 directory,
   owned by the web-app account, outside repository/media/static/backup mappings.
   Confirm shared filesystem visibility and writable access for all actual workers.
   Set THROTTLE_CACHE_DIR to that directory privately; no new credentials required.
6. Resolve the HTTPS scheme gate below before enabling Django redirect/HSTS.
   Retain host Force HTTPS throughout. If unresolved, do not activate redirect defaults;
   explicitly retain SECURE_SSL_REDIRECT=False and SECURE_HSTS_SECONDS=0.
7. After scheme verification, enable redirect and HSTS max-age 300, with no preload
   or includeSubDomains; retain secure cookies and standard headers. Reload only
   after all preceding gates pass. Verify no HTTPS loop, forged-proto behaviour,
   private URLs blocked, owner downloads and one normal ingestion run. No live
   password guessing or quota-exhaustion tests.

## HTTPS scheme gate

Django normally derives scheme from WSGI `wsgi.url_scheme`; if the host supplies it
correctly, no forwarded-header trust override is needed. If a proxy header is used,
its sanitation/overwrite guarantee must be established first. Synthetic local
RequestFactory tests cannot prove the live host contract. Do not set arbitrary
client headers as proof, or add a public diagnostic endpoint exposing request data.

Michael can send this focused question to PythonAnywhere support (not sent by Codex):

> For my free-tier Django web app with Force HTTPS enabled, does your WSGI layer
> supply wsgi.url_scheme=https on external HTTPS requests? If X-Forwarded-Proto is
> needed instead, do your proxies strip/overwrite all client-supplied occurrences,
> including comma-separated values? Can external callers bypass that proxy? What
> worker/shared-filesystem guarantees apply to a private file cache under my home?

Use the confirmed native scheme where available. Otherwise choose proxy trust only
after assurance and adversarial HTTPS/HTTP header tests. For IP throttles, the host
guarantees only the rightmost X-Forwarded-For peer; confirm whether a separate CDN
or proxy exists before selecting NUM_PROXIES. Do not expose client addresses in logs.

Sources: https://docs.djangoproject.com/en/6.1/ref/settings/#secure-proxy-ssl-header
and https://help.pythonanywhere.com/pages/WebAppClientIPAddresses/ .

## Rollback

Keep Force HTTPS and private media mappings intact. If redirects loop, set Django
redirect=False and HSTS=0 through the existing private configuration, restore the
previous verified proxy-trust configuration/reviewed revision, then reload. Existing
300-second HSTS policies may persist until expiry; HTTPS must remain available.
Unsetting THROTTLE_CACHE_DIR restores process-local counters and resets budgets;
record reduced cross-worker protection. Do not delete cache/DB/media or restore an
old DB over new writes as a routine rollback. Preserve all backups.

## Local verification of the release-review branch

On the branch based on main 1ef6159: backend check and migration check pass;
90 tests run, 89 pass and one Windows symlink privilege skip. Frontend npm ci,
lint, 25 component tests and build pass with the merged main lockfile. System
Node 22.15 emits engine warnings for updated transitive dependencies; use a
supported runtime (Node >=22.22.2 in the 22 line, or the installed 24.19 runtime).
No dependency pin or lockfile was changed to work around this. Exact dist versus
committed frontend_build bytes matched; the committed build was not regenerated.
No production activation or new live verification is claimed by these local tests.
