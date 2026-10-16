# AGENTS.md: Ajiri Development Guide for Codex

> Codex reads this file at the start of every session. It is the source of truth for scope, rules and the definition of done. If it conflicts with a chat message from Michael, follow Michael and tell him about the conflict.

## 1. Mission

Implement the approved isolated Brevo HTTPS transport and transactional delivery
budget service on feature/brevo-delivery-service, following the reviewed schema
package. Michael approved counting definite failed provider attempts against daily
capacity. No new migration or dependency, endpoint/task wiring, auth/API behavior
change, real delivery, secrets, DNS/provider writes, pushes or deployment. Console
email remains unchanged. Stop after this package for review. This supersedes the
previous schema-only mission only for the authorized dormant service and tests.

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

## 4. Current state (Phase B schema preparation, 16 October 2026)

Michael deployed merged Phase A e4eaefd after verified DB/media backup and isolated
restore, plus a preserved virtualenv recovery copy. Production pins now report
Django 6.1.2/PyJWT 2.15.1. Owner-reported checks passed: health GET/HEAD, tokenless
refresh CSRF rejection, login/logout, profile save, owner download, private-media
404, ingestion run #32, log directory 0700 and backup dry-run (7 files). Live log
writing/rotation remains unverified. Redirect=False/HSTS=0 pending the host scheme
answer; no change authorized here.

The schema package was reviewed and approved locally. The dormant transport and
quota package is now authorized, with failed provider attempts counting against
capacity. Approved decisions are recorded in docs/MIGRATION_DESIGN_3B1.md.
Domain michaelmathenge.dev is active in Michael's Namecheap account using BasicDNS,
but not authenticated in Brevo. Inspection was read-only; no credentials, DNS,
provider setting or production changes. Existing original-checkout lockfile,
coverage data, stash and Git configuration must remain untouched. Queued UI changes
(no-skills prompt, registration styling, alert defaults) are not this package.

## 5. Known gotchas

- DRF validation errors are field-keyed arrays (`{"email": ["..."]}`); other errors are `{detail: "..."}`. The frontend must render **all** of them, never just the first.
- Paginated lists return `{count, next, previous, results}`, 20 per page.
- SimpleJWT: `str(refresh)` does not create a new token. Rotation needs `blacklist()` plus `set_jti()` / `set_exp()` / `set_iat()`. The refresh token must stay in the httpOnly cookie, never in the JSON body.
- Django: `blank=True` and `default=''` are different; mixing them causes NOT NULL failures. Dotted `source=` fields on DRF serializers can silently drop data; use `to_representation`.
- Never let an expired access token attach to login/register/refresh requests (public endpoints are excluded in the interceptor).
- Windows/PowerShell: use `curl.exe`, not `curl`. `-replace` is case-insensitive; use `-creplace` with `[regex]::Escape()`.
- Integrate new code alongside existing imports. Never overwrite file tops.

## 6. Current package

feature/brevo-delivery-service: isolated standard-library HTTPS adapter; atomic
Nairobi-day 200 total/150 application/30 account/20 alert and 10-user application
budgets; unique request keys; accepted/definite-failure/unknown outcomes. Definite
provider failures consume capacity. No provider automatic retries; uncertain or
crashed sends require reconciliation. Entire service disabled by default and unused
by current senders. Test concurrency/failures/security, run section 7 gates, document
activation prerequisites and stop. Do not choose unapproved alert/account retry or
attachment policy defaults. Frontend builds are verification only.

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

## 12. Delivery-service handback

Write docs/CHECKPOINT3B_DELIVERY_REVIEW.md with actual gates, new behavior and limits,
provider API reference, no-network test evidence, atomicity, failure accounting,
uncertainty/reconciliation, disabled activation and remaining decisions. Verify new
commit identities against configured noreply. No push/deployment; preserve original
checkout changes, stash and Git config. Stop after this package for Michael's review.
