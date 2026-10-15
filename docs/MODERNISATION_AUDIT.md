# Modernisation audit — read-only

15 October 2026; source revision `24a0ae2` on integration/checkpoint-3. No application,
configuration, dependency, CI or production changes made. Status is **OK**, **gap**,
or **unknown**; **UNVERIFIED** means a claim could not be established. Effort uses
rough story points (SP), not a delivery promise. Evidence is repository-relative.
This is an engineering audit, not legal advice; privacy proposals are DRAFT for legal review.

## Command evidence and limits

- Backend `.venv` Python: `manage.py check --deploy` with DEBUG=False, audit.invalid
  allowed/trusted host, in-memory mail and explicitly dummy audit keys; dotenv loading
  disabled. Result: **security.W004 (HSTS), security.W008 (SSL redirect)**, no other
  deploy warnings. This does not verify the hosting proxy or actual production headers.
- Read-only serializer probes: common/numeric dummy password passes RegisterSerializer;
  configured validate_password rejects it with two errors. Nine non-PDF bytes named
  audit.pdf pass validate_cv_file. No user/file created by these probes.
- `python -m pip check`: **No broken requirements found**. `pip show pip-audit coverage`:
  both absent. No tools installed. Python vulnerability result **UNVERIFIED**;
  backend/frontend coverage **unmeasured** (Vitest coverage providers also absent).
- Initial restricted-network npm query failed DNS; retry with network access succeeded.
  `npm audit --json --fetch-retries=0 --fetch-timeout=20000`: **0 vulnerabilities**, 247
  dependency entries reported. This is a registry advisory snapshot, not proof of safety.
- `npm outdated --json --fetch-retries=0 --fetch-timeout=20000` returned 8 outdated
  direct packages (exit 1 indicates outdated entries). `pip list --outdated --format=json`
  returned 16 outdated installed packages. Exact examples below; no upgrades performed.
- No full test suite, fresh build, coverage, E2E, accessibility scanner, load test,
  production probe, backup restore or live header inspection performed this round.

Read-only reproduction for deploy checks (PowerShell, disposable process environment;
all key material below is deliberately non-secret, not production configuration):

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'False'
$env:SECRET_KEY = ('audit-dummy-not-a-real-key-' * 4)
$env:INGEST_API_KEY = 'audit-dummy-not-real'
$env:ALLOWED_HOSTS = 'audit.invalid'
$env:CSRF_TRUSTED_ORIGINS = 'https://audit.invalid'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check --deploy
```

Historical findings below describe the original audit revision; the final Checkpoint 3A
remediation status section is authoritative for local fixes and remaining limits.

## 1. Security

| Status / evidence | Risk | Suggested fix / effort |
|---|---|---|
| **gap**: settings.py effective SECURE_HSTS_SECONDS=0, SECURE_SSL_REDIRECT=False; W004/W008 | Downgrade protection depends on hosting | Michael verifies proxy HTTPS recognition/redirect first; staged short HSTS, no preload/subdomains initially. Avoid redirect loops. 2 SP |
| **OK (local config)**: DEBUG=False default; missing key fails outside DEBUG; ALLOWED_HOSTS parsed from env; prod secure session/CSRF/refresh cookies true | Actual production env **UNVERIFIED**; empty hosts reject access; wildcard/insecure key not explicitly rejected | Validate prod configuration without exposing values; preserve local fallback. 1 SP |
| **OK / gap**: SecurityMiddleware + frame middleware; effective nosniff=True, DENY, same-origin referrer policy. No explicit CSP or Permissions-Policy in project | XSS can expose localStorage access token; inline theme script complicates CSP. Live headers **UNVERIFIED** | Test headers and CSP report-only plan; retain auth client pending approved design. 3 SP |
| **gap**: accounts/views.py refresh reads httpOnly Secure/Lax cookie; APIView.as_view is csrf_exempt=True; JWT-only authentication provides no CSRF check; no explicit Origin enforcement | SameSite reduces cross-site cookie sending but is not a complete policy for same-site origins; CORS is not CSRF. No exploit demonstrated | Explicit CSRF/origin design for login/refresh, local-dev compatibility and adversarial tests. Protected auth changes need approval. 3 SP |
| **gap**: REST_FRAMEWORK has no default throttles; no view throttle classes found | Login guessing, registration abuse, document-generation and email resource exhaustion | Per-endpoint abuse controls and durable email budgets; trust proxy/IP only with verified configuration. 3–5 SP |
| **gap**: RegisterSerializer only min_length=8; create_user bypasses configured validators (probe confirmed) | Common/numeric/similar passwords accepted | Call Django password validation with candidate user; field errors and regression tests. 2 SP |
| **gap**: profiles/serializers.py validates extension and 5 MB only, no content sniffing | Disguised/unsafe files; private storage protects access, not file safety | Signature/container checks for PDF/DOC/DOCX, ZIP expansion limits and reject malformed inputs; signatures are not malware scanning. 3 SP |
| **OK (source)**: config/urls.py excludes /media; private permissions 0600/0700; owner download tests exist | Hosting mappings can bypass Django; current mappings **UNVERIFIED this round** | Keep manual privacy checks and private mappings in deployment acceptance. 1 SP |

Source context: [Django password validation](https://docs.djangoproject.com/en/4.2/topics/auth/passwords/)
explains model-level create_user does not apply validators; installed-code probes above
establish this repo's behaviour. [DRF CSRF guidance](https://www.django-rest-framework.org/topics/ajax-csrf-cors/)
distinguishes cookie/session requests from other authentication.

## 2. Auth and accounts

**gap.** accounts/urls.py only register/login/refresh/logout; no reset, verification,
export/deletion or consent endpoints/model fields. Tests cover rotation, replay,
expiry, logout and inactive login. Reset/verification policy and anti-enumeration
need design (5–8 SP); rights workflow belongs WP14 (8 SP). Block real employer email
until mailbox control is verified or explicitly restrict it to an owner-only pilot.

**gap / unknown.** Custom RefreshView validates token but does not look up current user
activity before issuing/rotating. An inactive account may continue refreshing until
expiry; protected JWT authentication checks user activity separately. No disabled-user
refresh regression found. Stop-issue/revoke policy, password-reset revocation and
concurrent refresh handling need tests/design; no exploit test run (3 SP). Client stores
access token in localStorage and refreshes each failed request separately; concurrent
refresh races and XSS exposure warrant targeted tests before changing protected auth.

## 3. Dependencies

**OK / gap.** package-lock.json supports npm ci; requirements-prod.txt pins versions
and requirements.txt includes runtime plus stubs. Python requirements are not a
hash-locked resolver output. pip check passes; npm advisory scan is clean today.

Outdated snapshot: React/ReactDOM 19.2.8 -> 19.3.1; Vite 8.2.2 -> 8.3.4;
react-router-dom 7.18.3 -> 7.18.4; oxlint 1.80.0 -> 1.88.0; plugin-react 6.1.1 -> 6.1.2;
React type packages -> 19.3.0. Python: Django 6.1 -> 6.1.2, DRF 3.18.0 -> 3.18.3,
PyJWT 2.13.0 -> 2.15.1, lxml 6.1.2 -> 6.1.3; other outdated entries are largely
Celery tooling, stubs, timezone data and pip. Outdated does not mean vulnerable.
Risk: stale patches and transitive drift. Recommend reviewed patch maintenance,
separate upgrades and future Python lock/hash decision (2–3 SP).

**unknown — UNVERIFIED Python vulnerabilities.** pip-audit not installed; do not infer
security from pip check or outdated. Michael can run the following **after separately
approving/providing pip-audit**, not as an implicit install instruction:

```powershell
cd C:\dev\ajiri\ajiri-backend
.\.venv\Scripts\python.exe -m pip_audit -r requirements-prod.txt
.\.venv\Scripts\python.exe -m pip list --outdated --format=json
cd ..\ajiri-frontend
npm audit --json
npm outdated --json
```

No audit package was installed. Vulnerability triage is a P0 verification gate; any
actual fixes depend on findings, not a blanket major-version upgrade.

## 4. Testing

**OK / gap.** Backend accounts/tests.py, jobs/test_{lifecycle,preferences,private_media,
send_concurrency}.py and profiles/test_cv.py cover core permissions/lifecycle. Frontend
src/test contains login/flows/profile/subscriptions tests; CI runs Django tests on
3.12–3.14 and Vitest. Historical counts in checkpoint reports are not a new test result.

**unknown — UNVERIFIED** line/branch coverage: coverage and both Vitest coverage
providers absent; no new dependencies installed. No Playwright/Cypress/axe dependency
or E2E/a11y CI job found. Risks: no real-browser auth/CSRF/keyboard regression gate,
no coverage of missing security controls/reset/verification. Recommend targeted P0
regressions first, then local browser smoke/keyboard checks; approve tools separately
before coverage/E2E automation (3–5 SP). No coverage percentage claimed.

## 5. Frontend

| Status / evidence | Risk | Suggested fix / effort |
|---|---|---|
| **OK / gap**: hooks/useApiResource aborts obsolete fetches; axios shared client; no shared response cache | Refetch on remount, repeated requests on mobile | Measure first; bounded in-memory deduplication, avoid persistent private-data cache. 2 SP |
| **OK / gap**: Register native constraints + all field-keyed errors; Profile extension/size validation; server lacks password/content checks | UI validation can be bypassed | Enforce server checks first, mirror helpful errors. Included security effort |
| **OK (measurement)**: committed assets total 438,431 raw bytes; main JS 384,921 raw / 123,952 gzip; CSS 19,312 / 5,211 gzip; App.jsx lazy routes | Main bundle/mobile cost; synthetic gzip is not live transfer size | Keep split routes, measure production compression and choose budget before new dependencies. 1–2 SP |
| **OK / unknown**: labels, aria-invalid, skip link and route focus in AppShell; Radix controls | Contrast, touch targets, keyboard and screen-reader completion **UNVERIFIED** | Manual mobile/keyboard review, then approved automated checks. 2 SP |
| **gap**: no service worker/offline manifest found | No offline shell; offline CV storage could create privacy risk | Defer PWA; never cache private documents/tokens. 3 SP if later approved |
| **OK / gap**: index.html has title/description/lang/viewport; no route-specific SEO/schema | Shared SPA metadata, authenticated jobs not searchable | Product decides public discovery before SSR/public-job work. 2–5 SP |

## 6. API

**OK:** settings.py sets page-number pagination (20); jobs/filters.py supports title,
location, type and skill. Owner scoping is explicit for applications/notifications.
**gap:** no OpenAPI/schema route/config or versioning policy found. Errors mix DRF
field arrays, detail strings and non-JSON infrastructure failures; frontend lib/errors.js
normalizes form errors. Risk: integration drift and inconsistent clients. Recommend
an explicit documented contract first, schema tooling only with dependency approval;
keep /api compatible, no gratuitous /v2 migration (2–3 SP). Schema generation and
end-to-end error consistency **UNVERIFIED**.

## 7. Operations

**OK / gap:** docs/DEPLOYMENT_CHECKLIST.md covers private SQLite/media backups,
restore rehearsal, staged migration-before-reload and rollback. Actual current backup
schedule, off-host copy, restore result and retention **UNVERIFIED**. No automated
backup/restore deployment system observed. Define manual recovery ownership first (2 SP).

**gap:** no project LOGGING/error tracker/health route; Django/platform defaults remain.
Console backend can log CV-bearing mail and report a false successful send. WP15 needs
sanitized events, health and a manual Actions/quota/renewal routine (3 SP). Production
log access/rotation/retention **UNVERIFIED**. Don't add a paid service.

**OK / gap:** tracked ajiri-backend/.env.example lists development/production setup,
but future SMTP quota/disable settings do not yet exist; keep examples value-free for
secrets and review stale deployment descriptions. No secret files read for this audit.

**OK / gap:** .gitattributes scopes LF to build-sensitive files; committed frontend_build
and CI's exact diff guard exist. scripts/build_frontend.ps1 is under ajiri-backend/,
normalizes HTML, but uses npm install instead of npm ci and replaces target tree.
Fresh build consistency **UNVERIFIED this round**; don't regenerate in docs-only work.
Recommend later reproducible packaging review and line-ending policy check (1–2 SP).

## 8. Performance

**gap (static evidence):** jobs/views.py JobList queryset lacks prefetch; JobListSerializer
calls calculate_match_score per job, which issues values_list for profile/job skills.
Application/Notification lists dereference job fields without select_related. Recommend
query-count regression tests and bulk skill sets/select_related (3 SP). Actual query
counts and latency **UNVERIFIED**, no production/load probe.

**OK / gap:** unique source_url and unique user/job pairs provide indexes/duplicate guards;
FK indexes exist. No explicit composite indexes for active/scam/posted ordering or
user/status/date in jobs/models.py. Choose indexes from EXPLAIN and representative
fixtures, not assumptions (2 SP; additive migration later).

**gap:** matching.py sweep loops all active jobs x all profiles with repeated skill
queries and synchronous mail. ingestion.py does per-entry exists/create/scam/match work;
views.py parses the whole body. SQLite has one writer, 20s lock timeout; feed body cap
10 MB. No chunking, request time budget or cache; inactive profiles are not excluded
from the matching iteration. Large fan-out risks worker timeout/partial completion.
Concurrent draft creation also does check-then-save around file writes: uniqueness
blocks duplicate rows but may leave orphan files/500s (not reproduced).
Recommend bounded query counts, inactive-user exclusion, explicit budgets and chunked
work proposal before scaling; ingestion changes require separate approval (5–8 SP).
No claim that today's small deployment exceeds capacity.

## Priorities

### P0 — before opening to real users / real employer mail

- Enforce configured password validators and content-aware upload validation.
- Approve and test CSRF/origin protection and auth/resource abuse limits; disabled-user
  refresh/sweep behaviour must be reviewed and covered. No auth change authorized yet.
- Resolve false email success/log exposure: gate real sending until verified mailbox,
  provider/sender approval, quotas and controlled owner-inbox rollout are ready.
- Legal-review privacy/consent and functioning rights-request contact/process; decide
  retention and backup access. DRAFT only, not a legal compliance certification.
- Michael verifies HTTPS redirect/proxy/cookies/headers and rehearsed private backups;
  stage HSTS only after HTTPS is known safe. Confirm renewal owner.
- Complete Python advisory scan/triage; no known Python vulnerability asserted here.

### P1

Password reset + verification UX, export/deletion fulfilment, monitoring/health,
accurate alert retries, query-count fixes, draft-creation race tests, patch maintenance,
CSP design and targeted browser/accessibility regressions. Some account controls are
also prerequisites of real sending, even if broader UX follows later.

### P2

Caching after measurement, schema/versioning formalization, broader coverage/E2E tooling,
index/load tuning, deterministic packaging cleanup, optional SEO/PWA after product review.
Production fixture cleanup remains a separately authorized housekeeping task.

## Checkpoint 3A remediation status (local only)

- WP11 password bypass: fixed in registration field validation and manager creation;
  custom-user admin forms use Django policy. Existing passwords/login unchanged.
  Other historical findings remain open until listed here with executed checks.

- WP12 absent throttling: scoped request limits implemented for five endpoints;
  proxy parsing tested. Shared-worker counters remain OPEN (LocMemCache), as do
  durable email quotas. Live proxy/cache topology remains UNVERIFIED; see THROTTLING.md.

- WP13 extension-only uploads: fixed with bounded PDF/DOC/DOCX structural checks,
  5 MB ceiling and UUID stored names. Full parsing and malware scanning remain OPEN;
  signature checks cannot certify files safe. Existing stored files are unchanged.

- WP14 W004/W008: addressed by DEBUG=False defaults and env-configurable profile
  (HSTS 300s, SSL redirect), with proxy/no-loop tests. Session/CSRF secure flags and
  standard headers configurable. Actual production remains UNVERIFIED. HSTS broader
  scope/preload advisories W005/W021 are deliberately retained, not silenced.

- WP15 refresh CSRF: design completed in REFRESH_COOKIE_CSRF_DESIGN.md; implementation
  remains OPEN, as authorized. No SameSite/origin/token validation changes were made.

### Remaining open after Checkpoint 3A

CSRF implementation; inactive-user refresh/alerts; shared-cache/atomic abuse protection;
durable mail quotas, real SMTP and truthful alert receipt handling; password reset and
mailbox verification; privacy/legal/consent and account rights; malware scanning/full
render validation; live proxy/header/cache verification and backups/renewal; Python
advisory scan, coverage/E2E/a11y, dependency patches; CSP/Permissions-Policy; query-count,
scaling/index/caching work; API schema/versioning, SEO/PWA and packaging cleanup.
None is silently declared fixed by a deploy check or a passing local suite.

## Sprint 3 AJ-14 evidence — 15 October 2026

Supersedes the original audit's UNVERIFIED Python scan and unmeasured backend
coverage only. Tested source 5e15a11 in an isolated local checkout. Existing tools:
pip-audit 2.10.1, coverage 7.16.2, Python 3.12. No dependency changes or installs.

`python -m pip_audit -r requirements-prod.txt --progress-spinner off` completed
with exit 1: **15 known vulnerabilities in two packages**, Django 6.1 and PyJWT
2.13.0. Django: PYSEC-2026-3717 (reported fixes 5.2.17/6.0.8/6.1.1).
PyJWT: PYSEC-2026-4140 through PYSEC-2026-4152 inclusive, and PYSEC-2026-4183.
The scanner reports 2.14.0 or 2.15.0 fixes for most PyJWT findings, but lists no
fix version for PYSEC-2026-4146. Do not assume upgrading alone clears every finding.
These are advisory matches, not demonstrated exploits or a production inventory.
Triage and compatible patch upgrades require a separate reviewed dependency task;
**P0 release risk remains open**. No ignore flags, audit fixes or dependency edits.

Fresh full suite: 88 run, 87 passed, one Windows symlink privilege skip.
`manage.py check` passed; `makemigrations --check --dry-run` found no changes.
Statement coverage: **90% (1182 statements, 121 missed)** excluding tests,
migrations and upload fixtures. Unfiltered total was 94%, inflated by tests.
No branch, frontend, E2E or production coverage measured. Notable gaps: tasks.py,
fix_mojibake command and WSGI/ASGI entrypoints 0%; CV generator 76%; cover-letter
generator and jobs serializers 80%; upload validator 89%. Coverage is not correctness.

Reproduce from ajiri-backend using its existing virtualenv, with local DEBUG=True,
in-memory EMAIL_BACKEND and PYTHON_DOTENV_DISABLED=1. Keep COVERAGE_FILE outside
the repo so existing local .coverage remains untouched:

```powershell
$env:COVERAGE_FILE = Join-Path $env:TEMP 'ajiri-sprint3-verified.coverage'
.\.venv\Scripts\python.exe -m pip_audit -r requirements-prod.txt --progress-spinner off
.\.venv\Scripts\python.exe -m coverage run --source=accounts,profiles,jobs,config manage.py test --noinput
.\.venv\Scripts\python.exe -m coverage report --omit='*/test*.py,*/migrations/*,*/upload_fixtures.py'
```

See SPRINT3_REVIEW.md for issue acceptance gaps and manual-only operations.

### Sprint 3 confirmed follow-up

AJ-10 now supports an opt-in private file-cache alias via THROTTLE_CACHE_DIR.
Independent processes share sequential request budgets; this does not make DRF's
read/modify/write atomic. Local default and ingestion flow remain unchanged.
Live cache/proxy activation is still unverified. AJ-13 option C is approved as a
design only, with implementation deferred. Read-only production HEAD checks found
HTTP-to-HTTPS redirect and standard frame/referrer/nosniff headers, but **no HSTS**;
do not declare the deployment-hardening finding fully fixed on the live site.
