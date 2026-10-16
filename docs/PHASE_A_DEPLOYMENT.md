# Phase A future release — Michael's server steps and rollback

Stage A at c4b9364 is owner-confirmed deployed on 16 October 2026. This runbook
does NOT deploy anything now. Phase A remains local and requires review, an exact
release SHA, authorized publication, passing CI and a separate deployment decision.
Do not substitute the current local integration tip for Michael's deployed SHA.
Stage B remains independent: keep Django redirect=False and HSTS=0 pending the
PythonAnywhere scheme answer. Preserve host Force HTTPS and all private mappings.

## WP16 release impact

WP16 changes documentation/evidence only; no dependency pins changed from c4b9364.
It requires no new migration, service or pip-audit installation on production.
If production already installed c4b9364's requirements, no additional upgrade is
needed for WP16. A future combined Phase A release still checks the actual venv
and installs the reviewed production requirements when necessary. Do not install
development requirements or scanners on the free-tier server for this release.

## Preflight and backup — before changing code or the active venv

In PythonAnywhere Bash, Michael runs:

```bash
cd /home/Mathenge/ajiri
workon ajiri
git status --short
git rev-parse HEAD
python --version
python -m pip --version
python -m pip check
python -c "from importlib.metadata import version; print('Django', version('Django')); print('PyJWT', version('PyJWT'))"
```

Require a clean checkout and expected current release c4b9364, Python 3.12 and the
ajiri virtualenv. Expected pinned versions: Django 6.1.2 and PyJWT 2.15.1. Stop on
unexpected versions/errors; do not silently downgrade or repair live dependencies.
Record the current full code SHA and non-sensitive package versions privately.
Verify backup freshness; pause writers and take/verify DB and private-media backups
using the existing DEPLOYMENT_CHECKLIST.md procedure, including off-server hashes
and isolated restore verification. The new WP22 command is not available on c4b9364.

If an actual package change is required, preserve a known-good environment before
touching the active one. If space cannot hold that recovery copy, stop and arrange
a reviewed recovery plan; never delete backups to make room. Unexpected dependency
drift requires review rather than a blind install on the serving venv.

## Stage the separately approved release, check dependencies, then activate

Only after review/publication/CI, replace the placeholder with that exact approved
SHA (not a floating main reference). No command here merges or pushes:

```bash
cd /home/Mathenge/ajiri
RELEASE_SHA='REPLACE_WITH_REVIEWED_FULL_PHASE_A_SHA'
git fetch origin
git rev-parse --verify "${RELEASE_SHA}^{commit}"
git merge-base --is-ancestor c4b9364 "$RELEASE_SHA"
git diff --name-only c4b9364 "$RELEASE_SHA" -- '*migrations*' '*requirements*'
```

Stop unless ancestry succeeds and no unexpected migration/requirement change is
present. Pause HTTP callers/writers using the owner's maintenance procedure before
switching the serving checkout or changing its venv; a worker restart can load new
files before an explicit reload. Do not rely on reload alone as a staging barrier.

```bash
git switch --detach "$RELEASE_SHA"
cd /home/Mathenge/ajiri/ajiri-backend
workon ajiri
python -m pip install --requirement requirements-prod.txt
python -m pip check
python -c "from importlib.metadata import version; print('Django', version('Django')); print('PyJWT', version('PyJWT'))"
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
```

The pip command is reconciliation to existing reviewed pins, not an unbounded
upgrade. Expect Django 6.1.2/PyJWT 2.15.1 and no new Phase A migration. Stop on
unexpected plans or failures. If already-current history has no pending operations,
`python manage.py migrate --noinput` is a no-op; otherwise obtain review first.
Do not add a Phase B migration to this release.

Privately configure exact `CSRF_TRUSTED_ORIGINS=https://mathenge.pythonanywhere.com`
for WP18's same-origin browser flow; do not expand CORS or trust proxy headers
without the host guarantee. Keep current redirect/HSTS-off values. Existing Secure
cookies remain enabled. CSRF origin validation needs the canonical HTTPS origin
even while the server's scheme handling is awaiting clarification.

Verify the existing throttle directory and create the private logging directory:

```bash
umask 077
mkdir -p /home/Mathenge/ajiri-private-logs
chmod 700 /home/Mathenge/ajiri-private-logs
stat -c '%U %a %n' /home/Mathenge/ajiri-private-logs
```

Expect owner Mathenge, mode 700; ensure no ancestor/link/static mapping exposes it.
Set PRIVATE_LOG_DIR to this path privately. Keep console mail unchanged. Reload
only after all preceding gates pass; resume callers after smoke checks.

Verify health GET/HEAD and no-store; CSRF bootstrap and rejected tokenless mutation;
login, refresh, logout, profile save, owner downloads, blocked direct media and
one normal ingestion run. Reload old browser tabs so server/client contracts match.
Check for unexpected redirect loops and private-log permissions/disk quota. Do not
deliberately break the production DB or exhaust production throttles. Follow the
Phase A review manual script and MONITORING_RUNBOOK.md. After release, rehearse
WP22 dry-run and isolated restore as documented in BACKUP_ROUTINE.md.

## Rollback

1. Pause callers/writers; preserve new DB writes, private files and diagnostic logs.
2. Restore the recorded known-good c4b9364 code/client/build as a pair:

   ```bash
   cd /home/Mathenge/ajiri
   git switch --detach c4b93647f65618e8d13f9baa47ded6d22a28f0fb
   cd ajiri-backend
   workon ajiri
   python -m pip install --requirement requirements-prod.txt
   python -m pip check
   python manage.py check
   ```

   Phase A and c4b9364 pins are identical: this does not roll back to vulnerable
   historical Django/PyJWT pins. If the venv is damaged, use the retained known-good
   environment/reviewed recovery plan; do not improvise dependency downgrades.
3. Restore reviewed prior non-secret configuration as needed, keeping shared cache,
   private media, host HTTPS and redirect=False/HSTS=0. Never disable WP18 CSRF on
   new code alone: roll back server and frontend together and reload old tabs.
4. Reload, verify login/download/privacy and normal ingestion, then resume callers.
   No Phase A schema reversal or routine old-DB restore is needed. Preserve backups;
   never overwrite newer writes with the pre-deployment database as routine rollback.
