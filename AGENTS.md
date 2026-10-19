# AGENTS.md: Ajiri Development Guide for Codex

> Codex reads this file at the start of every session. It is the source of truth for scope, rules and the definition of done. If it conflicts with a chat message from Michael, follow Michael and tell him about the conflict.

## 1. Mission

Deliver Checkpoint 4 Phase C on integration/checkpoint-4, pinned to
4b6e99bac4995fd3e36e6fbe1c7e3176383b6214. Michael's 19 October Phase C prompt
supersedes historical mission/package numbering and integration branch references.
Build C1 acceptance journey, C2 CV layout verification, C3 UI polish and C4 status
housekeeping, then document D1 alert defaults, D2 certificate decisions and D3
application/alert sending. Branch packages from integration and locally merge
--no-ff after section 7 gates; Michael explicitly approved these local merges.
No pushes, PRs, remote merges, connector writes, production actions, migrations or
new dependencies. Do not change auth/JWT/cookies/CSRF, CORS, ingestion, hosting or
CI. Stop affected work for a migration/auth requirement; continue independent
packages under section 8. All sending/consent/certificate designs remain proposals.

## 2. Product

Ajiri (ajiri.co.ke) is a job-matching and application-automation platform for the Kenyan market.
- Aggregates jobs via RSS ingestion
- Matches jobs to user profiles by skill (70% threshold triggers alerts; it does not restrict browsing or applying)
- Helps users apply: draft applications, generated CV and cover letter (DOCX), email or external-link sending, job alerts

Users are mostly on phones with limited data. **Mobile-first, lightweight, accessible.**

## 3. Repo and stack (verified, but re-check if something looks off)

- Repo root: `C:\dev\ajiri`. `ajiri-backend/` (Django + DRF) and `ajiri-frontend/` (React + Vite, JavaScript/JSX only, no TypeScript)
- Backend: Django 6.1, SQLite, SimpleJWT (access token in JSON, refresh in httpOnly cookie, rotation + blacklisting), django-cors-headers, django-filter, python-docx, feedparser. Celery/Redis available locally only.
- Frontend: Tailwind 4, Radix-backed shadcn-style components, lucide-react, React Router, axios (`src/api/client.js` handles auth interceptors and silent refresh)
- Production: PythonAnywhere free tier, a committed `frontend_build`, and a GitHub Actions workflow that posts jobs to `POST /api/jobs/ingest/` and `/api/jobs/sweep/` (header `X-Ingest-Key`)
- CI exists (`.github/workflows/ci.yml`: backend checks, migrations, tests, frontend lint/build, committed-build consistency; Python matrix 3.12-3.14). Local dev and PythonAnywhere use Python 3.12.

## 4. Current state as of 19 October 2026

Pinned merged main is 4b6e99bac4995fd3e36e6fbe1c7e3176383b6214, including PRs
21-24. Last recorded production is 641cdfb; no production inspection/deployment
occurs in Phase C. The pinned main must not be described as deployed. Since the
recorded deployment: CV date/save feedback and registration journey coverage,
frontend dependency/build updates, checkout updates and draft concurrency test
repair. No requirements or migration changes occur in that release delta.

Repository code includes 3A hardening, Phase A CSRF/health/logging/backup tools,
account verification/reset and owner-only email pilot, CV builder approval and
approved-CV application snapshots. Michael reported receiving and verifying his
pilot email and successful registration/profile/CV download. These are historical
owner reports, not a current production audit. Broader application/alert real
sending remains gated; existing console paths do not prove inbox delivery.
Redirect=False/HSTS=0 was last reported pending proxy scheme verification; current
settings are UNVERIFIED here. Renewal expiry must be rechecked by Michael.

C1-C3 local gates are recorded in package reviews: 216 Django tests run at C3,
one Windows symlink skip; 71 component tests; Node 24.19 locked install/lint/build.
Future approvals use cv-v2; Word synthetic rendering was inspected (six pages and
one page). Google Docs/phone/browser visual checks remain UNVERIFIED. The full
checkpoint results and limits belong in CHECKPOINT4_PHASE_C_REVIEW.md. New alert
email defaults/consent, certificate uploads and broad sending are NOT implemented.
Preserve original checkout changes, coverage, stash and Git configuration.

## 5. Known gotchas

- DRF validation errors are field-keyed arrays (`{"email": ["..."]}`); other errors are `{detail: "..."}`. The frontend must render **all** of them, never just the first.
- Paginated lists return `{count, next, previous, results}`, 20 per page.
- SimpleJWT: `str(refresh)` does not create a new token. Rotation needs `blacklist()` plus `set_jti()` / `set_exp()` / `set_iat()`. The refresh token must stay in the httpOnly cookie, never in the JSON body.
- Django: `blank=True` and `default=''` are different; mixing them causes NOT NULL failures. Dotted `source=` fields on DRF serializers can silently drop data; use `to_representation`.
- Never let an expired access token attach to login/register/refresh requests (public endpoints are excluded in the interceptor).
- Windows/PowerShell: use `curl.exe`, not `curl`. `-replace` is case-insensitive; use `-creplace` with `[regex]::Escape()`.
- Integrate new code alongside existing imports. Never overwrite file tops.

## 6. Checkpoint 4 Phase C packages

| Package | Branch | Acceptance |
|---|---|---|
| C1 | feature/acceptance-journey | Real API registration through approved-CV application review, exact bytes, no send/budget consumption; client transition tests |
| C2 | feature/cv-layout-verification | DOCX structure, installed Word rendering, manual cross-viewer checks; immutable old approvals |
| C3 | feature/ui-polish | Empty-skills prompt, readable complete form errors, safe readable download headers; snapshots unchanged |
| C4 | docs/housekeeping | Only sections 1/4/6/12 rewritten; ancestry-grounded banners preserve historical text |
| D1 | docs/alert-defaults-design | New-user email OFF and existing-user confirmation design; no code/migration |
| D2 | docs/certificates-decisions | Options/recommendations/defaults and explicit pending approvals; no uploads/schema |
| D3 | docs/application-alert-sending-design | Ledger/consent/truthful states and owner-only pilot design; no sending/schema |

Use section 7 gates for every package, including full Django and component tests.
Use Node 24.19 explicitly. Refresh frontend_build as the last frontend package
commit; verification-only builds must match. No dependency/migration is authorized.
Document concepts in ajiri-backend/docs/CONCEPTS.md with backend-relative references.

## 7. Quality gates (every package, no exceptions)

1. `git branch --show-current` before every commit
2. Backend: `python manage.py check`, `makemigrations --check`, full test suite passes
3. Frontend: `npm ci`, `npm run lint`, `npm run build` pass
4. `frontend_build` regenerated and committed as the **last commit of each frontend package** (CI checks consistency)
5. New behaviour has tests. No passing claims without actually running the command and recording its result.
6. No secrets, `.env` files, or personal data in commits
7. New concepts documented in `docs/CONCEPTS.md` (`## slug`, plain-language explanation) and referenced from code as `# see docs/CONCEPTS.md#slug`

If a gate cannot run in your environment, say so explicitly and mark the package **unverified**; do not claim done.

## 8. Autonomy and stop conditions

Proceed package by package without asking for approval. **Stop and ask** only if:
- A change requires a new migration that alters or removes existing data, or touches `AUTH_USER_MODEL`
- You need to change auth, CORS, the ingestion flow, or deployment config
- A package would exceed its scope or need a new dependency not already listed here (ask before adding)
- Tests fail and you cannot fix the cause after two focused attempts
- Requirements are ambiguous in a way that changes the design
- Anything looks destructive or irreversible

When blocked on one package, record it in the report and continue to the next independent package where possible.

## 9. Git workflow

- Create `integration/checkpoint-1` from up-to-date `main`. Branch every package from it and merge back with `--no-ff` after the gates pass.
- **Never commit to `main`. Never push.** Michael reviews and pushes.
- Small, focused commits with clear messages.
- Never merge PRs, push, or use GitHub/connector write actions unless Michael asks for that exact action in that session.

## 10. Do not touch without asking

`AUTH_USER_MODEL` and migration history; the SimpleJWT cookie/rotation logic; `src/api/client.js` interceptor behaviour (extend, do not rewrite); CORS settings; ingestion endpoints and `X-Ingest-Key` handling; CI workflow (propose changes in the report); hosting config.

- Never touch production. Server instructions are for Michael to perform manually.
- Never ask for or write secrets (keys, passwords, SMTP credentials or tokens) in chat, files or commits. Michael enters credentials privately himself.
- Changes must support the documented deployment order: backup, migrations, then activation of new code. Migration source may be staged first; new code must not handle requests before its migrations complete.

## 11. Working with Michael

- Michael is a Senior Scrum Master and solo developer, learning React. Explain the *why* of non-obvious choices in short code comments and in the report.
- Be direct. Push back when something is risky or wrong, and explain why.
- Give exact PowerShell commands for anything he needs to run, plus the expected result.
- Michael tracks work in Monday.com himself. Give completed items and honest story-point suggestions per package; do not assume any Monday.com access.

## 12. Checkpoint 4 Phase C handback

Write docs/CHECKPOINT4_PHASE_C_REVIEW.md in the Checkpoint 3B format: package
status/branches/ranges/points, actual commands/counts, manual verification script,
decisions, unresolved risks and Jira-ready title/acceptance criteria per package.
Include ALERT_DEFAULTS_DESIGN.md, CERTIFICATES_DECISIONS.md and
APPLICATION_ALERT_SENDING_DESIGN.md as proposals only. Preserve historical reviews
and distinguish merged source, local work, owner reports and verified deployment.
Check branch before every commit. Run a non-empty git log identity range from
4b6e99bac4995fd3e36e6fbe1c7e3176383b6214 to HEAD and verify configured noreply
author/committer identities. No push, remote merge, connector write or deployment
unless Michael asks for that exact action. Stop and wait for review.
