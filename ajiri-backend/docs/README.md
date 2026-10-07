# Ajiri Backend

Django REST API backend for Ajiri (ajiri.co.ke) — a Kenyan job-finding platform.

**Status:** In development. Deployment-ready (free-tier PythonAnywhere runbook written and rehearsed locally), not yet live. Private repo.

**Completed phases:** Identity & Access ✅ · User Profile ✅ · Job Pipeline ✅ · Job Discovery ✅ · CV Upload ✅ · Automated CV Formatting ✅ · Automated Cover Letter Generation ✅ · Auto-Apply ✅ · Job Alerts (email + in-app) ✅ · React frontend (walking skeleton) ✅ · Remote ingestion + deployment prep ✅
**Current phase:** First deployment — follow [`DEPLOY_PYTHONANYWHERE.md`](DEPLOY_PYTHONANYWHERE.md)

---

## Stack

- Python 3.12 locally (checks and tests also pass on 3.13, which PythonAnywhere runs, and 3.14)
- Django 6.1
- Django REST Framework 3.18 + SimpleJWT (JWT auth) + django-filter (query filtering)
- React + Vite frontend in the sibling `ajiri-frontend/` folder; its production build is committed in `frontend_build/` and served by Django through WhiteNoise (one origin, no CORS in production)
- Celery 5.6 + Redis (Docker container `ajiri-redis`) — **local development only**; production runs the same jobs from GitHub Actions
- GitHub Actions — CI (`ci.yml`) plus scheduled ingestion and match sweep (`ingest.yml`, `sweep.yml`)
- feedparser — RSS ingestion
- python-docx — generates CVs and cover letters as real .docx files from structured profile/job data
- python-dotenv — loads the git-ignored `.env` file; WhiteNoise — serves static files and the React build
- SQLite (local, and the free-tier deploy) — move to Postgres if the free tier is outgrown
- Windows / PowerShell dev environment
- Docker Desktop (for Redis only, and only if you run Celery locally)

---

## Prerequisites

- Python 3.12 installed and available as `py -3.12`
- Node.js (for the frontend)
- Git
- Docker Desktop (only if you want Redis/Celery locally)
- PyCharm (or any editor)

---

## First-time setup

Clone the repo (it holds both apps, `ajiri-backend/` and `ajiri-frontend/`; see the repository layout under "Project structure"), then from `ajiri-backend/` (the folder with `manage.py`):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`requirements.txt` is the development set (runtime packages plus IDE type stubs). The server installs the smaller `requirements-prod.txt`.

`.env` is git-ignored. The example already sets `DEBUG=True`, which is all local development needs. With `DEBUG` off and no `SECRET_KEY`, settings refuse to load — by design, so a misconfigured server fails loudly instead of running insecurely.

Apply database migrations and create an admin account:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

You'll be prompted for **email** (not username) and a password — this project uses a custom User model with email-based login.

Run the tests:

```powershell
python manage.py test
```

Optional — Redis for running Celery locally (only needs to be created once — after that, just start it):

```powershell
docker run -d --name ajiri-redis -p 6379:6379 redis:latest
```

---

## Every time you come back to work on this

Only the first two are needed for everyday work; each in its own terminal tab:

```powershell
# 1. Django dev server
cd ajiri-backend
.venv\Scripts\activate
python manage.py runserver

# 2. React dev server (talks to Django at http://127.0.0.1:8000 via ajiri-frontend/.env.development)
cd ajiri-frontend
npm run dev
```

Only if you want to run ingestion locally through Celery:

```powershell
docker start ajiri-redis
python -m celery -A config worker --loglevel=info --pool=solo
python -m celery -A config beat --loglevel=info
```

(`python -m celery` rather than bare `celery`: a virtualenv's `.exe` launchers hard-code its original path and break if the folder is ever moved.)

If you pulled new code that changed `models.py` anywhere, also run `python manage.py migrate`.

**Before every `git commit`, run `git branch` first** to confirm you're on the feature branch you think you're on — this project has repeatedly (accidentally) committed feature work straight to `main` because a branch switch got lost mid-session after a debugging detour. Not catastrophic solo, but worth the 2-second habit.

---

## Project structure

One git repository holds the whole project. The repository root is the folder *above* this one:

```
ajiri.co.ke/               # repository root (clone the repo into a folder with this name)
├── .github/workflows/     # ci.yml (backend + frontend checks), ingest.yml + sweep.yml (scheduled calls to the production API)
├── CLAUDE.md, SETUP.md    # rules for AI assistants; first-time setup
├── ajiri-frontend/        # React + Vite app
└── ajiri-backend/         # this Django project, described below
```

```
ajiri-backend/
├── config/            # Project settings, URL routing, Celery app config
│   ├── settings.py    # Environment-driven (.env); fail-safe defaults
│   ├── celery.py      # Celery app instance, autodiscovers tasks.py in every app
│   ├── urls.py        # API/admin routes, then a catch-all that serves the React app
│   └── views.py       # The catch-all view (index.html for client-side routes)
├── accounts/          # Custom User model (email, phone_number, full_name), JWT auth
├── profiles/          # Profile + Skill models, CV upload, CV generation
│   ├── cv_generator.py    # Generates a .docx CV from structured Profile data
│   └── serializers.py     # Note: full_name/phone_number live on User, not Profile —
│                           # see "Key architectural decisions" below for the read/write split
├── jobs/               # Job, Application, Notification; RSS ingestion; scam filter; Discovery API; cover letters
│   ├── ingestion.py           # ingest_feed(feed) processes a parsed feed; ingest_myjobmag_kenya() fetches then calls it
│   ├── scam_filter.py         # Rule-based red-flag detection
│   ├── matching.py             # Match percentage, match alerts, and the periodic sweep
│   ├── filters.py              # django-filter FilterSet (location/job_type/skill)
│   ├── cover_letter_generator.py  # Generates a tailored .docx cover letter per job
│   ├── utils.py                # Application-method detection, fix_mojibake()
│   ├── management/commands/    # fix_mojibake: one-off repair of mis-decoded text
│   └── tasks.py                # Celery task wrappers (local development)
├── deploy/             # WSGI file template for PythonAnywhere
├── scripts/            # build_frontend.ps1: builds the React app into frontend_build/
├── frontend_build/     # Committed production build of ajiri-frontend, served by Django
├── docs/
│   ├── README.md       # This file
│   ├── DEPLOY_PYTHONANYWHERE.md  # Step-by-step deployment runbook
│   ├── CONCEPTS.md     # Glossary of Django/DRF/React/git/DevOps concepts learned along the way
│   └── Github.md       # Notes on git push output, PR workflow
├── .env.example        # Template for the git-ignored .env
├── requirements.txt / requirements-prod.txt
├── manage.py
└── db.sqlite3          # Local dev database (not committed to git)
```

---

## Key architectural decisions

- **Custom User model (`accounts.User`)**: email login (required), phone_number and full_name both optional (`blank=True`). Set up before any real data existed.
- **`AUTH_USER_MODEL = 'accounts.User'`** in `config/settings.py` — load-bearing, do not remove.
- **Shared `Skill` model**: defined once in `profiles/models.py`, reused in `jobs/models.py`. This is what makes match-scoring possible across both CV/cover-letter generation and Discovery.
- **`full_name`/`phone_number` live on `User`, but are edited through the Profile API** — `ProfileSerializer` declares them as plain (non-`source=`) fields for reliable write behavior, and overrides `to_representation()` to explicitly pull the real values from `instance.user` on read. A dotted `source='user.full_name'` approach was tried first and silently dropped the fields from responses — avoid that pattern here.
- **CV and cover letter generation are template-based (python-docx), not AI-generated** — deliberate v1 choice: free, predictable, no external API dependency. Parsing an uploaded CV to auto-extract data, and AI-generated cover letter text, are both explicitly deferred to a "V2" phase (logged in Monday.com).
- **Cover letter tone is driven by `calculate_match_score()`** — the exact same function Discovery uses to show match percentages. Three tiers (≥75%, 40-74%, <40%) produce different opening-line language. One scoring function, reused everywhere match quality matters.
- **Match-scoring** (`jobs/matching.py`): percentage of a *job's* required skills that the profile has (not the other way around).
- **Scam filtering runs on ingestion**, not on read — checked once at creation time, cached on `is_flagged_scam`/`scam_flags`.
- **Discovery, CV generation, and cover letter generation all require authentication** — no anonymous access anywhere in this API by design.
- **Applications are created on demand, never automatically.** Clicking Apply generates the CV and cover letter once, snapshots the job's application method, and stores an `Application` for review; nothing is sent until the user confirms. Email-method jobs send a real email with both files attached; link-method jobs are just marked sent once the user says they applied.
- **Job alerts are automatic** because they cost nothing (an email and a database row). SMS/WhatsApp alerts are deferred until there is revenue to cover per-message costs.
- **Ingestion can be pushed in.** PythonAnywhere's free tier can only reach whitelisted sites, so a scheduled GitHub Actions workflow downloads the feed and POSTs it to `/api/jobs/ingest/`, protected by a shared secret (`X-Ingest-Key`), not a user login. `/api/jobs/sweep/` works the same way for the match sweep.
- **Configuration comes from the environment.** `DEBUG` defaults to off and a missing `SECRET_KEY` stops startup. Cookies are `Secure` whenever `DEBUG` is off.
- **One origin in production.** Django serves the built React app and its API together, so there's no CORS or cross-site cookie handling in production. CORS is only enabled for the Vite dev server.
- **Generated CVs get unguessable filenames** (random prefix), because `media/` files are served by URL without a login check. This is obscurity, not access control; serving them through an owner-checking view is the proper fix and is still to do.

---

## Known gotchas

- **Older notes claimed Python 3.14 breaks the Django admin.** With Django 6.1 the admin pages rendered fine on 3.14 in testing (and there's a test that opens them), so that no longer holds. 3.12 stays the local default because it's what the pinned requirements were generated on.
- **`InconsistentMigrationHistory`**: delete `db.sqlite3`, re-run `migrate` fresh — only safe with no real user data.
- **Never copy a `db.sqlite3` over a live one.** A snapshot silently deletes every account created since it was taken.
- **Virtualenvs are not relocatable.** Moving the project folder (it happened with OneDrive) breaks every `.exe` launcher inside `.venv\Scripts`. Recreate the venv, use `python -m ...`, and keep projects out of synced folders.
- **`curl` on Windows/PowerShell**: use `curl.exe` explicitly, not bare `curl`.
- **Django shell doesn't hot-reload**: exit and restart `python manage.py shell` after any code change.
- **`blank=True` ≠ a database default**: still need `default=''` (or `null=True`) or object creation without that field fails with `NOT NULL constraint failed`.
- **Celery token rotation**: `str(refresh)` alone does NOT create a new token — must `blacklist()` then `set_jti()`/`set_exp()`/`set_iat()` first.
- **A stale access token breaks public endpoints.** DRF authenticates before checking permissions, so an expired token sent to login/register is rejected even though those views allow anyone. The frontend never sends the token to those endpoints.
- **`pip install python-docx` but `import docx`** — the PyPI package name and importable module name don't match. Easy to forget the install step exists at all since the import line looks self-contained.
- **When adding new imports/classes to an existing file, ADD to what's there — never regenerate the whole file from a partial snippet.** This project hit real bugs (missing `generics`/`permissions` imports, a URL never registered) purely from a new code block replacing the top of a file instead of being inserted alongside existing imports. When in doubt, paste the full corrected file rather than a fragment.
- **`git rm --cached`** needed once for `celerybeat-schedule.*` — Celery Beat's local runtime state, correctly `.gitignore`'d now; harmless if they reappear untracked.
- **A zip of this project once arrived with three files missing** and no error. Cause unknown. When sharing the project as a zip, check the file count or use the checksum manifest from the clean copy.

---

## Roadmap

1. ~~Custom User model~~ ✅
2. ~~Registration + login API (JWT)~~ ✅
3. ~~Profile editing~~ ✅
4. ~~Job ingestion (MyJobMag Kenya RSS, hourly via Celery Beat; or pushed in from GitHub Actions)~~ ✅
5. ~~Job search/browse + match-scoring~~ ✅
6. ~~CV upload~~ ✅
7. ~~Automated CV formatting (generate from profile data)~~ ✅
8. ~~Automated cover letter generation (match-score-aware)~~ ✅
9. ~~Auto-apply + job alerts (email + in-app)~~ ✅
10. ~~React frontend, walking skeleton (register, log in, browse, apply, review/send, notifications)~~ ✅
11. **First deployment on PythonAnywhere (free tier)** ← next up
12. Authenticated CV/cover-letter downloads (owner-only)
13. M-Pesa / Visa / Mastercard payments
14. Subscription tiers
15. Employer dashboard
16. Custom domain → ajiri.co.ke (needs a paid hosting plan)

**Deferred to V2** (logged in Monday.com, Product discovery status): CV parsing/auto-extraction from uploaded files; AI-generated (vs. template-based) cover letter text; Salary Negotiation Coaching upsell with admin notification; SMS/WhatsApp alerts.

**CI/CD**: CI exists — `.github/workflows/ci.yml` (at the repository root) runs on every push to `main` and every pull request. The backend job runs `manage.py check`, a missing-migrations check and the full test suite on Python 3.12, 3.13 and 3.14; the frontend job runs lint and a production build, and fails if the committed `ajiri-backend/frontend_build/` doesn't match what that build produces. Deployment is manual for now: `git pull`, `migrate`, `collectstatic`, then Reload on PythonAnywhere (see the runbook).

---

## Environment variables

Set in the git-ignored `.env` file (copy `.env.example`) or in the server environment. Real environment variables win over `.env`.

| Variable | Purpose | Default |
|---|---|---|
| `DEBUG` | Development mode. Leave off in production | off |
| `SECRET_KEY` | Django signing key. Required when `DEBUG` is off | none (startup fails) |
| `ALLOWED_HOSTS` | Comma-separated hostnames, e.g. `yourname.pythonanywhere.com` | empty |
| `CSRF_TRUSTED_ORIGINS` | Origins with scheme, for admin login over HTTPS | empty |
| `INGEST_API_KEY` | Shared secret for `/api/jobs/ingest/` and `/api/jobs/sweep/`. Must match the GitHub secret | empty (endpoints disabled) |
| `TRUST_PROXY_SSL_HEADER` | Believe the proxy's `X-Forwarded-Proto` (only if the host's proxy sets it) | off |
| `CORS_ALLOWED_ORIGINS` | Extra allowed origins | the Vite dev server when `DEBUG` is on, else none |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | Real email (SMTP) | console backend |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Redis for local Celery | `redis://localhost:6379/0` |

Never commit a real value. The old hard-coded `SECRET_KEY` is in git history — treat it as public.

---

## Contact

Solo project — Michael Mathenge (michael@michaelmathenge.dev)
