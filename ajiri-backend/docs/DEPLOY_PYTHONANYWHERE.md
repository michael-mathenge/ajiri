# Deploying Ajiri on PythonAnywhere (free tier)

How it fits together:

```
GitHub Actions (every 3h)  --downloads feed-->  MyJobMag
        |
        +--POST feed + X-Ingest-Key-->  https://YOURNAME.pythonanywhere.com/api/jobs/ingest/
                                          (Django + WhiteNoise + SQLite, serving the React app too)
```

PythonAnywhere's free tier can only reach whitelisted sites, so GitHub (open internet)
fetches the feed and pushes it in. Celery/Redis are not used in production.
Background reading: `docs/CONCEPTS.md` (`remote-ingestion`, `whitenoise`,
`spa-fallback-route`, `environment-variables`, `github-actions`).

Where each command runs is marked: **[PC]** your PowerShell, **[PA]** a PythonAnywhere
Bash console, **[Web]** a browser.

## Free-tier facts to know first

- The free site lives at `YOURNAME.pythonanywhere.com`. A custom domain such as
  `ajiri.co.ke` needs a paid plan.
- You must periodically click **Run until ... from today** on the Web tab or the site is
  disabled. Read the expiry date it shows and put a reminder in your calendar.
- 512 MB disk and a daily CPU-seconds allowance. `requirements-prod.txt` measures about
  120 MB installed. Watch the CPU figure on the Dashboard after the first few days.
- Email goes to the console backend: new-match alerts appear in the server log, not in
  anyone's inbox, until you configure SMTP (see `.env.example`).

## Part 0 - Prepare locally **[PC]**

1. Commit your work, push the branch, open a pull request and merge it into `main`.
   Scheduled GitHub workflows only run from `main`.
2. Create your local `.env` once: `Copy-Item .env.example .env`. Keep `DEBUG=True`.
3. Run the tests: `python manage.py test` (expect all green).
4. If you changed anything in `ajiri-frontend`, rebuild it: `.\scripts\build_frontend.ps1`,
   then commit the refreshed `frontend_build/`.

## Part 1 - Code and environment **[PA]**

1. Sign up for a free "Beginner" account at pythonanywhere.com. Remember your username.
2. Open **Consoles -> Bash** and run:
   ```bash
   git clone https://github.com/michael-mathenge/ajiri.git
   cd ajiri/ajiri-backend
   ```
   The repository holds both apps; the Django project is the `ajiri-backend` folder, and every
   later command in this runbook runs from there.
   If the repo is private, use a GitHub fine-grained token with read-only "Contents"
   access: `git clone https://TOKEN@github.com/michael-mathenge/ajiri.git`.
   If the clone fails with a network error, upload a zip through the **Files** tab
   and unzip it instead.
3. Create the virtualenv and install the server dependencies:
   ```bash
   python3.13 --version        # must print 3.13.x (Django 6.1 needs 3.12 or newer)
   mkvirtualenv ajiri --python=python3.13
   pip install -r requirements-prod.txt
   ```
4. Generate two secrets (run twice, copy each result somewhere safe, never into chat):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
5. Create the server's `.env`: `nano .env`, paste the following, fill in your username
   and the two secrets, then save (Ctrl+O, Enter, Ctrl+X):
   ```
   DEBUG=False
   SECRET_KEY=<first secret>
   ALLOWED_HOSTS=YOURNAME.pythonanywhere.com
   CSRF_TRUSTED_ORIGINS=https://YOURNAME.pythonanywhere.com
   INGEST_API_KEY=<second secret>
   ```
   Then `chmod 600 .env`.
6. Initialise the database and static files:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
   If settings fail with "SECRET_KEY is not set", the `.env` file is missing or misnamed.

## Part 2 - Web app **[Web]**

1. **Web** tab -> **Add a new web app** -> next -> **Manual configuration** -> **Python 3.13**.
   (Not the "Django" wizard option; that is for brand-new projects.)
2. **Virtualenv** section: enter `/home/YOURNAME/.virtualenvs/ajiri`.
3. Click the **WSGI configuration file** link. Delete its contents and paste
   `deploy/pythonanywhere_wsgi.py`, replacing `YOURNAME`. Save.
4. **Static files** section, add one mapping:
   | URL | Directory |
   |---|---|
   | `/media/` | `/home/YOURNAME/ajiri/ajiri-backend/media` |

   WhiteNoise already serves `/static/` and the React app; only uploaded CVs and
   cover letters need this mapping.
5. Turn on **Force HTTPS** if the Web tab offers it.
6. Click the green **Reload** button.

## Part 3 - Check the site **[Web]**

- `https://YOURNAME.pythonanywhere.com/` shows the Ajiri app.
- Refresh on `/login` (not just the home page): it must still load.
- `/admin/` shows a styled login page; sign in with the superuser.
- Register a normal user, then log in. In DevTools -> Application -> Cookies,
  `refresh_token` should be marked `HttpOnly` and `Secure`.

If something is broken, the **Error log** link on the Web tab is the first place to look.

## Part 4 - Scheduled ingestion **[Web: GitHub]**

1. Repository -> **Settings -> Secrets and variables -> Actions -> New repository secret**:
   - `AJIRI_BASE_URL` = `https://YOURNAME.pythonanywhere.com` (no trailing slash)
   - `INGEST_API_KEY` = the second secret from Part 1 (identical value)
2. **Actions** tab -> **Ingest jobs** -> **Run workflow**. Open the run. Expect
   `Downloaded N bytes` and then JSON such as `{"created":57,"skipped":0,...}`.
3. Reload the site: jobs are listed.
4. Run **Sweep matches** the same way once you have a user with skills.

Failure guide:

| Symptom | Likely cause |
|---|---|
| Download step fails with 403 or 429 | MyJobMag is blocking GitHub's servers. Tell me; we need another fetch route |
| Send step: 403 `Invalid or missing ingest key` | The two `INGEST_API_KEY` values differ, or `.env` has none. Reload after editing `.env` |
| Send step: 400 "Request body exceeded ... DATA_UPLOAD_MAX_MEMORY_SIZE" | Feed larger than 10 MB: raise that setting |
| Send step: 5xx or timeout | Check the PythonAnywhere error log; daily CPU allowance may be used up |
| Nothing runs on schedule | The workflow files are not on `main`; or GitHub disabled scheduled runs after a long period with no repository activity |

## Part 5 - Check the application flow **[Web]**

Apply to a job and open the **CV** link. A 404 there means the `/media/` mapping from
Part 2 is missing or wrong. Links should open over `https://`.

## Everyday operations

**Deploy an update** **[PA]**:
```bash
cd ~/ajiri && git pull
cd ajiri-backend
pip install -r requirements-prod.txt   # only needed if requirements changed
python manage.py migrate
python manage.py collectstatic --noinput
```
Then **Reload** on the Web tab.

**Backups:** the whole database is one file, `~/ajiri/ajiri-backend/db.sqlite3`. Download it from the
**Files** tab regularly. Never copy a database over a live one by accident: a stale copy
silently deletes every user created since.

**Renewal:** click **Run until ... from today** on the Web tab before the date shown.

## Known limits

- CVs and cover letters are served by obscure URL, not login (`unguessable-filenames`).
- SQLite allows one writer at a time; fine at demo scale.
- Alerts are not emailed until SMTP is configured (and free-tier outbound access is limited).
- The refresh/sweep jobs depend on GitHub Actions staying enabled.
