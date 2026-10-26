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
   `private-media.tar.gz` into a ZIP in its private backup directory. When the
   deployed manifest explicitly has erasure_ledger_included=true, also include the
   checksum-listed `erasure-ledger.zip`. Never include arbitrary manifest paths.
   The enhanced command signs/checks source journals and refuses unresolved cleanup
   or unknown ledger entries. Set mode 0600,
   compute its SHA-256, and download using the authorized Files UI. This binary
   bundle avoids the browser's inline-JSON download ambiguity. Never include `.env`,
   WSGI configuration, keys, logs or unrelated backups.
7. Independently compare the downloaded ZIP hash, exact conditional member set, manifest
   completion and individual hashes. Extract into a new private isolated directory;
   integrity-check the copied database and safely extract only regular media files
   and directories under that directory. Compare file count/bytes with the manifest.
   Never restore over the live database or existing local developer data.
   If included, verify the bounded erasure ZIP inventory and per-journal hashes and
   retain it in the isolated restore. Independent hash verification needs no signing
   key; actual replay always requires the current private signature/identity checks.
   Never perform erasure/replay as part of this backup automation. The latest
   independent ledger must survive any restoration of an older snapshot.
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

21 October2026: scheduled run found an already verified snapshot from00:31 Nairobi
and skipped without a production pause. Source/archive hashes, both SQLite checks
and all12 restored files were independently rechecked. This proves the skip path,
not a new unattended snapshot. A later pre-release snapshot0857UTC was also verified
off server. The automation preserves optional erasure-ledger bundles where the
enhanced command is deployed; that new path is tested synthetically until used.

For unattended reliability when this desktop is off, provision an eligible
always-on scheduler with narrowly scoped private access; until then retain this
availability limitation and the manual recovery fallback in operational reporting.

## Reusable verifier

Where the operations package is installed, replace ad hoc verification scripts with:

```bash
python manage.py verify_private_backup --backup COMPLETED_BACKUP --restore-to NEW_PRIVATE_FOLDER
```

Omitting --restore-to performs hashes/integrity/archive checks without writing.
Actual restore verification requires a new private folder; existing destinations,
traversal, links, oversized expansion, mismatched inventory and partial manifests
are rejected. The same command works on a private downloaded backup in development
configuration. It never writes the live database. A source revision of unverified
in a Git-free packaged backup is explicit missing provenance, not a verified release.

### Access check and verified fallback - 23 October 2026

An empty browser-tab inventory does not establish that authentication expired.
Open the known PythonAnywhere dashboard and inspect the actual signed-in state
before deferring a backup. Never bypass a login challenge.

The development-run fallback completed a consistent database/media snapshot from
0678f404, restored the previously active web app and ingestion/sweep workflows,
then downloaded and independently verified the exact bundle and isolated restore.
The private receipt is outside Git under the owner's AjiriBackups directory.
This is evidence for a verified fallback, not an unattended scheduler execution.
Retention remains report-only; no retained backup was removed.

A second release fallback at 19:32 UTC on 23 October captured the changed database.
The exact off-server bundle and isolated restore passed before migrations; the
private receipt is retained outside Git. This also does not prove unattended execution.


## Scheduled fresh snapshot verified - 26 October 2026

The26October heartbeat created a fresh consistent snapshot at08:52UTC from source
f18d5b2173dc98cd8b88b082cb011ff4813ebf2e, after verifying no active Git/writer
operation and actual account quota444.2/512MB versus10,633,356 input bytes. Both
previously active workflows and enabled web app were paused, then restored and
verified before download; health returned200. No credentials/configuration changed.

Server verify_private_backup and independent off-server verification passed:
ZIP3,803,837 bytes; exact manifest/database/media member set, all hashes, both
SQLite integrity checks and safe isolated17-file/372876-byte restoration. The
manifest explicitly excluded an erasure ledger; no erasure/replay occurred. A
sanitized private receipt is retained outside Git. This verifies a fresh scheduled
run, not merely the earlier same-day skip or release fallback. Console login,
desktop availability and permissions remain real prerequisites for later runs.
Final quota457.9/512MB; no retained backup was deleted. Encryption remains unverified.

The first AX download click produced no local file/event. The observed exact ZIP
link was activated through the documented Playwright locator API and the resulting
local path was obtained from its download event before checksum verification.
Browser/UI uncertainty was not treated as a completed off-server backup.
