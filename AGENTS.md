# AGENTS.md: Ajiri Development Guide for Codex

> Codex reads this file at the start of every session. It is the source of truth for scope, rules and the definition of done. If it conflicts with a chat message from Michael, follow Michael and tell him about the conflict.

## 1. Mission

Prepare Checkpoint 3 on `integration/checkpoint-3`: documentation only. First commit updates AGENTS.md; second adds docs/CHECKPOINT3_PLAN.md and docs/SMTP_EMAIL_DESIGN.md. Stop for Michael's answers and approval. No application code, migrations, dependencies, CI changes, pushes, connector writes or production operations.

Sections 1, 4, 6 and 12 are time-bound. This checkpoint supersedes section 9's old integration branch name and section 8's instruction to continue implementing packages. Candidate packages are proposals, not implementation authorization. Michael's documentation-only validation instructions apply this round; section 7's application gates remain standing rules for future implementation.

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

## 4. Current state (Checkpoint 3 preparation, 15 October 2026)

Checkpoint 1 (WP1-WP6) and Checkpoint 2 (WP7-WP10) are merged. Main and origin/main were verified against the live remote at `2d5d175`, with a clean working tree before preparation. Ajiri is live at https://mathenge.pythonanywhere.com on PythonAnywhere's free tier, deployed from that revision.

Private media storage is in place outside public static mappings; owner-checked downloads remain available. Production uses Django's console email backend, so no real email is delivered. GitHub Actions performs ingestion and matching sweeps. The PythonAnywhere web app must be renewed periodically; the last deployment dashboard showed 14 November 2026 as its expiry, which Michael must recheck.

Prior deployment evidence records direct media URLs 404, owner downloads 200, non-owner 404 and anonymous 401, plus one successful ingestion run with 99 active jobs. These are historical results, not new checks this round. Three harmless probe files, an inactive test job and disabled synthetic users remain a housekeeping backlog.

The old stash contains only an earlier AGENTS.md GitHub write-permission rule. Do not apply, drop or modify it. SMTP/provider access, product restoration behaviour and privacy/retention choices require decisions before implementation.

## 5. Known gotchas

- DRF validation errors are field-keyed arrays (`{"email": ["..."]}`); other errors are `{detail: "..."}`. The frontend must render **all** of them, never just the first.
- Paginated lists return `{count, next, previous, results}`, 20 per page.
- SimpleJWT: `str(refresh)` does not create a new token. Rotation needs `blacklist()` plus `set_jti()` / `set_exp()` / `set_iat()`. The refresh token must stay in the httpOnly cookie, never in the JSON body.
- Django: `blank=True` and `default=''` are different; mixing them causes NOT NULL failures. Dotted `source=` fields on DRF serializers can silently drop data; use `to_representation`.
- Never let an expired access token attach to login/register/refresh requests (public endpoints are excluded in the interceptor).
- Windows/PowerShell: use `curl.exe`, not `curl`. `-replace` is case-insensitive; use `-creplace` with `[regex]::Escape()`.
- Integrate new code alongside existing imports. Never overwrite file tops.

## 6. Checkpoint 3 candidate work packages

| WP | Proposed branch | Planning scope |
|---|---|---|
| WP11 | feature/email-delivery | SMTP/API provider design, sender identity, delivery failures and shared sending limits |
| WP12 | feature/application-restore | Product choice: restore saved snapshots to review versus re-draft |
| WP13 | feature/privacy-consent | DRAFT privacy notice, registration acknowledgement and optional consent; legal review required |
| WP14 | feature/account-data-rights | Export, deletion and backup retention options; destructive steps require separate approval |
| WP15 | feature/basic-monitoring | Sanitized logging, minimal health endpoint and manual operations routine |

Recommended future order: WP13, WP15, WP11, WP12, WP14. Only the integration planning branch is created now. Do not create feature branches or implement packages before Michael answers the questions and approves their designs. Housekeeping is list-only.

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

## 12. Checkpoint 3 preparation handback

Deliver docs/CHECKPOINT3_PLAN.md and docs/SMTP_EMAIL_DESIGN.md. Include scope, likely files, migration/destructive impact, tests, risks, suggested points and decisions for each candidate. Include provider verification limits, manual-only server instructions and rollback. End the plan with recommended order, dependencies, branch names and numbered questions for Michael.

Check the branch before each commit. Preserve Git configuration and the old stash. Validate documentation diffs, scope, links and absence of secrets; report actual checks without implying application suites were rerun. Before handback run `git log --format="%h %ae | %ce" origin/main..integration/checkpoint-3` and confirm all authors/committers use Michael's configured noreply address. Stop after the documentation commits and wait for answers and approval.
