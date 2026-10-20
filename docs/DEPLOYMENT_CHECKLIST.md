# Release checklist

Use a reviewed immutable commit with all required CI checks passing. Current
deployment evidence is in JIRA_ROADMAP_PROGRESS.md; archived checkpoint instructions
are historical. Never copy a developer database/media directory onto production.

1. **Preflight.** Record previous/current reviewed SHAs, actual account quota,
   virtualenv and private data locations, service/workflow states and rollback.
   On a clean checkout of the reviewed source, run the read-only planner:

   ```powershell
   python ajiri-backend/scripts/release_preflight.py --revision FULL_REVIEWED_SHA --previous FULL_DEPLOYED_SHA
   # Add --expected-migration profiles.0006_privacy_notice only for that reviewed delta.
   ```

   It fetches nothing, changes nothing and does not replace runtime migration review.
   Unexpected migrations, dirty source or missing build assets stop the plan.
2. **Pause writers.** Pause enabled ingestion/sweep workflows, wait for queued/running
   writers to finish, and disable the enabled web app. Preserve prior states so a
   previously disabled service is not accidentally enabled during resumption.
3. **Back up before staging.** The daily automation normally handles routine backups;
   a release needs a fresh consistent snapshot if writes changed. In PythonAnywhere
   Bash, activate `workon ajiri` before strict shell options; run the existing
   `backup_private_data --destination PRIVATE_DIRECTORY --include-media --writers-paused`.
   Never assert paused writers without actually pausing them.
4. **Verify recovery.** Check manifest, hashes, copied database integrity and safe
   media restore; retain and independently verify the private off-server copy.
   Where the validator is available:

   ```bash
   python manage.py verify_private_backup --backup COMPLETED_BACKUP --restore-to NEW_PRIVATE_RESTORE_FOLDER
   ```

   This requires a new folder and never restores over live data. See
   [backup automation](BACKUP_AUTOMATION.md) for the full procedure and fallback.
5. **Stage the exact SHA.** Require a clean production checkout, then
   `git switch --detach FULL_REVIEWED_SHA`. If production requirements changed,
   preserve a private, verified dependency rollback first and run in the existing
   virtualenv:

   ```bash
   python -m pip install --no-cache-dir --requirement requirements-prod.txt
   python -m pip check
   ```

   If requirements did not change, no reinstall is necessary. Never downgrade to
   known-vulnerable historical pins to make a rollback look simple.
6. **Review/apply migrations.** Run `manage.py check`,
   `makemigrations --check --dry-run` and `migrate --plan`. Compare the exact pending
   operations with the approved list. Stop on unexpected operations. Apply them
   while requests remain paused; check integrity and preservation of existing data.
7. **Activate and resume.** Re-enable/reload the WSGI app only after migrations
   complete. Verify health GET/HEAD, release asset hashes, authentication/bootstrap,
   owner-only profile/document access, blocked direct media, intended feature behavior
   and HTTPS headers/no loops. Resume only previously active workflows; verify a
   normal ingestion run. Report partial resumption failures immediately.
8. **Record evidence.** Store sanitized backup/release receipts privately, record
   exact source/migrations/checks/limitations in the roadmap review and update Jira
   from evidence. Refresh old browser tabs after a release; the recovery UI offers
   an explicit reload without automatic mutation retries.

For this PythonAnywhere host, verified native WSGI HTTPS means
`SECURE_PROXY_SSL_HEADER=None`, host Force HTTPS on, Django redirect on and HSTS
300 seconds with subdomains/preload off. W005/W021 are intentional for that policy.
Do not copy these assumptions to another hosting setup without verifying it.

Rollback restores the reviewed server/client pair and changed configuration;
retain additive schema, receipts and newer writes. Do not routinely restore an old
database or reverse populated evidence migrations. Keep sending disabled where
its prior sender would bypass current document/authorization safeguards.
