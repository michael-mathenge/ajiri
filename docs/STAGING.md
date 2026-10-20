# Isolated staging (AJ-36)

This no-purchase staging environment is local and synthetic. It is not the public
PythonAnywhere app. Its database/media live in a separate named volume; the image
excludes local databases, media and environment files. Real email is forced off,
ingestion credentials are empty, the container runs as UID 10001, and port 8001 is
bound only to loopback. It does not reuse the Docker lesson on port 8000.

From `ajiri-backend` in the reviewed checkout:

```powershell
docker compose -p ajiri-roadmap-staging -f compose.staging.yaml build
docker compose -p ajiri-roadmap-staging -f compose.staging.yaml run --rm web python manage.py migrate --noinput
docker compose -p ajiri-roadmap-staging -f compose.staging.yaml up -d
curl.exe --fail http://localhost:8001/api/health/
```

Register a synthetic account and follow the user guide. Never enter real provider
keys or production account data. The frozen committed frontend is used, so rebuild
frontend_build before rebuilding the image when frontend source changes.

Stop with `docker compose -p ajiri-roadmap-staging -f compose.staging.yaml down`.
This preserves the staging volume. Do not add `--volumes` to routine cleanup.
PythonAnywhere remains a native WSGI deployment, not a Docker target.

Container build, fresh-volume migrations, health and journey results must be recorded
in JIRA_ROADMAP_PROGRESS.md; the presence of this file is not verification evidence.
