# Ajiri

Job-matching and application platform for the Kenyan market.

## Layout

This whole folder is ONE git repository (remote: github.com/michael-mathenge/ajiri).

- `ajiri-backend/`: Django 6.1 + DRF + SimpleJWT. Celery + Redis are for local development
  only; production uses GitHub Actions (see `ajiri-backend/docs/DEPLOY_PYTHONANYWHERE.md`).
- `ajiri-frontend/`: React + Vite. Its production build is committed in
  `ajiri-backend/frontend_build/` (built by `ajiri-backend/scripts/build_frontend.ps1`);
  CI fails if the two disagree.
- `.github/workflows/`: CI, scheduled ingestion, scheduled match sweep. Must stay at the
  repository root.
- Environment: Windows + PowerShell. Python 3.12 venv at `ajiri-backend\.venv`.
  Use `python -m pip` and `curl.exe` (plain `curl` is a PowerShell alias for something else).

## How to work with me

I am learning DevOps and React while building this. Before each non-trivial command or edit,
explain in one or two sentences what it does and why. Prefer the smallest change that works.
Show me the diff before committing. Ask before any larger piece of work.

## Hard rules

- Before overwriting any file that has uncommitted changes, STOP and tell me. Back it up or
  stash it first. Never overwrite uncommitted work.
- Never replace, delete, or copy over `db.sqlite3`, `media/`, `.env`, or `.venv`. (A stale
  database file once silently wiped my users.)
- Never commit secrets or real keys, and never print them. `SECRET_KEY` and `INGEST_API_KEY`
  come from environment variables / `.env` only. Do not ask me to paste them into chat.
- Work on a feature branch. Never commit to `main`. Never push, merge, or open a PR without
  asking me first.
- Never run anything against production or an external service without asking.
- Before every commit run: from `ajiri-backend`, `python manage.py check` and
  `python manage.py test`; and if the frontend changed, from `ajiri-frontend`, `npm run lint`,
  then `ajiri-backend\scripts\build_frontend.ps1` and commit the refreshed `frontend_build/`.
  Everything must pass.

## Conventions

- New concepts get an entry in `ajiri-backend/docs/CONCEPTS.md`; code comments point to it as
  `# see docs/CONCEPTS.md#slug`. Every referenced slug must exist.
- Keep ingestion logic in `jobs/ingestion.py`; Celery tasks and API endpoints stay thin wrappers.
- Match the existing style: comments explain *why*, not *what*.
