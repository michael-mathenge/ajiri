# Ajiri Backend

Django REST API backend for Ajiri (ajiri.co.ke) — a Kenyan job-finding platform.

**Status:** Early development. Not deployed. Private repo.

**Completed phases:** Identity & Access ✅ · User Profile ✅ · Job Pipeline ✅ · Job Discovery ✅
**Current phase:** CV & Application Assets (CV upload, automated formatting, cover letter generation)

---

## Stack

- Python 3.12
- Django 6.1
- Django REST Framework 3.18 + SimpleJWT (JWT auth) + django-filter (query filtering)
- Celery 5.6 + Redis (Docker container `ajiri-redis`) — background jobs + scheduled tasks
- feedparser — RSS ingestion
- SQLite (dev) — will move to Postgres later
- Windows / PowerShell dev environment
- Docker Desktop (for Redis only, right now — the Django app itself still runs natively)

---

## Prerequisites

- Python 3.12 installed and available as `py -3.12` (Python 3.14 is known to break Django admin — do not use it)
- Git
- Docker Desktop (for Redis)
- PyCharm (or any editor)

---

## First-time setup

Clone the repo, then from the project root:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> Note: a `requirements.txt` hasn't been generated yet — run `pip freeze > requirements.txt` next session so this step is real. Until then, install manually: `pip install django djangorestframework djangorestframework-simplejwt django-filter celery redis feedparser`

Start the Redis container (only needs to be created once — after that, just start it):

```powershell
docker run -d --name ajiri-redis -p 6379:6379 redis:latest
```

Apply database migrations:

```powershell
python manage.py migrate
```

Create an admin account:

```powershell
python manage.py createsuperuser
```

You'll be prompted for **email** (not username) and a password — this project uses a custom User model with email-based login.

---

## Every time you come back to work on this

You need **up to three processes running simultaneously**, each in its own terminal tab:

```powershell
# 1. Make sure Redis is running (skip if already up)
docker start ajiri-redis

# 2. Django dev server
cd ajiri-backend
.venv\Scripts\activate
python manage.py runserver

# 3. Celery worker (only needed to test/run ingestion manually or via Beat)
celery -A config worker --loglevel=info --pool=solo

# 4. Celery Beat (only needed if testing the hourly auto-schedule)
celery -A config beat --loglevel=info
```

If you pulled new code that changed `models.py` anywhere, also run:

```powershell
python manage.py migrate
```

---

## Project structure

```
ajiri-backend/
├── config/            # Project settings, URL routing, Celery app config
│   ├── settings.py
│   ├── celery.py      # Celery app instance, autodiscovers tasks.py in every app
│   └── urls.py
├── accounts/          # Custom User model, JWT auth (register/login/refresh/logout)
├── profiles/           # Profile + Skill models, auto-created via signal, CRUD API
├── jobs/               # Job model, RSS ingestion, Celery tasks, scam filter, Discovery API
│   ├── ingestion.py    # Pulls + parses MyJobMag Kenya RSS feed
│   ├── scam_filter.py  # Rule-based red-flag detection
│   ├── matching.py     # Profile-to-job skill match percentage
│   ├── filters.py      # django-filter FilterSet (location/job_type/skill)
│   └── tasks.py        # Celery task wrappers
├── docs/
│   ├── CONCEPTS.md     # Glossary of Django/DRF/git concepts learned along the way
│   └── Github.md       # Notes on git push output, PR workflow
├── manage.py
└── db.sqlite3          # Local dev database (not committed to git)
```

---

## Key architectural decisions

- **Custom User model (`accounts.User`)**: Login is by email (required), with an optional phone number field (for future M-Pesa integration). Set up before any real data existed, since changing the User model after the fact is very difficult. Do not attempt to revert to Django's default User model.
- **`AUTH_USER_MODEL = 'accounts.User'`** is set in `config/settings.py` — this line is load-bearing.
- **Shared `Skill` model**: defined once in `profiles/models.py`, reused (not duplicated) in `jobs/models.py` via `skills_required = ManyToManyField(Skill, ...)`. This is what makes match-scoring possible — a profile's skills and a job's required skills point at the exact same underlying rows.
- **Match-scoring** (`jobs/matching.py`): percentage of a *job's* required skills that the profile has (not the other way around) — reflects "how qualified am I for this job," not "how much of my skillset is relevant here."
- **Scam filtering runs on ingestion**, not on read — every job gets checked once at creation time (`jobs/ingestion.py`), result cached on `is_flagged_scam` / `scam_flags`, rather than re-scanning on every API request.
- **Discovery requires authentication** — browsing jobs at all requires a valid JWT; there's no anonymous job browsing by design.

---

## Known gotchas

- **Python 3.14 breaks Django 5.1+ admin** (`AttributeError: 'super' object has no attribute 'dicts'`). Always use Python 3.12.
- **`InconsistentMigrationHistory`**: usually means the database was built before a model change was introduced. In early dev with no real data, fix: delete `db.sqlite3`, then re-run `python manage.py migrate` fresh. **Do not do this once real user data exists.**
- **`curl` on Windows/PowerShell**: PowerShell aliases `curl` to `Invoke-WebRequest`, which uses different syntax. Use `curl.exe` explicitly.
- **Django shell doesn't hot-reload**: if you edit `models.py` (or anything) while a `python manage.py shell` session is open, that session still has the *old* code in memory. Exit and restart the shell after any code change.
- **`blank=True` ≠ a database default**: `blank=True` only relaxes form/admin validation. A `TextField`/`CharField` still needs `default=''` (or `null=True`) to avoid `NOT NULL constraint failed` when creating objects without that field set directly (e.g. in a shell or script).
- **Celery token rotation gotcha**: just calling `str(refresh)` again does NOT create a new token — you must call `refresh.blacklist()` then `set_jti()`/`set_exp()`/`set_iat()` before re-stringifying, or rotation silently no-ops. (Full writeup in `docs/CONCEPTS.md`.)
- **`git rm --cached`** needed for `celerybeat-schedule.*` files — these are Celery Beat's local runtime state and were accidentally committed once before `.gitignore` caught them. If they reappear untracked, that's normal (Beat regenerates them on start) and they should NOT be re-added.

---

## Roadmap

1. ~~Custom User model~~ ✅
2. ~~Registration + login API (DRF, JWT-based)~~ ✅
3. ~~Profile editing~~ ✅
4. ~~Job ingestion from Kenyan job boards~~ ✅ (MyJobMag Kenya RSS, hourly via Celery Beat)
5. ~~Job search/browse + match-scoring~~ ✅
6. **CV upload** ← current phase
7. Automated CV formatting + cover letter generation
8. M-Pesa / Visa / Mastercard payments
9. Subscription tiers
10. Auto-apply + job alerts
11. Employer dashboard
12. Production deploy → ajiri.co.ke

**Other job sources considered but not yet built** (see chat history for evaluation): jikAPI (community Kenya jobs API), Apify scraper-as-a-service, direct web scraping, manual/CSV bulk import. MyJobMag RSS was chosen first as the most legitimate, lowest-risk source to start with.

---

## Environment variables

None yet — using Django's default `SECRET_KEY` in `settings.py` for local dev only. **Before deploying**, this must move to an environment variable / `.env` file and never be committed to git.

---

## Contact

Solo project — Michael Mathenge (michael@michaelmathenge.dev)
