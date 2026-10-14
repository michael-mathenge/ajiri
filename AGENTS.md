# AGENTS.md: Ajiri Development Guide for Codex

> Codex reads this file at the start of every session. It is the source of truth for scope, rules and the definition of done. If it conflicts with a chat message from Michael, follow Michael and tell him about the conflict.

## 1. Mission

Prepare **Checkpoint 2: private media protection** from reviewed Checkpoint 1 on up-to-date main. The current authorization is documentation only: update sections 1, 4, 6 and 12 of this guide and write `docs/PRIVATE_MEDIA_DESIGN.md`. Stop for Michael's approval before implementation.

Sections 1, 4, 6 and 12 are time-bound. Sections 2, 3, 5 and 7-11 remain unchanged. Michael's current instruction to use `integration/checkpoint-2` supersedes the Checkpoint 1 branch name in standing section 9 for this preparation only. No Prompt 2 exceptions have been received or applied.

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

## 4. Current state (Checkpoint 2 preparation, 15 October 2026)

Checkpoint 1 (WP1-WP6) is reviewed and merged into main at `e5e0038`; its integration tip `b8c1881` is an ancestor. It includes profile preferences, independent alerts, application review/send/dismissal, registration errors, notifications, Profile/CV tools, authenticated downloads, plans preview, tests and polish. Recorded Checkpoint 1 results: 57 Django tests and 24 frontend tests; see `docs/CHECKPOINT1_REVIEW.md` for evidence and limits, not a claim of a new run.

Remaining privacy gap: files beneath the existing media root can bypass owner-checked download endpoints via public media URLs. Django exposes media in DEBUG mode; the PythonAnywhere runbook specifies a public media mapping. Live hosting configuration has not been inspected.

Precondition: verify complete Checkpoint 1 ancestry in fetched origin/main before starting. Preparation changes only this guide and the private-media design; existing auth, CORS and download endpoint behaviour remain unchanged. No file relocation, migration, hosting operation or implementation is authorized yet.

## 5. Known gotchas

- DRF validation errors are field-keyed arrays (`{"email": ["..."]}`); other errors are `{detail: "..."}`. The frontend must render **all** of them, never just the first.
- Paginated lists return `{count, next, previous, results}`, 20 per page.
- SimpleJWT: `str(refresh)` does not create a new token. Rotation needs `blacklist()` plus `set_jti()` / `set_exp()` / `set_iat()`. The refresh token must stay in the httpOnly cookie, never in the JSON body.
- Django: `blank=True` and `default=''` are different; mixing them causes NOT NULL failures. Dotted `source=` fields on DRF serializers can silently drop data; use `to_representation`.
- Never let an expired access token attach to login/register/refresh requests (public endpoints are excluded in the interceptor).
- Windows/PowerShell: use `curl.exe`, not `curl`. `-replace` is case-insensitive; use `-creplace` with `[regex]::Escape()`.
- Integrate new code alongside existing imports. Never overwrite file tops.

## 6. Checkpoint 2 preparation (in order)

| Step | Scope | Done when |
|---|---|---|
| 1 | Verify fetched main contains Checkpoint 1 WP1-WP6 | Stop if it does not; record verified base |
| 2 | Create `integration/checkpoint-2` from up-to-date main | No commit on main; check branch before every commit |
| 3 | First commit: documentation only | Update only time-bound AGENTS sections and add private-media design |
| 4 | Design review | Document current storage/serving, 2-3 options, recommendation, migration impact, dry-run relocation contract, manual PythonAnywhere steps, tests and rollback |
| 5 | Stop | Hand back the design and wait for Michael's approval |

Later implementation packages and any Prompt 2 exceptions are pending explicit instructions. Do not invent or start them. No source, dependencies, auth, CORS, CI, deployment or generated build changes during preparation. Hosting steps are instructions for Michael only.

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

## 10. Do not touch without asking

`AUTH_USER_MODEL` and migration history; the SimpleJWT cookie/rotation logic; `src/api/client.js` interceptor behaviour (extend, do not rewrite); CORS settings; ingestion endpoints and `X-Ingest-Key` handling; CI workflow (propose changes in the report); hosting config.

## 11. Working with Michael

- Michael is a Senior Scrum Master and solo developer, learning React. Explain the *why* of non-obvious choices in short code comments and in the report.
- Be direct. Push back when something is risky or wrong, and explain why.
- Give exact PowerShell commands for anything he needs to run, plus the expected result.
- Michael tracks work in Monday.com himself. Give completed items and honest story-point suggestions per package; do not assume any Monday.com access.

## 12. Checkpoint 2 preparation: what you hand back

Deliver `docs/PRIVATE_MEDIA_DESIGN.md` and the time-bound AGENTS update in a documentation-only first commit on `integration/checkpoint-2`.

Report the verified main/base commit, branch and documentation commit; recommended approach and migration/data impact; checks actually run and any unverified checks; unchanged standing rules and runtime/hosting scope; and confirmation that the commit author/committer use Michael's configured noreply address without changing Git config.

Stop after these documents. Wait for Michael's approval before implementation or hosting changes.
