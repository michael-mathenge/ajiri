# Ajiri

Ajiri helps job seekers in Kenya discover skill matches, prepare application documents, review applications and manage alerts. This repository contains a Django API and a React/Vite frontend in JavaScript/JSX.

## Checkpoint 1

Read [the review report](docs/CHECKPOINT1_REVIEW.md) for package status, test evidence, a manual review script and known limitations. Work is integrated on `integration/checkpoint-1`; it is not deployed or merged into main.

Implemented: registration/login, job filters and pagination, application review/send/external confirmation/dismissal, in-app notifications, profile/skills/preferences, CV uploads and authenticated document downloads. The plans page previews Free/Starter/Pro prices at KES 0/499/999; purchasing and entitlements are not implemented.

## Local setup (PowerShell)

Use the existing backend Python 3.12 environment. Never replace an existing .venv, database, media directory or .env. See [SETUP.md](SETUP.md) if starting a fresh clone.

```powershell
cd C:\dev\ajiri\ajiri-backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py showmigrations jobs
# Back up your existing local database before applying a new migration.
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Checkpoint 1 includes the approved additive jobs migration 0007_notification_in_app. It preserves existing alerts as visible. Development here used isolated test databases; your application database has not been migrated automatically.

In a second terminal:

```powershell
cd C:\dev\ajiri\ajiri-frontend
npm ci
$env:VITE_API_BASE_URL = 'http://localhost:8000/api'
npm run dev
```

Open the Vite URL, normally http://localhost:5173. Use localhost consistently for both frontend and API cookies. Stop Vite before npm ci on Windows to release its native-file lock.

## Checks

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
cd ..\ajiri-frontend
npm ci
npm run lint
npm run test -- --run
npm run build
```

For local email testing use the console or in-memory backend rather than sending to employers. Existing CI changes are proposed in [CI_PROPOSAL.md](docs/CI_PROPOSAL.md), not applied silently.

## Deployment build

PythonAnywhere serves committed static assets from ajiri-backend/frontend_build. No production Node service, Celery worker or Redis server is introduced. GitHub Actions ingestion and match sweeps remain unchanged; SQLite remains configured.

```powershell
cd C:\dev\ajiri
Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
.\ajiri-backend\scripts\build_frontend.ps1
```

Regenerate once at the end of a frontend package and commit that build last. No secrets belong in VITE_* variables: they are embedded in public JavaScript. See the [design system](docs/DESIGN_SYSTEM.md) and [concepts](ajiri-backend/docs/CONCEPTS.md).
