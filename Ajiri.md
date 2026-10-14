# Ajiri.md: Development Guide for Codex

> Read this file fully at the start of every session. It is the source of truth for scope, rules and the definition of done. If this file conflicts with a chat message from Michael, follow Michael and tell him about the conflict.

## 1. Mission

Take Ajiri from "Phase 1 design system done" to **Checkpoint 1**: a fully working, tested, documented V1 candidate that Michael can review end-to-end. Work through the work packages in section 6 **without stopping between them**, unless a stop condition in section 8 applies. Stop at the checkpoint and report.

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
- CI exists (`.github/workflows/ci.yml`: backend checks, migrations, tests, frontend lint/build, committed-build consistency; Python matrix 3.12–3.14). Local dev and PythonAnywhere use Python 3.12.

## 4. Current state (as of Phase 1)

Done: design system, app shell, protected routes, themes, redesigned Login/JobList/JobDetail, `docs/DESIGN_SYSTEM.md`, `docs/PHASE1_REVIEW.md`.
Existing but unpolished: Register (shows only the first error), Applications, Notifications.
Missing: Profile page, CV UI, Subscriptions UI.
API gaps: `notify_email` / `notify_in_app` not in the profile serializer; matching ignores `notify_in_app`; no application dismiss endpoint; external-link sending only records confirmation; document downloads need authenticated blob handling.
Tests: 19 methods (ingestion, sweep, filename, admin, frontend fallback). None for accounts, profiles, auth, or most of the application lifecycle. No frontend tests.

**Precondition:** confirm Phase 1 is merged into `main`. If it is not, stop and ask.

## 5. Known gotchas

- DRF validation errors are field-keyed arrays (`{"email": ["..."]}`); other errors are `{detail: "..."}`. The frontend must render **all** of them, never just the first.
- Paginated lists return `{count, next, previous, results}`, 20 per page.
- SimpleJWT: `str(refresh)` does not create a new token. Rotation needs `blacklist()` plus `set_jti()` / `set_exp()` / `set_iat()`. The refresh token must stay in the httpOnly cookie, never in the JSON body.
- Django: `blank=True` and `default=''` are different; mixing them causes NOT NULL failures. Dotted `source=` fields on DRF serializers can silently drop data; use `to_representation`.
- Never let an expired access token attach to login/register/refresh requests (public endpoints are excluded in the interceptor).
- Windows/PowerShell: use `curl.exe`, not `curl`. `-replace` is case-insensitive; use `-creplace` with `[regex]::Escape()`.
- Integrate new code alongside existing imports. Never overwrite file tops.

## 6. Work packages (in order)

Each package gets its own branch off `integration/checkpoint-1` and must pass the quality gates (section 7) before it is merged into the integration branch.

| # | Branch | Scope | Done when |
|---|---|---|---|
| WP1 | `feature/profile-api-gaps` | Backend: expose `notify_email` / `notify_in_app` in the profile serializer; matching respects `notify_in_app`; add application dismiss endpoint (status to `dismissed`, owner only, guards for already-sent) | Tests cover each change, including permission and invalid-state cases |
| WP2 | `feature/register-applications-notifications` | Register shows all field errors. Applications: status badges, review draft, send, explicit employer-link step for external applications, dismiss. Notifications: unread state, mark read, empty/error states | Every flow works against the real API; each page has loading, error and empty states |
| WP3 | `feature/profile-cv` | Profile page (contact details, skills via `skill_names`, notification preferences, CV upload: PDF/DOC/DOCX, max 5 MB, validated client and server side). Authenticated blob download for generated CV and cover letter | Upload, edit and download work; file-type and size errors are clear |
| WP4 | `feature/subscriptions-ui` | Free / Starter / Pro (KES 0 / 499 / 999) plans page. **UI only, no payments.** Clearly labelled as not yet purchasable | Responsive, accessible, no dead buttons that imply payment works |
| WP5 | `feature/tests-and-ci` | Django tests for auth (register, login, refresh rotation, logout), profiles, matching edge cases, full application lifecycle. Frontend component/flow tests (set up Vitest + Testing Library) for Login, Register, Applications and Profile. Propose (do not silently rewrite) any CI changes | All tests pass locally; test commands documented |
| WP6 | `feature/checkpoint-polish` | Accessibility pass (keyboard, focus, contrast, labels), mobile pass at 375px, bundle-size check, README/docs update, final `frontend_build` | Checkpoint report complete |

Out of scope (V2): CV text extraction from uploads, AI-generated cover letter content, real payments (M-Pesa/Daraja), Postgres migration.

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

## 12. Checkpoint 1: what you hand back

Stop after WP6 and produce `docs/CHECKPOINT1_REVIEW.md`:

1. **Summary table:** each WP with status (done / partial / blocked / unverified), branch, and commit range
2. **What changed**, grouped by package
3. **Verification evidence:** actual commands run and their results (tests passed/failed counts, lint, build, bundle size)
4. **Michael's review script:** a step-by-step manual test path covering register, login, browse and filter jobs, apply, review and send an application, dismiss one, notifications, profile edit with CV upload, document downloads, dark mode, and mobile (375px), with what he should see at each step
5. **Decisions made and why**
6. **Open risks, assumptions and follow-ups**, including anything marked unverified
7. **Suggested story points** per package
8. **Recommended next sprint** (for example payments scoping, deployment verification, CI updates)

Then stop. Do not start new work until Michael reviews.
