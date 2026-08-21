# Ajiri Backend

Django REST API backend for Ajiri (ajiri.co.ke) — a Kenyan job-finding platform.

**Status:** Early development. Not deployed. Private repo.

---

## Stack

- Python 3.12
- Django 6.1
- Django REST Framework 3.18
- SQLite (dev) — will move to Postgres later
- Windows / PowerShell dev environment

---

## Prerequisites

- Python 3.12 installed and available as `py -3.12` (Python 3.14 is known to break Django admin — do not use it)
- Git
- PyCharm (or any editor)

---

## First-time setup

Clone the repo, then from the project root:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install django djangorestframework
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

Run the dev server:

```powershell
python manage.py runserver
```

- App runs at: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

---

## Every time you come back to work on this

```powershell
cd ajiri-backend
.venv\Scripts\activate
python manage.py runserver
```

If you pulled new code that changed `models.py` anywhere, also run:

```powershell
python manage.py migrate
```

---

## Project structure


---

## Key architectural decisions

- **Custom User model (`accounts.User`)**: Login is by email (required), with an optional phone number field (for future M-Pesa integration). This was set up before any real data existed, since changing the User model after the fact is very difficult. Do not attempt to revert to Django's default User model.
- **`AUTH_USER_MODEL = 'accounts.User'`** is set in `../config/settings.py` — this line is load-bearing. Removing or changing it will break the entire auth system.

---

## Known gotchas

- **Python 3.14 breaks Django 5.1+ admin** (`AttributeError: 'super' object has no attribute 'dicts'`). Always use Python 3.12 for this project.
- If you ever see `InconsistentMigrationHistory` on `migrate`, it usually means the database was built before a model change (like the custom User model) was introduced. In early dev with no real data, the fix is: delete `../db.sqlite3`, then re-run `python manage.py migrate` fresh. **Do not do this once real user data exists.**

---

## Roadmap (rough order)

1. ~~Custom User model~~ ✅
2. Registration + login API (DRF, JWT-based)
3. Profile editing
4. Job ingestion from Kenyan job boards
5. Job search/browse
6. CV upload
7. M-Pesa / Visa / Mastercard payments
8. Subscription tiers
9. Automated CV formatting + cover letter generation
10. Auto-apply + job alerts
11. Employer dashboard
12. Production deploy → ajiri.co.ke

---

## Environment variables

None yet — using Django's default `SECRET_KEY` in `settings.py` for local dev only. **Before deploying**, this must move to an environment variable / `.env` file and never be committed to git.

---

## Contact

Solo project — Michael Mathenge (michael@michaelmathenge.dev)