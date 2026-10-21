# Account data requests

Status: export is deployed at4fa75b5. Signed-journal erasure/restore replay is local
and must pass its remaining release gates before deployment. This is
an operator-assisted workflow, not a self-service download endpoint or legal advice.

Verify the requester through an established account-owner channel before export.
Never put identity evidence, passwords or reset links in a ticket or command line.
Run a dry run first (PowerShell, from ajiri-backend with the project venv active):

```powershell
python manage.py export_account_data --user-id 123 --destination C:\PrivateExports\request-001 --dry-run
```

The destination parent must exist. The destination must be new, private and outside
the checkout, live database directory and media. Review the reported inventory.
For execution, pause web/ingestion/sweep writers and add `--verified-request
--writers-paused`. Resume the previous service states even if export fails.
These flags attest actual checks; they do not perform verification or pause services.

The folder contains account.json, private documents under random names, and a
completion manifest with SHA256 checksums. It includes profile/skills, CV workspace
and approvals, applications/packages/approvals/authorization, notifications, owner
delivery receipts/budgets and the relevant public job snapshots. It excludes other
accounts, password hashes, JWT/session secrets, internal delivery keys/digests,
credentials, shared global budgets, platform logs and backup copies. Export never
sends email, downloads to a public mapping, changes the account or prunes files.

An interrupted export has no completed manifest. Do not deliver it. Use a new
destination after fixing the cause; do not merge incomplete and complete exports.
Verify all manifest hashes and deliver only through the identity-verified private
channel. Protect Windows parent-directory ACLs: POSIX modes alone do not establish
Windows access control. No production account export was performed for testing.
Remove delivered temporary exports only under the separately established retention
and recoverability process; no automatic deletion policy is inferred here.

Deletion must preserve shared jobs/skills, revoke access, resolve pending delivery
outcomes, remove all owned DB rows/private files and make file-cleanup failures
resumable. Before actual erasure, legal holds/retention exceptions and the owner's
request must be checked. Backups/provider/employer copies are independent; never
promise immediate deletion from them. An erasure ledger must be preserved outside
old snapshots and replayed before any restored database reopens. These constraints
are enforced by the erasure command below; running export never erases anything.

## Erasure procedure

This operator-only workflow requires a verified account-owner request and legal
review of holds, retained accounting and applicable retention exceptions. Broad
feature approval is not permission to delete a particular account. Do not run a
production erasure just to test the feature. Export first if requested.

Use the configured ERASURE_LEDGER_DIR, defaulting to the owner's home directory
`ajiri-erasure-ledger`, outside code, live DB and media. Unix mode0700 is required;
verify Windows ACLs separately. Generate a request UUID and retain its association
with the verified request in the private operator record. PowerShell example:

```powershell
$requestId = [guid]::NewGuid().ToString()
$accountId = [int](Read-Host 'Verified requester account ID')
$ledger = Join-Path $HOME 'ajiri-erasure-ledger'
python manage.py erase_account_data --user-id $accountId --request-id $requestId --journal-dir $ledger
```

The default mode is a no-write inventory. Resolve missing/unsafe/cross-owner file
references and reserved/unknown delivery outcomes before proceeding. Pause all
writers and keep their previous states for guaranteed resumption.

1. Run the same command with `--mode prepare --verified-request --writers-paused`.
   A signed private journal records the exact owner fingerprint and file inventory.
2. Preserve an independently verified off-server copy before execution. The enhanced
   backup command includes `erasure-ledger.zip` automatically whenever the configured
   ledger exists. Run the normal verified backup/copy procedure and confirm the
   journal is included. Do not copy environment files, keys or credentials.
3. Only after the actual request, legal checks, writer pause and independent journal
   copy are established, execute with `--mode execute --verified-request
   --writers-paused --legal-hold-cleared --journal-copied`. These flags attest real
   checks; they are not substitutes for them. The command does not contact the owner,
   pause services or obtain legal approval for the operator.
4. Account/profile/application/CV/consent/session/JWT rows are removed, protected
   authorization links are cleared in dependency order, and referenced owned files
   are removed. Shared jobs/skills/global budgets remain. Settled delivery records
   retain pseudonymous accounting with owner/application links removed and provider
   receipt IDs cleared. Their permitted retention period still requires legal review;
   keyed digests are pseudonymous, not anonymous. No employer/provider copy is erased.
5. A file failure leaves a signed `db_erased` journal and a clear error. Resume the
   same request with the same execution attestations after fixing access. Never
   restore an older DB over newer writes to undo cleanup. Completion scrubs file
   paths from the minimal signed ledger; preserve/re-copy the completed ledger.
6. Resume the exact prior services and verify health. Retain the operator receipt
   privately. Backups still use30-day DRAFT/report-only retention, not deletion.

Unreferenced historical orphan files cannot safely be assigned to an owner by
guessing. Report them for a separate verified ownership review; never delete shared
or unknown files by filename similarity.

## Restoring an older snapshot

Keep writers closed. Obtain the **latest independent erasure ledger**, not merely
the ledger embedded in the old snapshot. Preserve newer ledger entries before
restoring any DB/media. For every completed request whose exact identity reappears,
run the same command in `--mode replay` with the original request/account identifiers
and execution attestations. Replay collects restored owned files and repeats the
verified deletion. A different identity with the same numeric ID is refused. A
pending request is not automatically executed. Resolve every cleanup/reconciliation
failure before reopening services. A restored folder is never itself activated by
the backup verifier.

The signed ledger requires the existing private Django signing configuration.
Credential rotation or unavailable verification keys must trigger manual recovery
review; never disable signature/identity checks or copy keys into a backup ZIP.
Erasure is irreversible for an actual verified request: code rollback preserves
the current DB/ledger and cannot recreate the account. Prefer forward fixes; old
backup code that omits the ledger must not be used after real erasures.
