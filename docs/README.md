# Ajiri Backend

Django REST API backend for Ajiri (ajiri.co.ke) — a Kenyan job-finding platform.

**Status:** Early development. Not deployed. Private repo.

**Completed phases:** Identity & Access ✅ · User Profile ✅ · Job Pipeline ✅ · Job Discovery ✅ · CV Upload ✅ · Automated CV Formatting ✅ · Automated Cover Letter Generation ✅
**Current phase:** Auto-Apply + Job Alerts (next up)

---

## Stack

- Python 3.12
- Django 6.1
- Django REST Framework 3.18 + SimpleJWT (JWT auth) + django-filter (query filtering)
- Celery 5.6 + Redis (Docker container `ajiri-redis`) — background jobs + scheduled tasks
- feedparser — RSS ingestion
- python-docx — generates CVs and cover letters as real .docx files from structured profile/job data
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

> **Still no `requirements.txt` generated as of this session — do this first next time:** `pip freeze > requirements.txt`, commit it. Until then, install manually:
> `pip install django djangorestframework djangorestframework-simplejwt django-filter celery redis feedparser python-docx`

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

Up to three processes, each in its own terminal tab:

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

If you pulled new code that changed `models.py` anywhere, also run `python manage.py migrate`.

**Before every `git commit`, run `git branch` first** to confirm you're on the feature branch you think you're on — this project has repeatedly (accidentally) committed feature work straight to `main` because a branch switch got lost mid-session after a debugging detour. Not catastrophic solo, but worth the 2-second habit.

---

## Project structure

```
ajiri-backend/
├── config/            # Project settings, URL routing, Celery app config
│   ├── settings.py
│   ├── celery.py      # Celery app instance, autodiscovers tasks.py in every app
│   └── urls.py
├── accounts/          # Custom User model (email, phone_number, full_name), JWT auth
├── profiles/          # Profile + Skill models, CV upload, CV generation
│   ├── cv_generator.py    # Generates a .docx CV from structured Profile data
│   └── serializers.py     # Note: full_name/phone_number live on User, not Profile —
│                           # see "Key architectural decisions" below for the read/write split
├── jobs/               # Job model, RSS ingestion, Celery tasks, scam filter, Discovery API, cover letters
│   ├── ingestion.py           # Pulls + parses MyJobMag Kenya RSS feed
│   ├── scam_filter.py         # Rule-based red-flag detection
│   ├── matching.py             # Profile-to-job skill match percentage (reused by cover letters too)
│   ├── filters.py              # django-filter FilterSet (location/job_type/skill)
│   ├── cover_letter_generator.py  # Generates a tailored .docx cover letter per job
│   └── tasks.py                # Celery task wrappers
├── docs/
│   ├── CONCEPTS.md     # Glossary of Django/DRF/git concepts learned along the way
│   └── Github.md       # Notes on git push output, PR workflow
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

---

## Known gotchas

- **Python 3.14 breaks Django 5.1+ admin.** Always use Python 3.12.
- **`InconsistentMigrationHistory`**: delete `db.sqlite3`, re-run `migrate` fresh — only safe with no real user data.
- **`curl` on Windows/PowerShell**: use `curl.exe` explicitly, not bare `curl`.
- **Django shell doesn't hot-reload**: exit and restart `python manage.py shell` after any code change.
- **`blank=True` ≠ a database default**: still need `default=''` (or `null=True`) or object creation without that field fails with `NOT NULL constraint failed`.
- **Celery token rotation**: `str(refresh)` alone does NOT create a new token — must `blacklist()` then `set_jti()`/`set_exp()`/`set_iat()` first.
- **`pip install python-docx` but `import docx`** — the PyPI package name and importable module name don't match. Easy to forget the install step exists at all since the import line looks self-contained.
- **When adding new imports/classes to an existing file, ADD to what's there — never regenerate the whole file from a partial snippet.** This session hit two real bugs (missing `generics`/`permissions` imports, a URL never registered) purely from a new code block replacing the top of a file instead of being inserted alongside existing imports. When in doubt, paste the full corrected file rather than a fragment.
- **`git rm --cached`** needed once for `celerybeat-schedule.*` — Celery Beat's local runtime state, correctly `.gitignore`'d now; harmless if they reappear untracked.

---

## Roadmap

1. ~~Custom User model~~ ✅
2. ~~Registration + login API (JWT)~~ ✅
3. ~~Profile editing~~ ✅
4. ~~Job ingestion (MyJobMag Kenya RSS, hourly via Celery Beat)~~ ✅
5. ~~Job search/browse + match-scoring~~ ✅
6. ~~CV upload~~ ✅
7. ~~Automated CV formatting (generate from profile data)~~ ✅
8. ~~Automated cover letter generation (match-score-aware)~~ ✅
9. **Auto-apply + job alerts** ← next up
10. M-Pesa / Visa / Mastercard payments
11. Subscription tiers
12. Employer dashboard
13. Production deploy → ajiri.co.ke

**Deferred to V2** (logged in Monday.com, Product discovery status): CV parsing/auto-extraction from uploaded files; AI-generated (vs. template-based) cover letter text; Salary Negotiation Coaching upsell with admin notification.

**CI/CD**: deliberately deferred. Scoped CI (GitHub Actions running `manage.py check` + migrations on every push) was proposed and would directly prevent the "forgot an import" class of bug this session hit twice — worth revisiting once a real test suite exists. Full CD waits until an actual deployment target exists (Staging/Production Deployment phase).

---

## Environment variables

None yet — `SECRET_KEY` in `settings.py` is Django's default, dev-only. Must move to env vars before deploying.

---

## Contact

Solo project — Michael Mathenge (michael@michaelmathenge.dev)
