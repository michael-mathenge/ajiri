# AGENTS.md: Ajiri Development Guide for Codex

> Codex reads this file at the start of every session. It is the source of truth for scope, rules and the definition of done. If it conflicts with a chat message from Michael, follow Michael and tell him about the conflict.

## 1. Mission

Deliver Checkpoint 3B Phase A locally on integration/checkpoint-3b, pinned to reviewed main c4b93647f65618e8d13f9baa47ded6d22a28f0fb. Michael confirmed Stage A deployed and verified on 16 October at this exact SHA; preserve that deployment base. Stage B remains pending PythonAnywhere's HTTPS scheme answer. Redirect/HSTS stay off until separately approved.

Only WP16, WP18, WP21 and WP22 plus Phase B migration DESIGN are authorized. WP18 narrowly permits CSRF protection on login/refresh/logout and a minimal existing-client extension, without changing token lifetimes/rotation/blacklisting. No model/migration changes, new dependencies, CORS or ingestion changes, CI edits, pushes, main merges, connector writes, production actions or secrets. Stop after the Phase A report and migration design. Section 9's older integration branch name is superseded for this checkpoint.

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

## 4. Current state (Checkpoint 3B Phase A, 16 October 2026)

Checkpoint 3A and PR #17 are merged at c4b9364; their CI passed. Michael reports Stage A deployed and reloaded on 16 October at this exact SHA, with SECURE_SSL_REDIRECT=False, SECURE_HSTS_SECONDS=0 and THROTTLE_CACHE_DIR writing counters. He verified weak-password rejection, login, jobs list, profile save and no public media mapping. This is owner-reported evidence, not an agent production inspection. Stage B awaits PythonAnywhere's HTTPS scheme answer. Private media, console-only mail and GitHub Actions ingestion remain. No 3B production actions are authorized.

Requirement scans on 16 October found no known vulnerabilities for production and development pins (Django 6.1.2, PyJWT 2.15.1); the older 15 findings concerned older pins and require documented reconciliation. Preserve Michael's dirty Dependabot lockfile, local coverage data and old stash. Fresh backup and basic disposable restore rehearsal were completed by Michael. Renewal/backup reminders are scheduled for 2/9 November at 09:00 Nairobi; last verified expiry 14 November. No expiry update is inferred.

## 5. Known gotchas

- DRF validation errors are field-keyed arrays (`{"email": ["..."]}`); other errors are `{detail: "..."}`. The frontend must render **all** of them, never just the first.
- Paginated lists return `{count, next, previous, results}`, 20 per page.
- SimpleJWT: `str(refresh)` does not create a new token. Rotation needs `blacklist()` plus `set_jti()` / `set_exp()` / `set_iat()`. The refresh token must stay in the httpOnly cookie, never in the JSON body.
- Django: `blank=True` and `default=''` are different; mixing them causes NOT NULL failures. Dotted `source=` fields on DRF serializers can silently drop data; use `to_representation`.
- Never let an expired access token attach to login/register/refresh requests (public endpoints are excluded in the interceptor).
- Windows/PowerShell: use `curl.exe`, not `curl`. `-replace` is case-insensitive; use `-creplace` with `[regex]::Escape()`.
- Integrate new code alongside existing imports. Never overwrite file tops.

## 6. Checkpoint 3B Phase A packages

| WP | Branch | Acceptance |
|---|---|---|
| WP16 | feature/dependency-advisories | Reconcile historical findings, retain current safe pins, capture scans and gates |
| WP18 | feature/refresh-cookie-csrf | Django CSRF bootstrap/token/origin validation; bounded client recovery and tests |
| WP21 | feature/health-and-logging | Minimal DB health, loose throttling, sanitized rotating per-process error logs |
| WP22 | feature/backup-routine | Private SQLite backup/optional media, dry-run and report-only DRAFT retention |

Branch packages from integration/checkpoint-3b and merge --no-ff after section 7 gates. Regenerate frontend_build once as WP18's last package commit. Use supported existing Node runtime. No actual migration, SMTP, password reset or email verification. Core concepts remain in ajiri-backend/docs/CONCEPTS.md. If main advances beyond the pinned deployment SHA, report it without silently rebasing.

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

## 12. Checkpoint 3B Phase A handback

Write docs/MIGRATION_DESIGN_3B1.md (design only; each future migration requires Michael's review) and docs/CHECKPOINT3B_PHASE_A_REVIEW.md in the 3A format, including actual gates, manual verification, deployment/session compatibility, rollback and open risks. Keep all Phase B implementations stopped. Backup retention defaults to 30 days DRAFT, lists candidates only, never deletes. PythonAnywhere's new free accounts lack scheduled tasks; document manual operation and conditional scheduling.

Check branch before each commit; preserve Git config/stash and unrelated work. Check every new commit author/committer against Michael's configured noreply identity. No pushes or production actions. Stop for migration-design review.

