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
