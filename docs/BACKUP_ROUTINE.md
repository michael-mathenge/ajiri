# WP22 private backup routine — manual operation

Local implementation; not run on production by Codex. Database-only mode uses the
SQLite backup API and is safe with ordinary online SQLite writes (including WAL).
Media is a separate filesystem snapshot: pause ALL writers before --include-media
and explicitly attest with --writers-paused. That flag is an operator assertion,
not an automatic maintenance switch. Recheck source inventory after archiving;
detected changes abort the snapshot. Never claim an online DB/media point-in-time
snapshot without a paused-writer window.

## Michael's PythonAnywhere steps after a separate approved deployment

Confirm private DB/media paths, free disk quota, account ownership and every static
mapping first. This command must not alter Michael's currently pinned c4b9364
deployment; it is available only after a future Phase A release is reviewed.
No credentials or environment backup is included. Backups contain personal data:
0700 destination and 0600 files; do not place under the repo/public/media trees.

In PythonAnywhere Bash, run dry-run FIRST (read-only, creates no directories):

```bash
cd /home/Mathenge/ajiri/ajiri-backend
workon ajiri
python manage.py backup_private_data --destination /home/Mathenge/ajiri-private-backups --dry-run
```

Read the plan and report-only retention count, then create a DB-only backup:

```bash
python manage.py backup_private_data --destination /home/Mathenge/ajiri-private-backups
```

For media, first dry-run with --include-media. Pause uploads, application sends,
ingestion/sweeps and any other writers using the existing maintenance procedure,
wait for running jobs, then run:

```bash
python manage.py backup_private_data --destination /home/Mathenge/ajiri-private-backups --include-media --writers-paused
```

Stop on failure. Resume callers after a successful snapshot, and verify their next
normal run. No migration/deploy is performed by the command. SQLite copy has a
60-second progress deadline and 20-second lock timeout; on resource limits, keep
the incomplete snapshot private and review, do not disable integrity checks.

Completed folders are backup-<UTC timestamp>-<random suffix>. Failed snapshots stay
under .partial-backup-* and never appear as completed; do not use them for recovery.
Only a fully verified snapshot gets manifest.json and is renamed atomically into
the completed namespace. No prior backup or source DB is overwritten or deleted.

The manifest records source Git revision, UTC completion time, file hashes, media
counts and a complete marker. It contains no credentials, mail content or individual
media filenames. media_uncompressed hashes the decompressed tar stream, supporting
browsers that decompress a .gz download but retain its filename. Download manifest,
DB and optional archive to the already protected BitLocker folder; compare server
and downloaded manifest hashes too. Never download/paste credentials into chat.

## Retention: DRAFT, report-only

Default 30 days; BACKUP_RETENTION_DAYS or --retention-days overrides the positive
day count. The command lists only its own completed, manifest-bearing expired
snapshots as candidates. It NEVER prunes or deletes anything, even during real runs.
No --prune exists. Do not delete historical or partial backups automatically.
Legal/operational approval is required before any future deletion implementation.
Quota can fill despite rotation candidates: review usage manually and export
off-server copies; the tool cannot promise space for 30 days of snapshots.

## Scheduler feasibility, verified 16 October 2026

PythonAnywhere's new free accounts lack scheduled tasks. Grandfathered free accounts
(created before 15 January 2026 US / 8 January EU) allow one daily task, up to two
hours. Paid accounts allow up to 20 hourly/daily tasks, up to 12 hours. Mathenge's
new free account must use the manual runbook; no scheduler or paid service is added.
Sources: https://help.pythonanywhere.com/pages/ScheduledTasks/ and
https://help.pythonanywhere.com/pages/FreeAccountsFeatures/ . Recheck before setup.

Only if the account becomes eligible, Michael can open Tasks, choose a daily
quiet time, and enter the explicit virtualenv Python plus absolute manage.py path:

```bash
/home/Mathenge/.virtualenvs/ajiri/bin/python /home/Mathenge/ajiri/ajiri-backend/manage.py backup_private_data --destination /home/Mathenge/ajiri-private-backups
```

Schedule DB-only backups; do not schedule --writers-paused blindly. Review the
task's displayed time zone, run it once manually, confirm completion manifest and
quota, and inspect the next task result. No Actions workflow, production task or
new remote backup endpoint is created in Phase A.

## Disposable restore rehearsal — never overwrite development or production

1. Verify the downloaded manifest against the private server copy. Compare DB and
   archive SHA-256 against its sha256 entries; if automatically decompressed, use
   media_uncompressed and rename only that download to .tar.
2. Create a NEW private rehearsal directory beside the snapshot, not in the repo.
   Copy db.sqlite3 into it. Use SQLite URI mode=ro plus PRAGMA integrity_check on
   the copy and explicitly close the connection; expect `ok`.
3. Validate every tar member: regular file/directory only, no links/absolute paths
   or traversal; extract only into the new empty private-media folder using Python
   tarfile's data filter. Compare restored file count/bytes with the manifest.
4. Keep the source backups intact. This basic rehearsal proves restoration of
   bytes/integrity, not a complete application/user-permission restore. A future
   isolated app restore must disable email/ingestion and use only the restored DB.
5. Record only success/counts/date. On any mismatch, stop before deployment and
   retain both copies; never regenerate an applicant's saved documents as a repair.

Rollback of this tool means reverting the reviewed code; no DB rollback, file
deletion, schema reversal or backup removal is necessary.
