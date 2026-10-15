# Sprint 3 review

15 October 2026 (Africa/Nairobi). Read directly from Jira board 34, sprint ID 3,
Ajiri Sprint 3, all nine issues AJ-8 through AJ-16. Jira reports this sprint as
future and Sprint 4 as active; no sprint or issue was changed. Source tested:
integration/checkpoint-3 at 5e15a11, isolated branch codex/sprint-3-evidence.

## Scope and acceptance

| Issue | Evidence / outcome | Remaining acceptance |
|---|---|---|
| AJ-8 GitHub hygiene | Earlier session configured protection, Dependabot and secret scanning; see ROADMAP_WORKING_PROMPTS.md | Current live settings not reverified this run; owner-scoped credentials cannot distinguish Michael from an agent |
| AJ-9 Password validation | Existing WP11, b792a9f; password regression suite included in fresh passing tests | Review; no forced resets |
| AJ-10 Throttling | Existing WP12, 89af1fa/f4e819f; fresh tests pass | Not fully done: LocMemCache is per-process; live proxy/hop/cache verification and shared-counter choice pending (THROTTLING.md) |
| AJ-11 Upload content | Existing WP13, 183b18b; spoof/empty/ZIP limits tested | Review; structural checks are not malware scanning |
| AJ-12 Deploy hardening | Existing WP14, 82d8931; tests and rollback in DEPLOY_SECURITY_VERIFICATION.md | Not done against Jira acceptance: Michael must verify production; no production action authorized |
| AJ-13 Refresh CSRF design | Existing WP15, fe656ff; REFRESH_COOKIE_CSRF_DESIGN.md | Michael's explicit design approval; no auth mitigation implemented |
| AJ-14 Scan / coverage | Executed and recorded in MODERNISATION_AUDIT.md below | Scan task complete; dependency remediation remains an open release risk |
| AJ-15 Backup / renewal | Manual checklist below | Blocked: production backup transfer and reminder not performed |
| AJ-16 Audit / planning | Existing MODERNISATION_AUDIT.md, CHECKPOINT3_PLAN.md, SMTP_EMAIL_DESIGN.md, DECISIONS_NEEDED.md; prior design approvals in chat | No new 3B implementation authorized |

Existing packages were merged --no-ff; do not recreate them or claim all nine issues
Done. Suggested sizing retains Jira's estimates (31 total); this evidence-only follow-up
is AJ-14's existing 2 points, not another implementation of 3A.

## Fresh verification

- Existing Python 3.12 virtualenv, installed pip-audit 2.10.1 and coverage 7.16.2;
  no new packages installed or requirement files changed by this run.
- `manage.py check`: no issues. `makemigrations --check --dry-run`: no changes.
- Coverage-wrapped full Django suite: 88 run, 87 pass, one Windows symlink skip.
  In-memory email, disposable test database/media; no provider or production call.
- Statement coverage: 1182 statements, 121 missed, 90%, excluding tests,
  migrations and upload fixtures. Branch coverage not measured. See audit for commands.
- `pip_audit -r requirements-prod.txt --progress-spinner off`: exit 1,
  15 advisories across two pinned packages. This is findings, not a tool failure.
- First sandbox attempts failed on temporary-file permissions; successful reruns
  used normal temporary-file access. No security check was bypassed.
- Documentation changes only: frontend install/lint/tests/build not rerun and
  frontend_build not regenerated. Previous 3A frontend results remain historical.

## Michael-only outstanding operations

1. Follow DEPLOY_SECURITY_VERIFICATION.md for AJ-12. Do not enable trusted proxy
   headers until the platform's header sanitation is verified. Confirm the short
   HSTS policy, redirects without loops, and cookies/headers; retain rollback steps.
2. For AJ-15, sign into PythonAnywhere privately. Locate the verified private backup
   described by DEPLOYMENT_CHECKLIST.md and confirm its date and contents. A historical
   backup alone does not protect newer production data; take a fresh backup manually
   if necessary using that checklist. Download DB and private-media backup through
   the authenticated dashboard to an encrypted, access-restricted local folder outside
   the repo and public/cloud-synced folders. Never attach it to Jira or chat.
3. Compare a SHA-256 digest on server and local copy (PowerShell:
   `Get-FileHash -Algorithm SHA256 -LiteralPath 'YOUR_PRIVATE_BACKUP_PATH'`).
   Rehearse integrity/restore against a disposable local copy; record only success
   and date, never data or credentials. Do not delete server backups as part of this step.
4. Recheck the web-app expiry in the dashboard; 14 November 2026 is historical,
   not newly verified. Set a private calendar reminder one week before the actual
   expiry and another two days before; renew manually and confirm the updated date.
   No calendar event or automation has been created by this run.

## Boundaries and handback

No app, dependency, migration, CI, hosting, auth or production changes. No pushes,
PR merges, Jira writes or 3B work. Preserve the original checkout's modified npm
lockfile and untracked coverage data. Review the audit findings and approve a separate
dependency-remediation scope before addressing them; no automatic audit fix.

## Approved follow-up — 15 October 2026

Michael confirmed the proposed remaining-task choices. AJ-10 now has an opt-in
private file-cache implementation and separate-process regression test; activation
and live proxy/worker verification remain pending. See THROTTLING.md. AJ-13 option C
is approved as a design only; no auth changes authorized by that acceptance.

Read-only production checks: authenticated Web dashboard confirms Python 3.12,
Force HTTPS enabled, no static mappings, expiry **14 November 2026**. Public HEAD
HTTP /login returns 302 to HTTPS; HTTPS /login returns 200, no redirect loop,
DENY frame policy, nosniff, same-origin referrer and no-store. **No HSTS header**
was returned: AJ-12 is not fully accepted. No reload, renewal or configuration edit
performed. Live cookie flags and trusted proxy hop/worker topology remain unverified;
no real account login or request-exhaustion probe performed.

AJ-15: authenticated directory listing confirms the verified-deploy backup folder
exists. Backup bytes were not opened or transferred; Michael must supply a private
local destination before download. Renewal reminder creation was rejected by automatic
approval review because exact persistent-automation authorization was unclear. No
reminder exists; request explicit approval for 7 and 12 November at 09:00 Africa/Nairobi.
Production verification authorization does not authorize a deployment to fix HSTS.

Fresh follow-up gates: backend check and migration check passed; **90 tests run,
89 passed, one Windows symlink skip**. Six targeted throttle tests passed, including
two new separate-process/configuration regressions. npm ci, lint, all 25 frontend
tests and build passed. Frontend source/lockfiles/build package unchanged; build was
a gate only. No regeneration or dependency upgrade needed. Suggested incremental
effort for the shared-cache follow-up: 2 points within AJ-10's existing estimate.

Proposed local backup destination: `C:\Users\micha\AjiriBackups`, outside the repo
and standard OneDrive folders. It does not exist yet. Drive encryption could not be
verified with the available local BitLocker cmdlet (absent). Before transferring
production data, Michael should confirm device encryption in Windows Settings and
approve an account-restricted folder (or encrypted removable storage). No backup
contents, .env or credentials were downloaded; no new backup was taken on production.

## Subsequent backup evidence and deployment readiness

Michael completed a fresh production backup at manual-20261015-181545 with writers
idle and ingestion paused, then re-enabled ingestion. The downloaded database and
revision hashes matched; browser-decompressed media matched the decompressed server
hash. Michael's local rehearsal verified all hashes, database integrity `ok`, and
restored 4 media files / 12,866 bytes into a disposable private directory. BitLocker
Protection On, recovery-key backup and account/SYSTEM/Administrators folder access
were confirmed by Michael. This supersedes the earlier backup-transfer blocker;
it is a basic restore rehearsal, not an authenticated application restore test.

On Michael's request to handle the remaining tasks, read-only server checks found:
clean tracked checkout at **2d5d175**, DEBUG=False, Django SSL redirect=False,
HSTS=0, proxy SSL header=None, secure session/CSRF cookies=True, no NUM_PROXIES
configuration and default LocMemCache. No server settings were changed or reloaded.

Remote main is **1ef6159**; frontend and all three backend CI checks passed. The
shared-cache commit b860658 is absent from remote main, so shared-cache activation
cannot proceed through the reviewed release path until Michael reviews/publishes
that change. No direct production patch, push, PR or main merge was attempted.

PythonAnywhere's current client-IP documentation guarantees the last X-Forwarded-For
item is the peer seen by its load balancer, but an application's additional upstream
proxy/CDN topology must be established before configuring NUM_PROXIES. Its Force HTTPS
documentation confirms host-level redirection; the consulted SSL-header material did
not establish the required X-Forwarded-Proto sanitation contract. Per
DEPLOY_SECURITY_VERIFICATION.md step 3, stop the HSTS/redirect rollout until that
contract or an appropriate native secure-scheme configuration is verified. Keep
Force HTTPS enabled; do not infer proxy trust from a passing synthetic test.

References: https://help.pythonanywhere.com/pages/WebAppClientIPAddresses/ and
https://help.pythonanywhere.com/pages/ForcingHTTPS/ .

Renewal automation creation was again rejected by automatic approval review as
insufficiently specific persistent-action authorization. No reminder exists. Exact
approval requested: reminders on 7 and 12 November 2026, 09:00 Africa/Nairobi, for
the 14 November expiry; no automatic renewal or production modification.
