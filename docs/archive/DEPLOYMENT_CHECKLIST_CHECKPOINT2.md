> Historical Checkpoint 2 checklist, archived 21 October 2026. Use [the current release checklist](../DEPLOYMENT_CHECKLIST.md) for operations. Original text follows unchanged.

# PythonAnywhere Checkpoint 2 deployment checklist

**Michael performs these steps manually after reviewing and approving Checkpoint 2.**
Nothing here has been deployed by Codex. Do not deploy an unreviewed feature tip.
Use Python 3.12 locally and on PythonAnywhere; CI keeps 3.12/3.13/3.14.
This checklist supersedes older instructions to expose `/media/` publicly.

## 1. Review and prepare

- [ ] Review `CHECKPOINT2_REVIEW.md`, the approved private-media design, and actual
  CI results on a pull request. Approve/merge the selected revision yourself.
- [ ] Record the approved revision, previous deployment revision, effective DB
  path, previous MEDIA_ROOT and all Web → Static files mappings privately.
- [ ] Verify your backup restore procedure, available disk quota (copies plus
  backups), the current Python 3.12 virtualenv and web worker account.
- [ ] Choose a maintenance window and recovery owner. Pause uploads, application
  preparation/sending, ingestion/sweep callers and any Celery workers/Beat. Pause
  scheduled GitHub Actions from the dashboard if they target this deployment.
  Use the site's existing maintenance procedure. Do not continue if writers remain.
- [ ] Save a known legacy uploaded-CV URL and both application-document URLs for
  your own test account privately; these are sensitive. Prepare a second test user
  and a synthetic job/employer target. Never send a test to a real employer.

## 2. Back up before migrations or mapping changes

- [ ] In the PythonAnywhere **Bash** console, replace account/timestamp below.
  These variables must point at your verified deployment, not a guessed folder:

```bash
cd /home/YOURNAME/ajiri/ajiri-backend
workon ajiri
python --version
umask 077
OLD=/home/YOURNAME/ajiri/ajiri-backend/media
NEW=/home/YOURNAME/ajiri-private-media
AUDIT=/home/YOURNAME/ajiri-private-backups/checkpoint2-YYYYMMDD-HHMMSS
export AUDIT
test -d "$OLD" || exit 1
test -f db.sqlite3 || exit 1
mkdir -m 700 -p "$NEW" "$AUDIT"
chmod 700 "$NEW" "$AUDIT"
realpath "$OLD" "$NEW" "$AUDIT"
```

- [ ] Require Python 3.12. Check all resolved paths against the mapping table.
  Do not use chmod 777 or place private paths beneath any mapped directory.
- [ ] Back up the actual SQLite DB using its backup API (handles WAL contents),
  plus the full media tree and environment. Do not overwrite a previous backup.
  If your DB is not `db.sqlite3`, substitute its verified path before executing:

```bash
python -c 'import os, sqlite3; from pathlib import Path; src=sqlite3.connect("file:db.sqlite3?mode=ro", uri=True); dst=sqlite3.connect(str(Path(os.environ["AUDIT"])/"db.sqlite3")); src.backup(dst); result=dst.execute("PRAGMA integrity_check").fetchone()[0]; dst.close(); src.close(); assert result == "ok", result'
tar -czf "$AUDIT/media.tar.gz" -C "$OLD" .
tar -tzf "$AUDIT/media.tar.gz" >/dev/null
git rev-parse HEAD > "$AUDIT/previous-revision.txt"
if test -f .env; then cp -p .env "$AUDIT/environment.backup"; chmod 600 "$AUDIT/environment.backup"; fi
```

- [ ] Stop on any nonzero exit. Verify a restore to a separate private directory
  and inspect the restored database's integrity before changing live data. Record
  totals and checksums privately. No backups/manifests/environment files enter Git.

- [ ] Recovery gate: if backup integrity or restore rehearsal fails, stop before
  staging code, migration, relocation or mapping changes. Keep the original DB
  and files in place and correct the backup problem first.

## 3. Stage approved code, then migrate before activating it

```bash
cd /home/YOURNAME/ajiri
git status --short
git fetch origin
git switch --detach APPROVED_COMMIT
cd ajiri-backend
python manage.py check
python manage.py showmigrations jobs
python manage.py migrate --plan
```

- [ ] Do not switch with unexplained working changes. Replace APPROVED_COMMIT
  with the reviewed revision. Keep the web app in maintenance and do not reload
  into the new code yet. Staging code on disk precedes running its migration tools;
  **database migrations precede activation/reload**.
- [ ] Review the plan. Checkpoint 1 introduced `jobs/0007_notification_in_app`:
  existing notification rows default to in-app visibility. If absent it must be
  applied before the new code handles requests. WP7/WP8 add no migration.
- [ ] Stop if the plan includes unexpected or destructive migrations. Once the
  backed-up plan is approved, run:

```bash
python manage.py migrate --noinput
python manage.py showmigrations jobs
```

- [ ] Confirm `[X] 0007_notification_in_app` and all expected migrations applied.
  Do not edit migration history or reverse 0007 as a routine rollback. Auth/CORS,
  cookie settings, ingestion keys and the auth client remain unchanged.

- [ ] Migration recovery gate: on failure, keep maintenance in place and inspect
  the migration state and verified backup. Do not reload new code or automatically
  reverse migrations/restore the DB; use the reviewed recovery decision in section 7.

## 4. Relocate media while writers remain paused

The implemented command copies regular files, preserves all relative names and
bytes, and never deletes originals or updates DB rows. It includes unreferenced
files as private copies, rejects unsafe paths/symlinks/junctions, missing referenced
files and conflicting destinations, and resumes safely over identical files.
Dry-run is the default and writes nothing, including no manifest file.

```bash
python manage.py relocate_private_media --help
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --dry-run
```

- [ ] Review counts, missing references, destination safety, permissions and disk
  quota. Resolve every error before applying; never replace a missing snapshot
  with an empty file or regenerate a user's approved application.
- [ ] Run the copy with a fresh manifest path, then verify the complete source
  inventory and current references:

```bash
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --apply --manifest "$AUDIT/relocation.json"
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --verify
```

- [ ] Require exit 0, matching totals and verified hashes. Inspect the private
  manifest's copied/already-identical counts. If apply was interrupted, keep
  maintenance in place, fix the cause and rerun with a new manifest filename.
  Existing identical destination files are accepted; conflicts are never renamed
  or overwritten. The source is still intact. Manifests may contain personal names.
- [ ] Set `PRIVATE_MEDIA_ROOT=/home/YOURNAME/ajiri-private-media` in the existing
  private server configuration mechanism, usually `.env` beside manage.py.
  Real process environment overrides `.env`; confirm the effective root without
  printing secrets. Keep DEBUG=False and `.env` at 0600.
- [ ] Verify NEW directories are 0700 and files 0600 and the web account can
  read/write them. Verify newly created files receive these permissions too.
  The command sets copy permissions; Windows testing does not establish Linux
  permission enforcement. Never add a public mapping to fix a permissions error.

- [ ] Relocation recovery gate: if copy/verification fails, leave OLD intact and
  keep writers paused. Do not switch the root or reload. Correct the cause and
  rerun the safe copy, or stop cutover and retain the previous revision/root.

## 4a. Remove public media mappings before reload

- [ ] In PythonAnywhere **Web → Static files**, remove `/media/` and every alias
  or parent mapping that can expose old media, private media, backups or manifests.
  Retain public assets only. Do not map the whole repository or home folder.
- [ ] Keep all writers and public traffic paused. Mapping changes become effective
  on the platform reload below. Do not resume traffic while old public URLs work.
  If any alias cannot be removed, stop cutover and keep maintenance in place;
  application permissions cannot override platform mappings. Never restore a
  public mapping as rollback (see section 7).

## 5. Activate and verify before restoring traffic

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
```

- [ ] Use **Web → Reload** only after migration, relocation and configuration
  checks pass. Keep maintenance until the checks below pass.
- [ ] Repeat anonymous and signed-in GET/HEAD tests against all known old media
  URLs, aliases and hostnames with browser cache disabled. No private bytes may
  be served; `/media/` must not fall through to an SPA 200. Previously downloaded
  browser/proxy copies cannot be revoked by this deployment.
- [ ] Owner can download uploaded CV, saved CV and saved letter through their
  existing API endpoints. Check original bytes/filenames and private/no-store
  headers. Another user's snapshot request is 404; anonymous requests are 401.
- [ ] Upload a synthetic PDF/DOC/DOCX, prepare a synthetic application and download
  its snapshots. Verify new files appear only in NEW. Existing snapshot bytes
  remain unchanged after editing the profile. Fresh generators still work.
- [ ] Use captured/console email in a separate local or staging environment to
  run the double-send review below; do not change production mail settings just
  for this test. Inspect live error logs privately for storage/permission failures.
- [ ] Public static assets, login/refresh/logout, jobs, preferences and alerts
  still work. The existing frontend_build is unchanged.
- [ ] Recheck every static mapping, then resume traffic and paused callers.
  Keep OLD, the backup, and audit manifests private until an agreed retention
  review. No automated deletion/cleanup is introduced by this checkpoint.

- [ ] Activation recovery gate: any failed privacy/download/health check blocks
  resuming traffic. Keep mappings removed; restore the recorded revision/root only
  as described in section 7, preserving any new writes. Never fix a failed owner
  download by restoring a public mapping.
- [ ] After activation and privacy/health checks pass, resume exactly one scheduled
  ingestion run from the existing GitHub Actions workflow. Check its Actions result,
  HTTP success and expected job/no-duplicate outcome; then resume the normal
  schedule. No ingestion code/key changes are needed. A failed run blocks declaring
  deployment verified; inspect private logs without exposing X-Ingest-Key.

## 6. Local double-send verification (PowerShell)

Run the deterministic overlapping-request test, using only its synthetic DB,
temporary attachments and captured email. No server or real account is needed:

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py test jobs.test_send_concurrency --noinput
```

Expected: three tests pass. One test blocks request A at delivery while request B
tries to send with a stale ready-state read. B must receive 400; after A is released,
A receives 200 and exactly one email with saved attachments exists. A failure test
requires 502, restores ready_for_review with no timestamp, then a retry sends once.
A stale dismiss cannot overwrite the send claim. `sent` is visible while delivery
is pending; no new status or schema was introduced.

For a UI check in a captured-mail local environment, prepare a fresh synthetic
email application, open it in two signed-in tabs, approve both drafts, and trigger
send in both. Expect one success, one 400, and one captured message. Repeat with
another synthetic application if both tabs were not ready before the first send.
The automated test is the reliable overlap proof; manual tab timing alone is not.

## 7. Rollback without restoring the privacy leak

- [ ] Keep writers paused and mappings removed if any acceptance check fails.
  Do not restore `/media/`, a parent alias, or DEBUG media serving.
- [ ] Before any new writes, revert application revision/root setting to the
  recorded previous state so endpoints read intact OLD, then reload and verify
  owner access. Keep production DEBUG=False. 0007 is additive and normally stays.
- [ ] After new writes, preserve them: reconcile NEW into the old **unmapped**
  root with explicit inventory/hash/conflict review, or fix forward with NEW.
  Do not blindly copy over conflicts or restore an old DB over new user records.
- [ ] Database restoration, migration reversal, data deletion and source cleanup
  require a separate reviewed recovery decision. Recover from verified backups
  only while maintenance is in force; protect environment secrets throughout.
- [ ] Recheck privacy and owner downloads before resuming traffic. Document the
  outcome and retain audit evidence privately.

SMTP ambiguity is a separate recovery case: after a process crash or lost provider
acknowledgement, a claimed application can remain sent even if delivery is uncertain.
Check provider/server evidence manually before any reset/retry. No automatic reset
or exactly-once SMTP guarantee is provided; a server may accept email then raise.
