# AJ-85: repeatable recovery-capacity gate

Feature branch `codex/mvp2-aj85-recovery` was created from reviewed MVP2 `cee43f4`
and fast-forwarded to reviewed AJ-87 merge `00ce84f` before final checks. The original
main checkout, stash, archived tips and private recovery copies remain untouched.

## Readiness evidence and remaining risk

The archived October migration stack is reference material, not a merge candidate:
its jobs.0017 analytics collides with the deployed0017 browsing migration. Existing
release_preflight rejects historical migration modifications and requires an exact
reviewed additive migration list. Neither this package nor AJ-87 has migrations.
The earlier13November release already verified private off-server recovery and
isolated16-file restoration; do not repeat that completed work as unfinished.
The last runtime was d5f2f68 and the last measured home usage447,372KiB. These are
historical inputs to this package, not a new production capacity measurement.

Backup source size alone misses the period when a completed snapshot and download
ZIP coexist. A shared-host df reading also does not establish account-quota reserve.
The new `private_recovery_plan` command requires explicit fresh quota/usage in bytes
and returns a conservative, read-only peak-space report. It measures SQLite main,
WAL/rollback-journal and private media/ledger file sizes by stat; it never opens
SQLite or reads/copies document contents. Existing inventory guards reject links,
special files and credential-file names. No private paths/content are printed.

The report includes archive padding/metadata, compression expansion, simultaneous
snapshot/transfer bytes and a default16MiB operating reserve. Compression allowance
uses the upstream [zlib compressBound arithmetic](https://github.com/madler/zlib/blob/master/compress.c)
with additional wrapper allowance. Per-file ZIP allowances account for independently
compressed members. Ledger estimation conservatively includes regular-file sizes;
it does not expand the real backup's allowed member set or include signing keys.
No backup/restore success is inferred from a passing estimate. Inputs must be
remeasured in the paused-writer release window; background usage/growth can change
capacity. Insufficient reserve returns an unsuccessful command without pruning.

The default scope is SQLite/private media/erasure recovery. A new runtime archive
is explicitly excluded, with an optional additional-snapshot byte allowance for
separately bounded artifacts. Restoring production still requires separately
verified source/runtime/configuration and independent off-server recovery. This
tool does not authorize a purchase, retention policy, deletion or production switch.

## Actual verification

Eleven focused synthetic tests passed in0.260s: arithmetic/boundary/overquota and
invalid inputs, incompressible archive expansion, metadata/private ledger allowance,
no copied/changed files, low-capacity refusal, absent/unsafe input, journal sizing
without SQLite/shared-memory writes and relative-path rejection. The first9-test
run passed before journal edge cases were added. Initial Ruff invocation was
unavailable in the selected venv; installed the exact repository-pinned0.17.4 there,
then full backend/scripts Ruff passed. System and migration-drift checks passed.

Explicit Node24.19 locked npmci installed358packages; lint and build passed in1.65s.
All38 regenerated frontend files match the unchanged committed build. The full
backend suite passed544tests in258.304s (one existing skip). Six required CI checks
and fresh production measurement remain pending; no new production activation is
claimed yet.

## Activation and rollback

After required checks, merge into MVP2 and use a separate checked main release.
Before activating, measure current account quota, keep a fresh consistent private
backup/off-server copy/isolated restore and confirm the new planner's actual report.
It does not replace any backup command or scheduler receipt. Retention stays
report-only. Runtime/application safety flags remain unchanged. Rollback is source
only; keep current database/private media/erasure journals and all new writer records.
