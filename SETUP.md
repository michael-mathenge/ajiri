# Developer quick start

Use Python 3.12 and Node 24.19. These commands are for a fresh local clone,
not production. Keep the project outside OneDrive or other synced directories.
Preserve an existing .venv, .env, database and private media; back up existing data
before migration. Never copy production data into a development image.

## 1. API (PowerShell)

```powershell
cd C:\dev
git clone https://github.com/michael-mathenge/ajiri.git
cd ajiri\ajiri-backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

The example enables local DEBUG. Keep real sending disabled. Explicitly using the
virtualenv executable works without activation. Docker has a separate Linux Python
environment; it does not use this Windows .venv.

## 2. Frontend (another PowerShell terminal)

```powershell
cd C:\dev\ajiri\ajiri-frontend
node --version # v24.19.x
npm ci
$env:VITE_API_BASE_URL = 'http://localhost:8000/api'
npm run dev
```

Open the printed Vite URL, normally http://localhost:5173. Use localhost for both
services for consistent cookies and CSRF origins. Register a synthetic account.
A fresh database has no jobs; use synthetic fixtures/admin, never the production
ingestion key. Registration alone does not prove a verification email was sent.

## 3. Verify a change

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:DEBUG = 'True'
$env:PYTHON_DOTENV_DISABLED = '1'
$env:REAL_EMAIL_ENABLED = 'False'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test --noinput
cd ..\ajiri-frontend
npm ci
npm run lint
npm run test -- --run
npm run build
```

Stop Vite before npm ci if Windows locks a native dependency. Test counts change;
read actual output instead of relying on old checkpoint counts. Use curl.exe in
PowerShell. Never publish console account-security links.

## 4. Release

Clear development VITE_API_BASE_URL overrides and run
`ajiri-backend/scripts/build_frontend.ps1` from the root. Commit its generated build
last; CI compares it with a clean build. Follow the deployment checklist: verified
backup, reviewed source/dependencies, expected migrations with writers paused,
activation, verification. Roll back code/configuration while preserving newer data
and additive schema; never routinely overwrite writes with an old database.

See [concepts](ajiri-backend/docs/CONCEPTS.md) for explanations and the Jira backlog
for scope. No secrets belong in Git or public VITE variables.
