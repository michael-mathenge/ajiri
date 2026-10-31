# Durable delivery queue — inactive

AJ-48 now has real additive jobs.0018 database tasks and a registered Celery worker,
not an inline fixture queue. DELIVERY_QUEUE_ENABLED defaults false. No broker,
worker, scheduler, production flag or hosting configuration was activated.

Each task holds only a kind and existing owner/authorization/notification/search
references, deduplicated by stable server UUID. Broker arguments are the task UUID
only: no recipient, subject, tokens, private bytes or document paths. Application
dispatch can return 202 with a private queue status instead of performing provider
I/O when the queue is enabled; duplicate requests reuse the same task. The existing
authorization receipt remains authoritative and readable when sending is disabled.

enqueue_delivery_work accepts exactly one existing authorization, notification,
due saved search or matching target. Owner targets require --owner-id; matching is
an operator-only global kind. Future/off saved-search windows cannot be enqueued.
delivery_queue --publish-pending publishes at most 20 pending rows (limit 1..50),
with persistent delivery to ajiri.delivery and retry=False. This follows the
[Celery sending API](https://docs.celeryq.dev/en/stable/userguide/calling.html#message-sending-retry).
A publication timeout leaves publication_unknown; no automatic republication occurs.
An original broker message or explicit execution can still claim its original UUID.

Workers atomically claim a three-minute lease and use the same real application,
alert, saved-search or matching service. Delivery authorization, current consent,
mailbox, source freshness, documents, expiry and budgets are checked at execution.
Existing accepted/reserved/unknown receipts prevent another provider call. Simulated
process death before/after handoff is covered; this is not new live broker/host
failure evidence. [Late acknowledgements](https://docs.celeryq.dev/en/stable/userguide/tasks.html#Task.acks_late)
and worker-loss redelivery reuse the database task. Recovery claims are bounded at
three; a lost old lease cannot overwrite the new result. Queue success/acceptance
does not establish inbox delivery, and a dead task is not proof of provider failure.

Operator commands: delivery_queue (counts only), --recover-leases, --execute-id UUID,
and explicit --resume-blocked with execution for a reviewed blocked/reconciliation
task. Resume never changes provider identities or reopens ambiguous mail receipts;
it can reconcile existing results or process previously unattempted eligible rows.
Automatic recovery handles only expired running leases. Unknown/reserved mail stays
in needs_reconciliation, and ambiguous broker publication is never republished by
the publisher. No raw exception/provider text is stored in task status.

GET /api/jobs/delivery-tasks/{task-uuid}/ is owner-only and no-store. It exposes
coarse state/category/times, never leases, recipients or private payloads. Outstanding
queued work requires reconciliation before verified account erasure. Export includes
owner task metadata; settled references use SET_NULL when account data is removed.
No real account export/erasure occurred during this implementation.

Activation prerequisites: actual eligible always-on worker/broker host, private
broker credentials entered outside chat, durable broker/storage/visibility settings,
shared authoritative database/private documents, monitoring/dead-letter ownership,
scheduled bounded publication and lease recovery, queue feedback in the release
client and a real isolated broker/host crash/recovery rehearsal. Worker must consume
the dedicated ajiri.delivery queue. Existing free WSGI hosting is not worker evidence.
No automatic email-collection/scheduler wiring or private credential setup is claimed.

Deploy backup -> additive migration -> paired source -> separately approved flags
and host activation. Rollback stops producers/consumers and disables queue claims;
preserve tasks, leases, approvals, shared receipts and newer data. In-flight cutoff
cannot guarantee cancellation. After any database/storage rollback or lost ledger,
halt all sending and reconcile provider evidence before resuming; restoring an old
snapshot is not proof that a previous handoff never occurred. Never reverse a
populated migration or blindly replay a dead-letter/unknown task.
