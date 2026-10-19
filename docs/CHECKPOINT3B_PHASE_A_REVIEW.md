# Checkpoint 3B Phase A review

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026, Africa/Nairobi. Local implementation only, based on exact reviewed
main `c4b93647f65618e8d13f9baa47ded6d22a28f0fb`. Remote main was rechecked at handback
and still resolves to that SHA. No rebasing or changes to Michael's deployment SHA.
Michael confirmed Stage A deployed/reloaded on 16 October at c4b9364: redirect=False,
HSTS=0, shared cache writing counters, weak-password rejection, login, jobs list,
profile save and no public media mapping verified by him. This is owner-reported
evidence, not an agent inspection. Stage B awaits PythonAnywhere's HTTPS scheme
answer; keep redirect/HSTS off. The Phase A branch was already completed locally
before this confirmation; its base was not changed.

## 1. Package summary

| WP | Local status | Branch | Source range | Suggested points |
|---|---|---|---|---:|
| WP16 | gates passed; existing safe pins retained | feature/dependency-advisories | f96ec68..bf9547a | 3 |
| WP18 | gates passed; paired client/server change | feature/refresh-cookie-csrf | 4db333e..1e4197a | 8 |
| WP21 | gates passed; production configuration pending | feature/health-and-logging | 021f81f..3791833 | 5 |
| WP22 | gates passed; manual operation documented | feature/backup-routine | af8f62f..e969690 | 5 |

Each package merged into integration/checkpoint-3b with --no-ff after its gates.
WP22 also includes focused WP21 follow-up 391cf94: private permissions after log
rollover and sanitized fallback on logging I/O failures. Final full gates cover it.
First commit f96ec68 changed only AGENTS time-bound sections. Final handback is docs
only. Points total 21, relative sizing rather than a promise about elapsed time.
WP17/WP19/WP20 were not invented: only the four Phase A packages were authorized.

## 2. Changes

WP16 captures production and development pip-audit results and reconciles all 15
historical advisories, original versions, current fixes and applicability. Current
pins already include Django 6.1.2/PyJWT 2.15.1. No dependency files changed.
Historical clean claims without reproducible evidence remain unverified; advisory
matching does not establish exploitability. Primary advisory discrepancies and the
finding without a published fixed event are explicitly recorded.

WP18 adds GET /api/accounts/csrf/ with a masked Django token and no-store response.
Login, refresh and logout require a valid Django token and exact trusted Origin
before side effects. Stable csrf_failed JSON 403 responses enable one bounded
bootstrap/retry. Existing axios client bootstraps, renews after login, and shares
simultaneous silent refreshes. Refresh 401 still invalidates a session; CSRF 403,
429 and network failure do not erase an otherwise valid session. JWT lifetimes,
rotation/blacklisting and HttpOnly refresh-token storage remain unchanged.
Existing sessions bootstrap normally; old tabs may need a reload. No runtime
CSRF-disable switch. The committed frontend_build was regenerated once, as WP18's
last package commit; later builds were verification only.

WP21 adds unauthenticated GET/HEAD /api/health/ using SELECT 1, generic ok/unavailable
JSON, empty HEAD body and non-cacheable responses. Resolved-IP throttle defaults to
60/minute using the existing throttle cache. Sanitized JSON errors contain only
timestamp, severity, category, generated correlation ID, status and route name.
Private per-process files rotate at 1 MiB with three retained rotations by default.
Failure fallback also excludes original exception/message contents. Stale process
files need manual quota review. Console email remains unchanged and can still put
mail content into platform console logs; these are separate from sanitized files.

WP22 adds backup_private_data: required private destination, dry-run, SQLite backup
API, integrity checks, unique private directories, optional media, checksums and a
completion manifest published only after success. Media requires a declared paused
writer window and inventory consistency check. Unsafe paths/links and credential
files are rejected. Thirty-day retention is DRAFT and report-only: no automatic
deletion or pruning flag. Interrupted copies remain private/incomplete. The runbook
covers manual free-tier operation, conditional scheduling and isolated restore.

MIGRATION_DESIGN_3B1.md proposes Profile verification fields and delivery attempt/
budget tables, token alternatives, defaults, constraints, concurrency, old-row
impact, mixed-version compatibility and rollback. No fields/migrations added.

## 3. Actual verification

Python 3.12.6; isolated environment installed existing pinned requirements.
Supported Node 24.19.0 invoked explicitly (Windows npm.cmd otherwise selected an
older Node). Existing tools only; no project dependency additions. Test mail uses
Django's in-memory backend; no real SMTP or production data involved.

| Package | Full backend suite | Frontend component tests | Other gates |
|---|---|---|---|
| WP16 | 90 run: 89 passed, 1 skipped | 25 passed | all passed |
| WP18 | 94 run: 93 passed, 1 skipped | 32 passed | all passed |
| WP21 | 99 run: 98 passed, 1 skipped | 32 passed | all passed |
| WP22 / final code | 111 run: 110 passed, 1 skipped | 32 passed | all passed |

Every package ran pip check, manage.py check, makemigrations --check --dry-run,
full Django tests, locked npm ci, lint, component tests and build. Production-like
check --deploy used dummy settings: only intentional W005/W021 remain because
HSTS includeSubDomains/preload are disabled. No warning suppression. Dependency
scans returned no known vulnerabilities for both requirement files; exact outputs
and scanner version are retained in DEPENDENCY_ADVISORIES.md and audit-evidence/.

Final targeted backup/monitoring run: 17 passed. Initial backup tests exposed
SQLite handles remaining open on Windows; explicit connection closing fixed this
before the passing full suite. The one backend skip is Windows symlink privilege
coverage; Linux CI must exercise it after a separately authorized push. No CI run
or production verification is implied. Coverage/E2E/accessibility were not rerun.
Final frontend main bundle: 415.26 kB, gzip 134.63 kB (Vite output).

## 4. Manual review script — local first

Use the isolated checkout without switching Michael's dirty original checkout:

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test --noinput
```

Expected: no system issues/schema changes; 111 tests run, one Windows skip. Inspect
accounts/test_csrf.py and frontend src/test/csrf-client.test.js for origin rejection,
cookie/token rotation, existing sessions and bounded/concurrent recovery checks.
The strict backend CSRF tests enforce checks; ordinary Django test-client exemption
is not a production bypass.

For an already running LOCAL server (do not start one against production data):

```powershell
curl.exe -i http://localhost:8000/api/health/
curl.exe -I http://localhost:8000/api/health/
curl.exe -i http://localhost:8000/api/accounts/csrf/
curl.exe -i -X POST http://localhost:8000/api/accounts/refresh/ -H "Origin: http://localhost:5173" -H "Content-Type: application/json" --data '{}'
```

Expected: health 200 minimal status JSON; HEAD no body; CSRF bootstrap no-store
and CSRF cookie; tokenless refresh 403 with code csrf_failed. Do not paste token/
cookie output into chat. In a browser with a disposable local account, log in,
reload, trigger concurrent authenticated requests after access expiry, and log out.
Expect one silent refresh and retained login after temporary network/429 failures.

Read BACKUP_ROUTINE.md before invoking a backup: dry-run first, private destination
outside repo/media, never use real media mode without pausing all writers. Rehearse
hash/integrity checks and restore into a NEW isolated folder. This phase did not
copy production personal data or execute any live backup.

After a separate future deployment approval, Michael verifies origin/scheme behind
the trusted proxy, private log folder access/permissions, health/429, owner downloads,
blocked direct private URLs and a normal ingestion run. Follow MONITORING_RUNBOOK.md
and the existing deployment checklist; do not change the pinned 3A rollout now.

## 5. Rollback, limits and decisions

- Roll back reviewed WP18 client/server/build together. Reload old tabs; never
  disable CSRF on the server to accommodate a stale client.
- Health is not evidence of mail delivery or ingestion freshness. Existing DRF
  shared file-cache limits remain approximate rather than atomic mail quotas.
- Safe application error events do not sanitize separate platform access/console
  logs. Per-process rotations multiply disk usage; review stale worker files.
- Backup writer assertion cannot itself stop writers. Disk exhaustion can leave
  partial snapshots; retention never frees space automatically. Backup credentials
  are deliberately excluded, so this is not a complete machine/configuration image.
- No real SMTP, password reset, verification, consent or rights features implemented.
  Approve exact migration design, token expiry/revocation behavior, global delivery
  cap/allocation, metadata retention and unverified-account restrictions first.
- Future 3B rollout and Stage B HTTPS verification stay Michael-owned. Stage A
  success is owner-confirmed as above. See PHASE_A_DEPLOYMENT.md for exact server
  steps, requirements installation/version checks and rollback.
  No pushes, main merges, connector writes or production operations performed.

## 6. Git and review gate

Original lockfile/coverage changes, old stash and Git configuration were preserved.
All new author/committer identities were checked against the configured noreply
address using git log over c4b9364..integration/checkpoint-3b. No identity changed.
Inspect the final commit with the same command after handback.

```powershell
git log --format="%h %ae | %ce" c4b9364..integration/checkpoint-3b
```

STOP for Michael's migration-design review. Phase B requires a separate prompt.

## 7. Queued follow-ups — not started

- No-skills job cards: replace misleading 0% match with an add-skills prompt.
- Registration error-message styling.
- New-account job-alert checkboxes default off.

These remain later work, outside Phase A. No implementation was made.
