# Ajiri: setup

One git repository holds the whole project:

```
ajiri.co.ke/               the repository root (clone into a folder with this name)
  .github/workflows/       CI, scheduled ingestion, scheduled match sweep
  CLAUDE.md                rules and context for AI assistants working in this repo
  SETUP.md                 this file
  ajiri-backend/           Django API (also holds frontend_build/, the committed site build)
  ajiri-frontend/          React app
```

Keep the project outside OneDrive or any synced folder (for example `C:\dev`): syncing a
virtualenv, `node_modules` and a live database causes broken launchers and conflicts.

## 1. Get the code

```powershell
cd C:\dev
git clone https://github.com/michael-mathenge/ajiri.git ajiri.co.ke
cd ajiri.co.ke
```

The repository is private, so Git will ask you to sign in the first time.

## 2. Backend

```powershell
cd ajiri-backend
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
Copy-Item .env.example .env        # the example already says DEBUG=True
python manage.py migrate
python manage.py createsuperuser
python manage.py test              # expect: Ran 19 tests ... OK
python manage.py runserver
```

Python: 3.12 is the local default. CI also runs the checks and tests on 3.13
(PythonAnywhere's version) and 3.14.

## 3. Frontend

```powershell
cd ..\ajiri-frontend
npm install
npm run dev                        # http://localhost:5173
```

## 4. Changing the frontend

The site served in production is the committed build in `ajiri-backend/frontend_build/`.
After editing anything in `ajiri-frontend`, run:

```powershell
ajiri-backend\scripts\build_frontend.ps1
```

and commit the changed `frontend_build/` together with your source change. CI rebuilds the
frontend and fails the pull request if the two don't match.

## 5. Optional: Celery and Redis locally

Only needed to run the scheduled ingestion on your own machine; production uses GitHub Actions.

```powershell
docker start ajiri-redis
python -m celery -A config worker --loglevel=info -P solo      # in ajiri-backend, venv active
python -m celery -A config beat --loglevel=info                # second terminal
```

## 6. Day to day

- One branch per piece of work. Run `git branch` before you commit to confirm which one you're on.
- Open a pull request into `main`; CI must be green before you merge.
- Never commit `.env`, `db.sqlite3`, `media/`, `.venv` or `node_modules` (all git-ignored).

## 7. Deploying

Follow `ajiri-backend/docs/DEPLOY_PYTHONANYWHERE.md`.

## Sharing the project with an assistant

Preferred: `git bundle create ..\ajiri.bundle --all` makes one file holding the complete history.
If you zip instead, leave out `.venv`, `node_modules`, `db.sqlite3`, `media/`, `.env` and `.idea`:
they are large, regenerable, or private. Windows' zip tool has silently dropped files before,
so check the file count.
