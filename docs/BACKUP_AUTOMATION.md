# Automatic private backups

The active Codex automation **Verify and copy Ajiri daily backup**
(`verify-and-copy-ajiri-daily-backup`) is scheduled daily at **10:00 Africa/Nairobi**.
It coordinates the existing verified backup command and private off-server copy.
This is a desktop automation, not a PythonAnywhere scheduled task. The computer
and app must be available, the required signed-in connections must work, and
execution must have available usage/approvals. Missed or blocked runs are not
successful backups. See [official scheduled-task guidance](https://developers.openai.com/training/walkthroughs/scheduled-tasks).

Manual backup is a recovery fallback when automation cannot run, or when a release
needs a newer snapshot before migration. Do not substitute a reminder for an
executed, verified backup. Existing November readiness/renewal reminders remain.

## Daily run

1. Check the latest sanitized local receipt in `C:\Users\micha\AjiriBackups`.
   Skip if today's complete database/media snapshot already has an independently
   verified off-server copy and restore. Do not infer success from a directory name.
2. Read current production revision, Git-operation state, any active migration or
   deployment, and actual PythonAnywhere account quota. The shared filesystem's
   `df` free space is not the account allowance. Defer on an active operation or
   inadequate snapshot/verification headroom. Never prune backups automatically.
3. Record the current web-app and ingestion/sweep workflow states. Pause only
   enabled workflows; wait for existing writer runs to finish. Disable the web app
   only if enabled. Use the existing signed-in PythonAnywhere account and GitHub
   connection. Do not create or copy credentials.
4. In the existing Bash console, activate `workon ajiri` **before** strict shell
   options (virtualenvwrapper references unset variables). Run:

   ```bash
   cd /home/Mathenge/ajiri/ajiri-backend
   umask 077
   python manage.py backup_private_data \
     --destination /home/Mathenge/ajiri-private-backups \
     --include-media --writers-paused
   ```

   Never assert `--writers-paused` while a web worker or workflow can still write.
   The command must complete and publish `manifest.json`; partial directories are
   failed attempts, never usable backups. Verify every manifest hash and SQLite
   integrity, and reject archive links/traversal/special entries.
5. Restore the web app and workflows to their exact prior states immediately after
   the consistent snapshot, including on failure. Recheck HTTPS health. Do not keep
   writers paused during local download, and do not activate previously disabled
   services. A partial resume failure is urgent and must be reported.
6. Bundle only the completed `manifest.json`, `db.sqlite3` and
   `private-media.tar.gz` into a ZIP in its private backup directory. Set mode 0600,
   compute its SHA-256, and download using the authorized Files UI. This binary
   bundle avoids the browser's inline-JSON download ambiguity. Never include `.env`,
   WSGI configuration, keys, logs or unrelated backups.
7. Independently compare the downloaded ZIP hash, exact member set, manifest
   completion and individual hashes. Extract into a new private isolated directory;
   integrity-check the copied database and safely extract only regular media files
   and directories under that directory. Compare file count/bytes with the manifest.
   Never restore over the live database or existing local developer data.
8. Retain the verified off-server backup under the owner's local backup directory
   and a sanitized receipt with UTC time, source revision, hashes, counts and
   verification results. This local copy is not a public artifact or Git content.
   Do not claim disk encryption without verifying it separately. Keep retention
   **30 days DRAFT/report-only**: candidates are reported, not deleted.

Notify Michael on inaccessible sessions, approval/usage failures, quota shortage,
checksum/integrity failure or incomplete service resumption. Healthy routine runs
remain quiet. No purchase, account renewal, deployment or email is part of this job.

## Verification status

20 October 2026: automation created and active; its first scheduled execution is
**not yet verified**. The existing backup command and earlier off-server restore
rehearsal are verified separately; those do not prove that this new schedule ran.
Current release recovery evidence remains in the private 20 October backup folder.

For unattended reliability when this desktop is off, provision an eligible
always-on scheduler with narrowly scoped private access; until then retain this
availability limitation and the manual recovery fallback in operational reporting.
