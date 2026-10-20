# Jira roadmap execution

20 October 2026. Source: [AJ board 34](https://michaelmathenge.atlassian.net/jira/software/projects/AJ/boards/34/backlog).
Baseline: remote main and recorded deployed release
`647449851c98f5b22e0419db673f2500c86d1e86`.
Working branch: `codex/jira-roadmap`, isolated checkout `.worktrees/jira-roadmap`.

Michael approved implementation, tests, documentation, push, merge and deployment
of the defined backlog. For provisional AJ-42 through AJ-52, he selected concrete
requirements and test integrations first. Do not represent those as live services.
The complete Jira project query returned 52 issues with `isLast=true`.

## Current local work

- AGENTS.md now links the backlog and records the current authorization and backup
  guideline. The original checkout's other uncommitted files remain untouched.
- AJ-37: owner-only dismissed-application restoration preserves original files and
  text, blocks missing files and unresolved/accepted delivery, and supersedes old
  sending authorization. Added an explicit client action and regressions.
- AJ-37 source is ready for its local commit; no push, merge or deployment of this batch has occurred.

## Actual verification

Using the existing Python 3.12 virtualenv, with `DEBUG=True`,
`PYTHON_DOTENV_DISABLED=1`, `REAL_EMAIL_ENABLED=False`:

```text
python manage.py check                         passed
python manage.py makemigrations --check --dry-run   no changes
python manage.py test jobs.test_lifecycle --noinput  14 passed
python manage.py test --noinput                281 run, OK, 1 Windows skip
```

Resume verification: both additional authorization/ambiguous-delivery restoration
regressions passed. Full suite rerun: **283 tests, OK, one Windows skip**, 192.020s.
The first focused attempt exposed a synthetic fixture without original application
files; the fixture now supplies them, preserving the production missing-file guard.

Explicit Node 24.19, locked npm installation: 180 packages installed, zero audit
findings; `npm run lint`, `npm run test -- --run` (99 tests), and `npm run build`
passed. The generated build has NOT yet been copied into committed frontend_build.
Commit source/review evidence first, then the generated frontend build last.

## AJ-12 platform response supplied by Michael

PythonAnywhere confirms standard Django/WSGI receives native
`wsgi.url_scheme='https'` for HTTPS. Client-supplied X-Forwarded-Proto headers,
including duplicates and comma-separated values, are stripped. Keep
`SECURE_PROXY_SSL_HEADER=None`; do not enable proxy-header trust.

Before activation, verify a real HTTPS request reports secure through the actual
WSGI application. Then activate:

```text
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=300
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
```

Keep host Force HTTPS enabled. Verify no loop, HTTPS HSTS header, ordinary
authentication/profile/download use and spoofed-header behavior. Roll back only
the changed redirect/HSTS settings and reload if verification fails; never restore
the database for a configuration rollback. This response resolves platform
assurance, but live verification and activation remain pending.

## Remaining execution

Continue defined AJ-17 and AJ-24 through AJ-41; reconcile existing functionality
against each actual criterion. AJ-8–AJ-11, AJ-13–AJ-16 and AJ-18–AJ-23 are currently
Done in Jira; AJ-12 and AJ-17 are In Progress. Existing account emails do not
complete application/alert sending. Renewed expiry is recorded as 19 November 2026.

Implement and verify automated private backups with off-server recovery; document
machine availability and platform constraints honestly. Retention remains report
only. Simplify developer/user onboarding after feature changes settle. Housekeeping
must inspect references and preserve private data, backups, stash, Docker lesson
files, coverage and original checkout changes. No cleanup has yet been performed.

## Resumed execution results

AJ-37 committed locally as 7382c79 (source) and bb3c4b2 (build). All 283 backend
tests passed (one Windows skip); 99 frontend tests passed. Not yet merged/deployed.

AJ-24: explicit draft-policy agreement, additive profiles.0006_privacy_notice,
owner-visible read-only evidence, public draft notice and UI. Focused 16 backend
tests passed; full suite 286 passed with one Windows skip (426.804s) after isolating
a historical migration regression to its fixed target instead of future leaf nodes.
No production privacy migration has been applied yet. New frontend gate: 100 tests,
lint and repeated build passed using explicit Node 24.19. The final locked install
passed in .verification/frontend; original worktree reinstall hit a Windows-locked
native Tailwind binary, which was preserved. Lint used the original source path
explicitly because the verification folder is Git-ignored. The CV focus regression
now awaits the animation-frame effect rather than asserting synchronously.
Tailwind scanning is explicitly limited to src so nested checkout/build folders
cannot add unrelated CSS; repeated verification builds matched their asset names.

A newly published npm advisory affected transitive follow-redirects 1.16.0
(GHSA-q3jh-wrc6-jgq8 / GHSA-8r9p-f939-6h3c). Patched only its version, resolved URL
and integrity to 1.16.1, preserving other lockfile entries/platform metadata.
After patch, npm audit reported zero findings; this is advisory matching, not proof
that browser Ajiri credentials were exploitable through a Node-only redirect path.

AJ-12 completed in production on unchanged source 6474498: native secure recognition
verified, original WSGI restored, Django redirect True and HSTS 300 activated without
proxy trust/subdomains/preload. Live header/loop/spoof checks passed; owner reads
and private download passed. Only deliberate check --deploy W005/W021 remain.
Jira Done status was reread and confirmed. See HTTPS_ACTIVATION_20261020.md.

Backup automation verify-and-copy-ajiri-daily-backup created ACTIVE for 10:00 Nairobi
daily, using the documented private snapshot/off-server/restore procedure and
failure reporting. Its first scheduled run remains UNVERIFIED. No always-on
PythonAnywhere scheduler or disk-encryption guarantee is claimed.

README/SETUP simplified; USER_GUIDE and operator backup guidelines added. Verified
unused social sprite removed; no private/user data or original Docker lesson
removed. See HOUSEKEEPING_REVIEW.md. AJ-31/38/41 decisions recorded in
ROADMAP_SPIKE_DECISIONS.md; local staging setup/verification is in progress.
