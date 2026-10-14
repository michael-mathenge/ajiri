# CI proposal for Michael's approval

The existing `.github/workflows/ci.yml` is unchanged.

## Proposed change

Add the following frontend step after lint and before build:

```yaml
- run: npm run test -- --run
```

The test script is Vitest, using jsdom and React Testing Library. All packages are devDependencies in the existing lockfile; npm ci installs them. No browser installation or production service is needed.

Keep the backend Python 3.12 / 3.13 / 3.14 matrix, system check, migration check, full tests and committed frontend build comparison. Consider setting the backend job's EMAIL_BACKEND to django.core.mail.backends.locmem.EmailBackend for consistently captured synthetic emails. Correct the stale comment about PythonAnywhere's interpreter after verifying the hosting account; Michael specifies Python 3.12.

Do not add deployment or payments to this workflow. Run the actual GitHub Actions pipeline on a pull request before merging; local checks do not establish Linux or multi-version CI results.

## Local verification (PowerShell)

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

Expected: zero system-check issues, no migration drift, all tests pass, lint exits 0 and build exits 0. Regenerate frontend_build at the end of a frontend package using the existing build script; its tree must match dist.
