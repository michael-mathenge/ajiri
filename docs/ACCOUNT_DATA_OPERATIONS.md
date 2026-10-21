# Account data requests

Status: export command implemented locally; deletion/restore-replay remains pending.
AJ-25 is not complete until deletion and its failure/recovery tests pass. This is
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
remain implementation work; running the export does not erase anything.
