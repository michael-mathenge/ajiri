# Public validation performance release — 14 November 2026

Release PR103 passed all six exact-head checks on95198a6 and merged into main as
`c88da83070b2e491a3f2df2601a6efaaed08374f`. All six merged-main checks passed.
Following-backup capacity passed and the exact runtime was activated at approximately11:06UTC.
Production was freshly verified clean at
`9676fc4c89b7aef04461c2ba0bbc9eed060ade45`; merged source is not deployed evidence.

PR102 implemented deferred public login/register/recovery validation with the same
schemas and explicit submit, failed-download, duplicate-submit and changed-input
guards. Its source/build-last commits df0c325/b711ff7 passed all six checks and
merged asb48d5e5. PR101 retained the actual discovery activation and the initial
251ms register failure, integrated the checked fix, then passed all six new-head
checks before MVP2 merge95198a6. Neither budgets nor CI workflows were weakened.
Linux43516747325 measured login/register three-run TBT110/101ms and initial
transfer474740/472854bytes. See reports/AJ86_PUBLIC_VALIDATION_2026-11-14.md for
all local commands, initial busy-state failure/correction, lab medians and limits.

## Fresh consistent recovery

At10:33:15UTC the quota plan passed:448741376bytes used with1MiB margin,
88129536available,73941075required,14188461beyond planned snapshot/ZIP/reserve.
The database was27877376bytes, so older unchanged-data evidence was not reused.
Ingest377395490 and Sweep377395493 were observed active, disabled and drained;
five run-state queries returned no active/queued/requested/waiting/pending runs.
Web was paused. The fresh clean-source9676fc4 snapshot
`backup-20261114T103614144596Z-cea25a60` completed with media included. Existing web
and both writer workflows were restored immediately before download; external
health returned200. This is a manual consistent release fallback, not a fresh
unattended automation claim. No source staging preceded completed recovery.

The immutable private transfer completed through PythonAnywhere Files:

- ZIP11206918bytes, SHA256
  `1e8d8bf4496a3cf50c08b1202311ca58cc1f924c10810e84f9a6de93962c133f`.
- Manifest SHA256
  `020efbc59a5ba96a5e5fc22a2ddae4416eae7818b8def4571fea15e22547662b`.
- Private retained directory:
  `C:\Users\micha\AjiriBackups\release-public-validation-backup-20261114T103614144596Z-cea25a60`.

Downloaded size/hash, complete manifest/source, exact bounded ZIP members,
SQLite integrity and all16files/335905bytes passed. `verify_private_backup`
completed an isolated restore and retained a complete aggregate receipt.
No production database or files were replaced with development data.

## Measured capacity gate and concrete duplicate copies

After retaining the new snapshot and ZIP, at10:41:56UTC the planner failed closed:
488108032bytes used with margin,48762880available versus73941075required,
deficit25178195. Web/writers remain active on9676fc4. This gate must be green
before staging; no recurring pruning authorization is inferred.

Only three older raw copies are proposed in
`/home/Mathenge/ajiri-private-backups/backup-20261113T134617405732Z-46a6f54d`:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| db.sqlite3 |27779072|`87fad7a0433c2c71054aae382e8eede7db6e6ba6e3bf794cf9e0327211ec0c91`|
| manifest.json |605|`cb433e1c81b0fc18f3ad6d83ddbe5353735ee158673383f9ad767bbc264909cf`|
| private-media.tar.gz |254683|`6b07afe89a5ebdb4023ca4518cff25cf739dce5d4f38252e81e621528c3af447`|

Total28034360bytes. Server and off-server raw hashes match. The full server ZIP
`original-source-recovery.zip` in that same folder remains and was rehashed to
`4b77a0a06dcc35bf080472dbd7c1393d297a8369afa7512502d2b6d984fcb334`;
its exact three member sizes/hashes match these raw files. The off-server ZIP
and completed recovery receipt were independently reverified as well. Both newer
server snapshots, every other entry and all off-server copies must remain.

Michael's earlier three-file approval covered a different11November snapshot,
already handled. Michael approved these exact three duplicate copies on14November. Initial UI
input contention blocked execution before any mutation. After Michael confirmed
the window ready, exact path, size, hashes and retained ZIP members were checked
before unlinking only those three paths. Complete before/after inventory matched
exactly minus those names; retained ZIP SHA256 remained unchanged. AGENTS.md's
report-only retention rule still applies to all other files and future retention.

## Activation and rollback gates

After all six merged-main checks and capacity pass, pause/drain writers/web again.
Compare every current database table/trigger and private file with the completed
fresh recovery; stop if any current data changed. Stage only exact checkedc88da83.
Release preflight must show no new migrations or dependency installation relative
to9676fc4; run check/drift and the actual empty migration plan before reloading.
With no schema change expected, every table/trigger/media hash and existing safety
flag must remain exactly unchanged. Verify all33 runtime pins, owner-only private
reads and existing approved CV bytes without a personal mutation or live send.
Verify health/HSTS and all44 actual frontend files externally, then independently
confirm both writer workflows restored active. No new manual ingest is authorized
by the already-used earlier one-time ingestion check.

Rollback source only to9676fc4 while preserving all current database/private media
and flags. Do not restore an old snapshot as routine rollback, disable freshness,
enable posting/public jobs/sending, grant staff access or create fake vacancies.
AJ86 remains In Progress for genuine pilot/manual-device/field-p75 acceptance;
MVP2 still has16unfinished non-Epic items and is not declared complete.

## Release receipt verification before activation

All six merged-main checks passed on c88da83. Local exact-release preflight
passed with zero expected migrations, no dependency installation, and frontend
index SHA256 `6735520347e72e73ce23fea4b6e12d84667a008fa84987742b4b03e685256dcb`.
For this receipt package, backend check and migration drift passed;591 tests
passed in288.705s with one existing platform skip. Node24.19 locked npm ci,
lint and build passed (2.13s); all44 regenerated files match committed bytes.
These local checks supplement the independently observed production evidence below.

## Actual production activation and verification

At11:00:50UTC the approved cleanup receipt confirmed28034360bytes removed,
other entries preserved and the retained ZIP checksum unchanged. Capacity passed:
460062720bytes used with margin,76808192available,73941075required,
2867117beyond planned next snapshot/ZIP/16MiB reserve. Both writer workflows were
disabled and all five queried run states were empty before web was disabled.

Before staging, all45tables including complete columns/rows, three search triggers
and16private-file hashes matched today's completed recovery. No erasure ledger
appeared. Existing safety flags were recorded and exactly preserved. Git fetch
confirmed origin/main exactlyc88da83; checkout detached that revision from clean
9676fc4. Production release_preflight passed, no pip install was needed; check,
makemigrations --check --dry-run and migrate --plan passed. MigrationExecutor
independently asserted an empty plan. No actual migration ran.

At11:04:15UTC the post-staging planner passed:461045760bytes used with margin,
75825152available,73941075required,1884077beyond the complete next-backup plan.
All45tables/three triggers/16files and flags matched again exactly. Source was
clean. All33 requirements-prod pins matched installed versions. Read-only API
view checks with APIRequestFactory/force_authenticate returned200 for owner jobs,
CV draft, employer drafts, suggestions, dismissed suggestions, saved jobs and
applications. Counts were0/0/0/1 for the last four. Existing approved private CV
bytes matched their stored SHA256; anonymous access returned401 and private
responses used private,no-store. These are direct view checks, not a new network
login or owner mutation. Saved searches remain disabled and correctly returned403.

Web was re-enabled and explicitly reloaded; the reload control returned enabled.
Both Ingest377395490 and Sweep377395493 were enabled and independently observed
active. External HTTPS health returned200 with HSTS max-age=604800; all44 public
files, including index SHA256
`6735520347e72e73ce23fea4b6e12d84667a008fa84987742b4b03e685256dcb`,
matched checked local bytes. No manual ingestion or real email was performed.
Freshness stays on; posting/public vacancies/application and alert sending stay
off. Original-source readiness remains0eligible roles/0employers against50/10;
no pilot, consent, inbox delivery, manual-device or field-p75 result is invented.
Runtime is c88da83070b2e491a3f2df2601a6efaaed08374f. Documentation-only follow-up
merges do not imply a newer activated runtime. All off-server recovery copies,
both newer server snapshots, the older retained ZIP and unrelated entries remain.
