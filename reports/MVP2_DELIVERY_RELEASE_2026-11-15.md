# Delivery reliability release - 15 November 2026

Closeout recorded16 November. Exact active runtime is
276f37ae05285c7fbe978994f6bf521add99d5fe (PR113), verified externally at
2026-11-15T20:59:55.836387+00:00. Earlier runtime/rollback source is ef1c102.
Documentation follow-ups do not establish a newer activated runtime.

## Reviewed implementation and actual validation

PR111 exact38da502 passed all six checks and mergedMVP2 as 88080fc. Signed manual
match/search continuation advances past examined ineligible rows; fixed upper IDs
defer new inserts to a fresh pass. Search cursors bind UUID/revision. Existing
list callers and final-handoff eligibility/consent/budget/receipt guards remain.
No public API, ingestion or automatic scheduler changes.

PR112 correctedf3fb461 passed all six checks and mergedMVP2 as f89e739. Dormant outbox
supports exact application authorizations, notifications and saved-search revision/
windows. No matching/sweep/HTTP producer hooks or periodic schedule. Conditional
leases, token settlement, three-claim exhaustion, broker publication uncertainty
and explicit operator reconciliation preserve receipts. Fast-worker settlement
survives publisher timeout. Final review fixed existing search failures being
mislabeled complete; no uncertain provider IO is automatically repeated.

Release PR113 exactf89e739 and merged main 276f37a each passed all six checks.
Only additive jobs0022_durable_delivery_queue after0021 was reviewed/applied;
archived conflicting0018 was not reused. No dependency installation or frontend
byte change. Queue/normal sending/posting/publication remain disabled.

Actual local gates: continuation full618tests531.248s(one existing skip) plus
21focused3.008s; queue full636tests294.056s(one existing skip); correction17queue
tests5.831s and full637tests265.345s(one existing skip). Check/drift/Ruff passed.
Node 24.19 locked ci358/audit0/lint/build passed, with47regenerated files exactly
matching committed assets. Populated0021-to0022 rehearsal preserved old table rows,
relationships, document bytes and all three search triggers. Release-evidence gates also
passed637tests308.029s(one existing skip), check/drift/Ruff; locked frontend ci,
lint/build1.81s and47-file comparison passed. No frontend source/build modification.
IndexSHA256 c1a069b2ec992fbb5714a2a7a017e01b0337ac0fdd33df9b2dd53aa3e9a42448.

## Fresh recovery and exact authorized capacity remedy

Paused/drained writers plus reversibly disabled web produced consistent
backup-20261115T202725589172Z-4c73df88 fromef1c102. All45 tables/columns/rows,
three triggers and16 private file hashes matched current production. Server hashes
passed. Web and both prior-active writers were restored before private download.
This was a manual consistent release fallback, not an unattended daily-run claim.

ZIP11316357bytes SHA256
0b6f097f77792e13ea5f585053e847e3cf2235de5778f7dd55ca6c4728c613c7;
manifestSHA256 ad57bf243181c8c297cf7e2118f8e391f0d4b8d081e99e798f58f692991916e1.
Exact off-server ZIP/raw members, isolated SQLiteintegrity and all 16 restored media
hashes passed; private recovery receipt complete. Erasure ledger was absent.
Retained14 November and24 October off-server archives/raw members/isolated restores
were independently reverified (16and17 private files), with completed receipts.

Initial15 November reserve failed by94406bytes.127loose Git objects already stored
in verified packs were reclaimed. Pack/fsck verification before/after plus exact
HEAD/refs/reflogs/config/worktree preservation passed; no backup/user file removed.
Capacity then passed827194bytes beyond the full plan. Fresh snapshot/transfer and
fetched reviewed source subsequently left39780550bytes below the full future
snapshot+transfer+16MiBreserve plan at20:40UTC; no code was staged on that failure.

Michael explicitly approved ONLY five server files totaling43091389bytes:
- backup-20261114T103614144596Z-cea25a60/db.sqlite3
- backup-20261114T103614144596Z-cea25a60/manifest.json
- backup-20261114T103614144596Z-cea25a60/private-media.tar.gz
- backup-20261114T103614144596Z-cea25a60/backup-20261114T103614144596Z-cea25a60-recovery.zip
- backup-20261024T102207298247Z-c787f77e/release-backup.zip

Paths are relative to /home/Mathenge/ajiri-private-backups/. Immediately before
removal, exact hashes, sizes, regular-file/symlink/link-count and resolved-path
bounds were checked; all3retained off-server ZIP hashes/completed receipts were
rechecked. Only these five files were unlinked. All off-server copies, fresh server
recovery and other files remain. No future retention policy or further deletion
authority inferred.20:47:19 UTC reserve passed3333946bytes beyond the complete plan.

## Migration-first activation and preservation

Both prior-active writer workflows were disabled and drained; all5pending/active
run-state queries had zero writer runs. Web was reversibly disabled. A fresh paused
comparison again matched the completed recovery's45 tables/columns/row hashes,
three triggers,16 private file hashes and existing flags. Erasure ledger remained
absent. Exact clean sourceef1c102 staged reviewed276f37a; release_preflight expected
only jobs0022, pip_install_requiredFalse and the exact index/asset inventory.
Production check, migration drift and actual migrate --plan passed. MigrationExecutor
independently asserted the sole forward jobs0022 plan before actual migrate.

jobs0022 applied successfully before requests resumed. Verification retained all
old table values and columns, all three search triggers and16 private file bytes. The only
new table is empty jobs_deliverytask; expected metadata additions were one migration
row, one jobs.deliverytask content type and4 permission-catalog rows. Existing
user/group permission associations were preserved; no staff grant. SQLite integrity
and foreign-key checks passed; actual remaining migration plan empty.

The operational verifier initially assumed permission-column positions; it was
corrected to named columns and rerun without another migration. The read-only CV
probe initially assumed a streaming response; buffered/streamed handling was
corrected. Final preservation and smoke checks passed; these were verifier fixes,
not application code changes or extra send/migration attempts.

Fresh-process actual WSGI configuration verified all ninedisabled gates, freshness on,
and general account-security configuration valid in account_security mode. All33
installed production pins matched requirements-prod. Direct owner views returned200
for jobs, CVdraft, employer drafts, suggestions/dismissals, saved jobs and applications
(counts0/0/0/0/0/1 where applicable). Existing approved private CV bytes matched stored
SHA256, no-store; anonymous equivalent401. Saved searches correctly403while off.
These used APIRequestFactory/force_authenticate, not a new network login or genuine
outside-employer acceptance. Aggregate queue read empty; disabled queue recovery,
match/search commands and task executor made no new task, delivery attempt or handoff.

Final post-smoke old-row/file/flag preservation passed.20:57:32 UTC used458952704bytes
including1MiBmargin,77918208available,74694854required for full next snapshot/transfer/
16MiBreserve;3223354remaining beyond the plan. No reserve reduction or extra cleanup.
Web was re-enabled and explicitly reloaded; reload returned enabled. Both writer
workflows were re-enabled and independently observedactive. External health200/
HSTSmax-age604800, all 47exact asset hashes and3anonymous private401checks passed
at2026-11-15T20:59:55.836387+00:00. No manual ingestion or live normal send.

The first final writer-state read was not executed because approval review hit a
usage limit; after Michael continued, the same approved read succeeded and verified
bothactive. No approval bypass or alternative writer mutation occurred.

## Remaining acceptance and rollback

AJ17/26/43/48 retain real normal-path and hosted durability prerequisites. No normal
send, new consent, staff grant, employer/candidate acceptance, infrastructure service,
analytics or payments were activated. MVP2 remains incomplete. Source-only rollback
to ef1c102 keeps jobs0022/newer rows, private files, receipts, erasure ledger and safety
flags. Never reverse production schema or restore stale data as routine rollback.
