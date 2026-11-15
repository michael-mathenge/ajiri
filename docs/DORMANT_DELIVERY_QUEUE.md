# Dormant delivery queue

This package integrates reviewed archived outbox/recovery code against current main.
It is not a live service: DELIVERY_QUEUE_ENABLED defaults False, all normal sending
switches remain off, no automatic enqueue hooks or periodic schedule are added.
No new HTTP endpoints or dispatch response changes. Matching/sweep work is excluded.
The archive's conflicting0018 is not reused; jobs0022 follows current0021 and creates
only the queue table, including saved-search revision/window references.

## Operator procedure after separately verified service prerequisites

Inspect aggregate states: python manage.py delivery_queue
Enqueue one existing target: python manage.py enqueue_delivery_work --owner-id <ID>
with exactly one of --authorization-id <UUID>, --notification-id <ID>, --search-id <UUID>.
Targets must belong to that active owner. Search tasks bind the currently due window
and revision; they cannot consume a future window or follow an edited search.
Returned task UUID is a private operational reference, not proof of sending.

Publish only pending tasks: python manage.py delivery_queue --publish-pending --limit 20
Recover expired leases: python manage.py delivery_queue --recover-leases --limit 20
Reconcile one blocked/uncertain target explicitly:
python manage.py delivery_queue --execute-id <UUID> --resume-blocked
All limits are1-50, enforced inside handlers. No action starts when the queue is off.
Default inspection is read-only and prints state counts only. No public diagnostics.

Publication timeouts become publication_unknown and must not be blindly republished.
A worker or explicit operator can resolve that same target; shared ledger receipt
reconciliation prevents another external handoff. Three-minute conditional leases
and lease-token settlement prevent duplicate claims/stale settlement. After three
expired claims the task becomes dead/lease_exhausted with no fourth handoff. Definitive
failure becomes dead; ineligibility/disabled channels become blocked; reserved/unknown
outcomes remain needs_reconciliation. Dead tasks have no automatic revival command.

Do not delete or reset receipts, leases or dedupe keys to retry. An unresolved receipt
requires provider/operator investigation; no tool here fabricates resolution or makes
a fresh authorization. Blocked resumes recheck current owner/consent/documents/job and
preserve normal shared budgets. Existing owner pilots are retained as historical
inbox evidence, not normal-path acceptance.

## Release and recovery

Verify capacity and consistent private off-server backup/isolated restoration before
staging. Pause/drain writers and web, apply only reviewed jobs0022 before new code
handles requests, then compare old table values, triggers, relationships and private
file bytes. Confirm queue and all normal sending/publication flags remain False.
Restore web and prior writer states; verify HTTPS, exact assets and private access.
Source-only rollback keeps the new empty/durable queue table, newer rows, private
files, receipts and erasure ledger. Never reverse production schema or replay
ambiguous provider IO. No broker, worker, scanner, storage or live sending is provisioned.

Earlier synthetic process/broker/uncertain-handoff rehearsals remain evidence only
for their tested cases. Actual host/disk-loss/off-server broker restoration, operational
access/retention and eligible hosted workers remain AJ48 acceptance prerequisites.
