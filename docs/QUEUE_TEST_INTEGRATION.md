# Background delivery: closed inline integration

24 October 2026. AJ-48 first scope uses an inline fake executor before provisioning
a broker or worker. It is not a running queue service. The PythonAnywhere free
WSGI app has not acquired an always-on worker. No Celery schedule, ingestion
endpoint, hosting, credentials or CI configuration changes are included.

## Contract

An immutable application envelope holds only owner ID and the exact authorization
UUID. It contains no email address, text, file bytes, provider secret or new retry
identity. The worker resolves current ownership and delegates to the existing
application dispatch service, which checks document approval, authorization,
pilot eligibility, attachments and shared budget. Queue insertion is not consent
or permission to send. Delay cannot bypass expiry, withdrawal or changed documents.

Duplicate queue execution uses the same authorization and delivery ledger key.
A settled/unknown/reserved receipt is reconciled rather than initiating another
provider call. Provider acceptance still does not prove inbox delivery. A simulated
crash before/after handoff leaves the message requiring explicit reconciliation;
the inline executor does not automatically retry an uncertain worker exception.
After handoff, the existing receipt prevents a second network call even if the
queue acknowledgement was lost. Queue acknowledgement is not financial or delivery
authority, and it must never mint a fresh authorization/idempotency key.

`DELIVERY_QUEUE_TEST_CAPTURE=False` is a constant, not an environment activation
switch. No production route/task imports the executor. Tests override it, use
synthetic users/private documents and capture Brevo transport calls. Default-off
execution does not create budget/attempt records. Turning this lab off does not
remove the ordinary authenticated receipt/reconciliation API or delivery evidence.

## Verified scope and limitations

Nine focused tests passed3.711s: duplicate messages, default closed, expiry and
withdrawal, unknown outcome, crashes before/after handoff, ownership, shared pilot
quota and changed package evidence. Initial runs had invalid fixture assumptions
about CV revision reuse, expiry constraints, receipt categories and exception
types; corrected without weakening runtime checks. Full423 Django tests passed
329.895s (one known platform skip), system/drift and Ruff passed. Node24.19 locked
installation audited364/zero vulnerabilities; lint/build2.01s passed and all36
generated files match unchanged committed bytes. CI/release remain pending.
No real message was sent.

The inline lock models local acknowledgement serialization only. It does not
prove durable broker acknowledgements, leases, multi-process delivery, operational
recovery, dead-letter handling or queue encryption/access controls. Existing
delivery-ledger concurrency tests cover reservation logic independently; the
queue-specific quota test consumes capacity serially, not a distributed load test.

Before a real worker: verify platform eligibility and cost, choose a private
broker/worker, use durable minimal envelopes and bounded retention, demonstrate
duplicate/redelivery/lease loss/process-crash behavior with the shared ledger, and
exercise operator reconciliation without repeating unknown provider IO. A real
alert executor additionally needs current verified consent and unsubscribe checks;
this package adds only application test integration. The current owner-only pilot
and separate sending authorization remain in force.

Rollback stops new queue submissions and workers, retains authorizations/receipts
and reconciles in-flight uncertainty. Do not purge evidence, infer cancellation
after handoff or restore an old database over newer delivery decisions. Removing
this unused inline lab affects no production queue or account state.
