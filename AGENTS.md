# AGENTS.md: Ajiri Development Guide for Codex

> Codex reads this file at the start of every session. It is the source of truth for scope, rules and the definition of done. If it conflicts with a chat message from Michael, follow Michael and tell him about the conflict.

## 1. Mission

Development backlog: [Ajiri Jira board 34](https://michaelmathenge.atlassian.net/jira/software/projects/AJ/boards/34/backlog).
Follow the current Jira acceptance criteria and sprint order; reconcile existing implementation and deployment evidence before rebuilding completed features.

Michael authorized the remaining roadmap on 20 October 2026, including implementation, tests, documentation, pushes, pull requests, merges after required checks and production deployment. Presented designs, review notes and decisions are approved; do not request repeated intermediate approvals. This authorization supersedes historical checkpoint-only/no-push/no-production restrictions below for this roadmap. Provisional issues still need concrete requirements; never invent credentials, legal approval, user consent or production verification.

Automate routine backups where supported, verify completion/checksums and isolated restoration, and retain private off-server recovery copies. Manual backups are the fallback when platform access or a consistent paused-writer window requires them. Retention remains report-only until a concrete deletion policy is authorized. Housekeeping must preserve user work, private data, backups, Git configuration and stash; remove only files whose redundancy or lack of use is verified.

## 2. Product

Ajiri (ajiri.co.ke) is a job-matching and application-automation platform for the Kenyan market.
- Aggregates jobs via RSS ingestion
- Matches jobs to user profiles by skill (70% threshold triggers alerts; it does not restrict browsing or applying)
- Helps users apply: draft applications, generated CV and cover letter (DOCX), email or external-link sending, job alerts

Users are mostly on phones with limited data. **Mobile-first, lightweight, accessible.**

## 3. Repo and stack (verified, but re-check if something looks off)

- Repo root: `C:\dev\ajiri`. `ajiri-backend/` (Django + DRF) and `ajiri-frontend/` (React + Vite, JavaScript/JSX only, no TypeScript)
- Backend: Django 6.1.2, SQLite, SimpleJWT (access token in JSON, refresh in httpOnly cookie, rotation + blacklisting), django-cors-headers, django-filter, python-docx, feedparser. Celery/Redis available locally only.
- Frontend: Tailwind 4, Radix-backed shadcn-style components, lucide-react, React Router, axios (`src/api/client.js` handles auth interceptors and silent refresh)
- Production: PythonAnywhere free tier, a committed `frontend_build`, and a GitHub Actions workflow that posts jobs to `POST /api/jobs/ingest/` and `/api/jobs/sweep/` (header `X-Ingest-Key`)
- CI exists (`.github/workflows/ci.yml`: backend checks, migrations, tests, frontend lint/build, committed-build consistency; Python matrix 3.12-3.14). Local dev and PythonAnywhere use Python 3.12.

## 4. Verified state (25 October 2026)

Latest verified runtime package is `26261635ccf97c7f69616136258d71032d40fa95`
(PR #60 review guidance; subsequent documentation-only revisions may exist),
including offline analytics/scanner contracts (no production callers or activation),
owner-only saved searches, application progress and reasoned staff
moderation. jobs.0016 added only the protected audit table after a fresh verified
private off-server backup/restore. Existing table values were preserved; no actual
moderation decision or staff access grant occurred. All six checks passed through
PR60; local469 Django tests passed (one platform skip),144 components and eight
helper tests passed; regenerated36-file frontend build matched production bytes.
The latest approved email package puts its separate permission controls before
long previews, with verified live keyboard return/focus. On25October Michael
personally authorized and sent one owner-only application pilot; one accepted
receipt, Brevo Delivered and owner inbox/correct-content confirmation were recorded.
Application sending was then disabled and reloaded; broader sending remains off.
A fresh25October private snapshot, off-server copy and
isolated17-file restore passed; web and both writer workflows were restored.
See docs/JOB_MODERATION.md and docs/ROADMAP_NEXT_ACTIONS.md. Twelve non-Epic
stories remain unfinished; test adapters do not establish live service acceptance. Additive
jobs.0014/0015 applied after verified private off-server backups and isolated
restores. Legacy application fields/snapshots were preserved. Saved searches are
enabled; application/saved-search real sending and queue capture remain disabled.

PR56/58 added actual isolated synthetic PostgreSQL data and Redis/Celery process-crash
rehearsals. Data/relationships/private document bytes and one-handoff receipt reuse
passed; no historical PostgreSQL migration, object storage, broker/host durability,
production storage switch or hosted worker is verified. Source1c264164 contains the
unused queue lab; production runtime and sending flags are unchanged. AJ47/AJ48
remain In Progress. See docs/STORAGE_MIGRATION_REHEARSAL.md and docs/QUEUE_BROKER_REHEARSAL.md.
Payment and inline queue contracts are offline test integrations, not live services.
PR50 passed all six CI checks; local434 Django tests (one platform skip),141
components and nine real-endpoint browser journeys passed. Production health,
exact live build, clean source and authenticated empty application-list reads
passed. Real owner progress entry was unavailable because the account had no rows.
See docs/APPLICATION_PIPELINE.md and docs/JIRA_ROADMAP_PROGRESS.md for evidence.
The preparation-only repair passed all six required checks and deployed without
migrations. Owner-only preparation is enabled while application sending remains
False; authenticated synthetic review editor and health/HSTS passed. Never activate
sending before current personal document approval and exact authorization.
The backlog is not complete. Optional application URLs preserve all three SQLite
search triggers. Account mail remains a separate owner-only pilot.

JOB_FRESHNESS_ENFORCED and EMPLOYER_POSTING_ENABLED are true. Anonymous
PUBLIC_JOBS_ENABLED remains false. 979 jobs were retained; 977 active historical
listings without reliable evidence were archived as unverified, not proven expired.
No currently eligible vacancies remained at activation. Do not disable freshness
on rollback; independently disable posting/publication and preserve new records.
Independent staff review and a future closing date are required for employer jobs.
General employer email onboarding remains constrained by the owner-only mail pilot.

A fresh consistent backup, exact private off-server copy and isolated restore
passed (13 media files); writers were restored before download. This was a release
fallback, not proof of a fresh unattended daily snapshot. Production HTTPS health,
HSTS300, exact live HTML/employer bundles, clean source and authenticated jobs/
employer-page reads passed. The signed-in account had no historical applications,
so an additional real document download was unavailable; automated ownership and
unchanged-document regressions passed. No real employer or application was sent.

All six required checks passed on c7a00bc (CI40011465224), including eight Linux
browser/performance tests in 96.909s. Locally: 378 Django tests (one platform skip),
132 components and seven browser journeys passed. Local Lighthouse NO_NAVSTART
remains failed evidence; a valid Linux pass does not erase that local limitation.
Manual Android/iOS installation remains unverified. Earlier search measurements
(877-job sample) remain historical evidence in docs/JIRA_ROADMAP_PROGRESS.md.

Earlier PR #30/#31 functionality remains:
verified-request erasure with signed recovery journals, resumable private-file cleanup
and restore replay. Production verification used dry runs only; no account was erased.
This follows PR #29 export and explicit alert consent/unsubscribe; existing values
were preserved, and no consent inferred. The owner personally opted into the bounded
synthetic alert pilot, confirmed inbox receipt and unsubscribed. Production confirmed
the unsubscribe event and email eligibility false. The pilot flag is off; normal
alert transport remains disconnected. Retain the independent erasure ledger on restores.
Account email verification/reset has an owner-only Brevo pilot. Reviewed application
packages and explicit authorization exist; broader application sending remains disabled
until its gated integration and pilot pass. Never treat console output/provider
acceptance as inbox delivery.

AJ-12 is verified in production: native WSGI HTTPS, proxy SSL header None, redirect
True, HSTS 300 seconds, subdomains/preload False; host Force HTTPS remains enabled.
See docs/HTTPS_ACTIVATION_20261020.md. Free-account expiry is recorded as 19 November
2026; recheck on renewal. The daily verified-backup desktop automation is active;
the 21 October run verified an existing same-Nairobi-day copy/restore receipt and
skipped a duplicate snapshot. A fresh scheduled snapshot is not yet verified.
See docs/BACKUP_AUTOMATION.md.

Use docs/JIRA_ROADMAP_PROGRESS.md for local package/CI/deployment evidence. Do not
infer that local commits or merged source have been deployed. Preserve the original
checkout, Docker lesson, uncommitted lockfile, coverage, stash and Git configuration.

## 5. Known gotchas

- DRF validation errors are field-keyed arrays (`{"email": ["..."]}`); other errors are `{detail: "..."}`. The frontend must render **all** of them, never just the first.
- Paginated lists return `{count, next, previous, results}`, 20 per page.
- SimpleJWT: `str(refresh)` does not create a new token. Rotation needs `blacklist()` plus `set_jti()` / `set_exp()` / `set_iat()`. The refresh token must stay in the httpOnly cookie, never in the JSON body.
- Django: `blank=True` and `default=''` are different; mixing them causes NOT NULL failures. Dotted `source=` fields on DRF serializers can silently drop data; use `to_representation`.
- Never let an expired access token attach to login/register/refresh requests (public endpoints are excluded in the interceptor).
- Windows/PowerShell: use `curl.exe`, not `curl`. `-replace` is case-insensitive; use `-creplace` with `[regex]::Escape()`.
- Integrate new code alongside existing imports. Never overwrite file tops.

## 6. Roadmap workflow

Use the linked Jira backlog, current sprint acceptance and verified implementation
as the source of work. Complete defined AJ-17 and AJ-24–AJ-41 in tested packages;
reconcile completed work rather than duplicating it. Michael chose concrete
requirements and test integrations first for provisional AJ-42–AJ-52. Designs,
provider stubs and spikes must not be represented as live services.

Work in isolated `codex/` branches based on fetched reviewed main. Preserve dirty
original checkouts. Pass section 7 gates for each package, keep focused commits,
then push, open a PR and merge only after required CI passes. The current task
explicitly authorizes this release workflow and production verification.

Document concepts in ajiri-backend/docs/CONCEPTS.md with backend-relative references.
Use Node 24.19 explicitly and locked installation; commit generated frontend_build
last in each frontend package. Never replace production storage with development data.

## 7. Quality gates (every package, no exceptions)

1. `git branch --show-current` before every commit
2. Backend: `python manage.py check`, `makemigrations --check`, full test suite passes
3. Frontend: `npm ci`, `npm run lint`, `npm run build` pass
4. `frontend_build` regenerated and committed as the **last commit of each frontend package** (CI checks consistency)
5. New behaviour has tests. No passing claims without actually running the command and recording its result.
6. No secrets, `.env` files, or personal data in commits
7. New concepts documented in `docs/CONCEPTS.md` (`## slug`, plain-language explanation) and referenced from code as `# see docs/CONCEPTS.md#slug`


If a gate cannot run in your environment, say so explicitly and mark the package **unverified**; do not claim done.

## 8. Autonomy and boundaries

Proceed without repeated package/design approvals within the authorized backlog.
Continue independent work when one item is blocked, recording the exact limitation.
Do not invent acceptance criteria for provisional work; refine it and use test
integrations first as Michael selected. Report failed gates honestly and fix causes.

Preserve AUTH_USER_MODEL and migration history. Use additive, reviewed migrations
and data-preserving rollback. Actual erasure requires a verified account-owner
request, not merely approval to implement an erasure feature. Do not buy services,
accept legal agreements, enter new credentials or make irreversible user-data
changes on the strength of a broad implementation request. Michael enters secrets
privately. Ask only for genuinely missing requirements/access or consequential
choices outside this scope, explaining the specific reason; do not stop the rest.

## 9. Git workflow

- Never commit directly to main; use focused feature branches and required-check PRs.
- The current roadmap task authorizes pushes, PR creation, merges after checks,
  Jira updates and PythonAnywhere production deployment, including private backups.
- Do not bypass required checks, rewrite published history or modify Git configuration.
- Check the branch before every commit and verify new author/committer identities
  use Michael's configured noreply address. Preserve stash and unrelated changes.

## 10. Do not touch without asking

`AUTH_USER_MODEL` and migration history; the SimpleJWT cookie/rotation logic; `src/api/client.js` interceptor behaviour (extend, do not rewrite); CORS settings; ingestion endpoints and `X-Ingest-Key` handling; CI workflow (propose changes in the report); hosting config.

- Production work follows the explicit current-task authorization and verified rollback; never infer it from historical reports.
- Never ask for or write secrets (keys, passwords, SMTP credentials or tokens) in chat, files or commits. Michael enters credentials privately himself.
- Changes must support the documented deployment order: backup, migrations, then activation of new code. Migration source may be staged first; new code must not handle requests before its migrations complete.

## 11. Working with Michael

- All designs, review notes and decisions presented to Michael as of 20 October 2026 are approved. Continue the agreed roadmap without intermediate approval pauses; Michael will review the final product. Future design changes and actions outside the agreed scope require separate authorization. Push, merge, deployment and real email sending remain subject to the current task's explicit authorization.
- Michael is a Senior Scrum Master and solo developer, learning React. Explain the *why* of non-obvious choices in short code comments and in the report.
- Be direct. Push back when something is risky or wrong, and explain why.
- Give exact PowerShell commands for anything he needs to run, plus the expected result.
- Michael tracks work in Jira. Jira edits are authorized for this roadmap; note material acceptance changes and record honest story-point suggestions.

## 12. Handback and guidelines

Keep docs/JIRA_ROADMAP_PROGRESS.md current with branches/ranges, actual commands,
results, skipped/unverified checks, migrations, CI, source and deployed revisions,
rollback and remaining work. Update Jira from evidence; local implementation alone
is not deployed acceptance. Retain historical reviews without using them as current
setup instructions. README/SETUP and docs/USER_GUIDE.md are the onboarding entry points.

Automated backups must verify completion, integrity, private off-server copy and
isolated restore, and report failures. Manual backup is a fallback, not the default;
never claim an unavailable scheduler ran. Retention is report-only until a concrete
pruning policy is approved. Housekeeping requires demonstrated lack of use and
recoverable tracked removal; never indiscriminately delete untracked files or backups.

Complete the approved roadmap through tested push/merge/deployment; report real
external blockers and unfinished items explicitly rather than claiming completion.
