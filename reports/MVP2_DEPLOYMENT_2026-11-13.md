# MVP2 first release: production receipt, 13 November 2026

Activated `d5f2f6871276434569df10ffb153cb8591a9a7df` on
https://mathenge.pythonanywhere.com after the paused deployment was resumed.
This releases the implemented AJ-83 skill-explanation slice, not the whole MVP2
backlog. Previous production source was `e682cac4299102f963c1193d580979ecdefa219f`.

## Branches and required checks

`MVP2` was created from reviewed main `a8f11fd` as Michael requested. Feature
branch `codex/mvp2-aj83-matching` merged through
[PR88](https://github.com/michael-mathenge/ajiri/pull/88) into `MVP2` as `3e37c47`.
[PR89](https://github.com/michael-mathenge/ajiri/pull/89) released it to main as
`d5f2f6871276434569df10ffb153cb8591a9a7df`. Both release trees are identical.
All six exact production-head checks passed in
[CI43094746515](https://github.com/michael-mathenge/ajiri/actions/runs/43094746515):
backend Python 3.12/3.13/3.14, frontend, quality and browser/performance. The first
browser job passed its test step but failed artifact upload with an HTML/JSON
service error; the rerun passed. This was not hidden as a passing first run.

Actual local release verification used the fully pinned Python 3.13.17 environment
with Django 6.1.3 and lxml 6.1.3: `pip check`, `manage.py check`,
`makemigrations --check --dry-run`, and the full suite passed (533 tests in
258.239 seconds, one existing platform skip). Local Python 3.12 remains unavailable;
CI supplies that platform's acceptance. Explicit Node 24.19 locked `npm ci`,
both linters, 159 component tests in 28 files, the quality helper and build passed.
All 38 generated files matched the committed build. No new frontend changes were
made during activation.

## Recovery and production order

The consistent paused-writer snapshot `backup-20261111T202211225524Z-44e595ea`
was completed and verified before any runtime/source activation. The database and
all 16 private files (335,905 bytes) were rechecked against it under the 13 November
web pause; there had been no intervening data changes. The private off-server copy
and isolated restore are complete, superseding the earlier unfinished download.
The recovery copy is retained privately under Michael's `AjiriBackups` directory,
outside Git. Its receipt records 8,736 restored runtime regular files, 85,450,850
bytes and three Linux links retained as metadata on Windows.

Recovery SHA-256 values:

- Manifest: `5325d37af95f02f08f78a5c95c380cfcf8f6caa1c5f717e897b79ecc06f9f7b8`
- Downloaded recovery ZIP: `fc41e5bf94732cc30293076c1553898a7b2c07e62349ed5c633afcc030d47328`
- Previous virtualenv archive: `e8b532c35966e94109b3306b2c7bd818bac79b82efe5f89db7a0379c0d33d627`

Both GitHub writers were disabled and all five pending/running workflow statuses
were empty before the web app was disabled. Exact source staging and
`scripts/release_preflight.py --revision d5f2f6871276434569df10ffb153cb8591a9a7df
--previous e682cac4299102f963c1193d580979ecdefa219f` passed with no changed migrations.
Eleven pinned upgrades were installed from the previously downloaded release wheels
using `pip install --no-cache-dir --no-index --find-links ... -r requirements-prod.txt`.
`pip check`, Django check, migration drift and actual `migrate --plan` all passed;
there were no migration operations, so no migration was applied.

All 33 runtime pins were independently checked. Database SHA-256, complete private
media inventory/content, SQLite integrity, search trigger definitions and release
flags matched their preactivation values. Production source was clean at the exact
release SHA. Home usage was 447,372 KiB after installation, about 436.9 MiB of the
512 MiB quota; no backups or user files were pruned. Capacity remains a bounded
constraint, not proof of unlimited backup retention.

## Activation and smoke checks

The web app was re-enabled and explicitly reloaded. PythonAnywhere's reload control
returned to its ready state. Public verification after the final reload passed:
health HTTP 200, HSTS `max-age=604800`, and exact bytes for all 38 frontend files.
The live index SHA-256 is
`6d0dcd1bb78288450d54cb06e54aea55c1e10f2f5ebe67b75eb891064859f6c6`.

Read-only DRF requests inside the production runtime used the existing owner's
account: jobs list 200 (count 0), CV draft 200, and existing approved CV download
200 with matching stored document SHA-256 and private/no-store caching. Anonymous
CV download returned 401. These are authenticated server view checks, not a new
network login or manual phone journey. No second active account was available for
a production cross-owner check. A historical job's serialized explanation passed
its required/matched/missing consistency check; there was no currently visible
vacancy for an authentic live job-detail browsing journey. Automated ownership,
low-score preparation and browser accessibility tests remain the corresponding
regression evidence. No synthetic production job or account was created.

Ingest and sweep workflows were both restored and independently confirmed active.
After automatic review initially blocked an extra manual ingestion run, Michael
explicitly authorized one check. That single run completed successfully:
[Ingest43425203368](https://github.com/michael-mathenge/ajiri/actions/runs/43425203368).
No extra sweep or replay was triggered. Successful ingestion is not independent
proof that vacancies are current or that any email reached an inbox.

Freshness enforcement stays true. Application email, alert email, public jobs and
supplemental browsing stay false; the existing account-mail service remains true.
No application, alert, payment, consent, private document approval or broader
sending activation occurred. Free hosting expiry was displayed as 30 November 2026.

## Rollback and remaining scope

If required, pause writers/web, return source to the recorded previous SHA and
restore the privately verified previous virtualenv with its original paths. Verify
dependencies and data preservation before re-enabling service. Retain current
SQLite, private media, erasure recovery ledger, settings and any new normal writer
records; do not routinely replace them with an old snapshot. No rollback was needed.

AJ-83 remains In Progress: normalized filters, preferences/dismissals and the
consented usability pilot are separate unfinished work. Remaining MVP2 inventory,
recovery capacity and external-service prerequisites are not completed by this
deployment. This documentation follow-up does not establish a newer runtime SHA.

## Documentation follow-up verification

The isolated receipt branch is `codex/mvp2-deployment-receipt-20261113`, targeting
`MVP2`. Its first local Django invocation stopped before checks because the clean
worktree deliberately has no `.env`. With isolated test settings (`DEBUG=True`,
dotenv disabled and real email false), system/drift checks passed and all 533
tests passed in 256.262 seconds, one existing skip. Node 24.19.0 `npm ci` installed
359 packages, lint passed and build passed in 2.13 seconds; all 38 regenerated
files still match the unchanged committed frontend build. `git diff --check`
passed. No production secret or personal content was copied into this receipt.
