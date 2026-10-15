# Checkpoint 3A review — security hardening only

15 October 2026, Africa/Nairobi. Base integration/checkpoint-3 at `0a02c74`.
Michael's build instructions supersede AGENTS' earlier documentation-only mission
and WP numbering. Earlier Checkpoint 3 email/privacy WP11-WP15 remain proposals,
not implemented by these identically numbered **Checkpoint 3A** packages.
No push, main merge, connector write or production operation performed.

## 1. Package summary

| WP | Local status | Branch | Source range | Suggested points |
|---|---|---|---|---:|
| WP11 | passed local gates | feature/password-validation | 0a02c74..b792a9f | 3 |
| WP12 | passed; cache/proxy limits below | feature/throttling | bc59a78..f4e819f | 5 |
| WP13 | passed; structural checks only | feature/upload-content-validation | 1b306ce..183b18b | 5 |
| WP14 | passed; production manual verification pending | feature/deploy-settings | 2ec3767..82d8931 | 3 |
| WP15 | design only; no CSRF implementation | feature/refresh-cookie-csrf-design | 3e49fa8..feature/refresh-cookie-csrf-design | 2 |

Source ranges exclude integration merges. Resolve final WP15 tip with
`git rev-parse feature/refresh-cookie-csrf-design`. Passing packages merge --no-ff.
Points are relative sizing for Michael's tracker, not time estimates (total 18).

## 2. What changed

### WP11 — Password validation

Registration runs configured validators with candidate email/name and returns every
message in password-field arrays, including when another field fails. Manager-based
creation validates non-None passwords. Custom-user admin creation/change forms retain
Django validation. No password reset endpoint was invented, no existing hash changed,
no forced reset and no JWT/cookie change. Tests cover short/common/numeric/similar
passwords, strong acceptance, manager/admin/set-password paths and legacy weak login.
Frontend already displayed arrays; its regression now asserts multiple password errors.

### WP12 — Endpoint throttling

Login/register/refresh use IP keys; apply/send use authenticated user keys. Defaults
are 10/min login, 5/hour register, 60/min refresh, 20/hour apply, 10/hour send, all env
overridable (THROTTLING.md). These request rates are NOT the proposed future daily
accepted-email quota. Added attributes only on RefreshView; token/cookie code unchanged.
Interactive login/register/apply/send show 429 wait guidance, reading Retry-After where
available; no automatic mutation retry. Test caches are cleared between cases.

Repository default LocMemCache is process-local; live cache/worker topology is not
inspected. Limits are approximate, not distributed hard guarantees. DRF_NUM_PROXIES=0
ignores client forwarded headers until Michael verifies trusted hops. Same-NAT/proxy
users may share public limits; this is a pre-deployment gate, not a claimed production
fix. Proposed private shared-filesystem cache is documented only; multi-host/atomic
requirements need another design. No ingestion/sweep endpoint changes or global default
throttle were added. Tests show valid-key calls remain successful beyond user limits.
The existing interceptor may route to login if silent refresh receives 429; tailored
silent-refresh recovery UX remains an auth-client follow-up requiring approval. Its
behaviour was deliberately not rewritten in this package.

### WP13 — Content-aware CV uploads

Keep 5 MB, PDF/DOC/DOCX; reject empty/oversize/spoofed files. PDF checks signature and
EOF, DOC bounded compound directory/WordDocument entry, DOCX expected package parts,
XML, paths, CRC and expansion limits. No extraction/network/renderer/scanner. New stored
basenames are random UUIDs; existing data untouched. Unusual valid packages may be
rejected conservatively (UPLOAD_VALIDATION.md). Invalid uploads preserve prior CV.
Synthetic fixtures now contain format-appropriate bytes rather than arbitrary text.

### WP14 — Deploy settings

DEBUG=False profile enables SSL redirect and HSTS 300 seconds; local DEBUG=True keeps
HTTP/HSTS off. Session/CSRF Secure flags, nosniff/referrer/frame policies and HSTS controls
are env-overridable. Broad HSTS/preload remain off. Existing TRUST_PROXY_SSL_HEADER
opt-in is retained; verify proxy sanitation before activating production redirects.
Tests cover isolated settings profiles, overrides, trusted HTTPS no-loop, HTTP redirect,
headers and untrusted forwarded proto. REFRESH_COOKIE_SECURE/JWT logic unchanged.
See DEPLOY_SECURITY_VERIFICATION.md for Michael-only checks and rollback.

### WP15 — CSRF design and handback

REFRESH_COOKIE_CSRF_DESIGN.md documents actual Lax/HttpOnly/Secure cookie, DRF exemption,
credentialled CORS and same-origin deployment; compares Strict, Origin+custom header and
explicit Django CSRF validation. Recommends the standard Django token/origin solution,
with tests and coordinated rollback. No option is implemented. Audit remediation status
separates historical findings, local fixes and remaining open work. Standing rules remain;
AGENTS time-bound sections record Checkpoint 3A scope.

## 3. Verification evidence

Executed locally with Python 3.12.6 / Node 22.15.0 (existing runtimes). Every package runs
backend check, makemigrations --check --dry-run, full Django suite; npm ci, lint, component
tests and build. Django mail is in-memory. No real SMTP/production credential used.

| Package | Django suite | Frontend suite | Other gates |
|---|---|---|---|
| WP11 | 76 run, 75 passed + 1 skipped | 24 passed | check/migration check/npm ci/lint/build passed |
| WP12 | 80 run, 79 passed + 1 skipped | 25 passed | all passed; 4 final targeted throttle tests also passed |
| WP13 | 84 run, 83 passed + 1 skipped | 25 passed | all passed |
| WP14 | 88 run, 87 passed + 1 skipped | 25 passed | all passed |
| WP15 | 88 run, 87 passed + 1 skipped | 25 passed | all required gates passed |

The skip is Windows symlink privilege coverage; Linux CI must run it before Michael
merges. No CI write/run performed. Initial sandbox attempts failed node_modules/temp
permissions; required commands passed with normal filesystem access. One registration
validation-order regression was corrected before merge; no protection was weakened.
ZIP duplicate-name warning is deliberate malformed fixture coverage.

Local production-like `check --deploy`: original W004/W008 gone; W005/W021 remain
intentionally because includeSubDomains/preload are false. No warnings silenced. This
is not a claim of zero warnings or live production hardening.

Frontend build packaged once at end of WP11 (no byte changes) and once in WP12's final
commit; exact dist/package bytes verified. WP13/WP14/WP15 builds are gates only and do
not regenerate the committed package. No dependency/lockfile or CI changes. Final AST comparisons confirm login/refresh/logout
post bodies and ingestion/sweep/key-check implementations are identical to the base;
protected model/auth-client bytes and migration/workflow/dependency diffs are unchanged.

## 4. Manual verification script — Michael

Run only after reviewing this branch; deployment is a separate decision. Local tests
use disposable test DB/media and captured mail, never real employers. In PowerShell:

```powershell
cd C:\dev\ajiri
git branch --show-current
git status --short
cd ajiri-backend
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test accounts.test_passwords accounts.test_throttles profiles.test_upload_content config.test_security --noinput
.\.venv\Scripts\python.exe manage.py test --noinput
cd ..\ajiri-frontend
npm ci
npm run lint
npm run test -- --run
npm run build
```

Expected targeted 16 tests pass; full 88 run with one possible Windows symlink skip;
25 frontend tests pass, migration check finds none. Stop if frontend tooling is locked;
stop your own dev server before npm ci, don't kill unrelated processes or use force fixes.

Local UI review (synthetic accounts only, credentials entered privately by you):
1. Register with short/common/numeric and email-similar values; every returned password
   message appears. A strong password registers; existing-user login still works.
2. In an isolated local environment, lower one THROTTLE_* rate before starting the server;
   repeat that action and expect 429/wait message. Wait the indicated interval and retry
   once. Apply/send status must not change on a throttled request. Use automated tests
   for cache/timer isolation; don't exhaust production/login limits deliberately.
3. Upload genuine small PDF/DOC/DOCX and download as owner; bytes unchanged, random
   stored filename. Rename HTML/executable bytes to .pdf or try an empty/oversize file:
   expect cv_file errors, previous CV retained. Never open executable test content.
4. Read CSRF design, choose an option separately. Do not expect a CSRF fix in this build.

Production verification is **manual-only and not performed**: follow
DEPLOY_SECURITY_VERIFICATION.md for proxy sanitation, exact curl.exe header/no-loop
checks, secure cookie attributes without values, 300s HSTS and rollback; THROTTLING.md
for hop/cache verification. Keep normal backup -> migrate -> activate order and private
media mapping rules. No 3A migration, real-email change or fixture deletion is required.

## 5. Decisions and boundaries

No migration/dependency needed. AUTH_USER_MODEL/model definition, migration history,
CORS, ingestion endpoint implementations, hosting config, CI and auth interceptor are
unchanged. Password manager/form validation is within WP11; refresh only gains throttle
attributes. No SMTP/privacy/restoration/rights/monitoring feature proposals were built.
Michael must verify live proxy/cache topology and approve a CSRF implementation later.

## 6. Risks and follow-ups

- Process-local non-atomic throttle counters, proxy/NAT shared limits; no hard quota.
- Silent-refresh 429 recovery remains existing auth-client behaviour, not tailored UX.
- Structural validation is not malware detection; historical uploads unscanned.
- HSTS/proxy/header/live cookie verification pending; 300s browser retention survives
  zeroing the setting until expiry. No preload/subdomain broadening authorized.
- CSRF, inactive-user refresh, reset/verification, console false-send/log privacy, real
  mail quotas, legal/consent/rights, advisory scan/patches, accessibility/coverage and
  query/scaling issues remain open as listed in MODERNISATION_AUDIT.md.
- An untracked ajiri-backend/.coverage file appeared during local command execution;
  it was not read, modified, deleted or staged. No coverage measurement is claimed.

## 7. Recommended next sprint

Review the CSRF design and proxy/cache findings first; choose a supported shared-counter
strategy before treating throttles as cross-worker protection. Then separately scope
account recovery/verification and real-email safeguards with the unresolved provider,
identity, quota and legal decisions. No deployment is implied by this handback.
