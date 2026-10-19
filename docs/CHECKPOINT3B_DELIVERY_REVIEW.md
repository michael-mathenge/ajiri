# Checkpoint 3B — dormant Brevo transport and quota service review

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026. Branch feature/brevo-delivery-service, based on locally approved
schema package 6fe90d3. Michael authorized this package and confirmed that definite
provider failures consume quota. No push, deployment, provider/DNS write or real
email. Schema package remains an unpublished prerequisite; no new migration here.

## Package / suggested points / files

Suggested 8 points: isolated adapter, transactional accounting, concurrency/recovery
tests and documentation. jobs/brevo_transport.py contains the standard-library HTTPS
adapter; jobs/delivery_service.py contains accounting and orchestration. Tests in
jobs/test_delivery_service.py. Existing endpoints, ingestion, matching, auth client,
Django EMAIL_BACKEND, configuration, dependencies and CI remain untouched.

## Delivery contract

- Disabled by default: DeliveryService requires explicit enabled=True from a future
  reviewed caller; there is no environment activation switch in this package. No
  production view/task imports the service. Existing console mail remains unchanged.
- The adapter receives configuration through its constructor (no credentials loaded
  or persisted). Repr redacts configuration. Uses POST only to Brevo's fixed HTTPS
  /v3/smtp/email endpoint, standard-library TLS verification, bounded timeout and
  response reads, with redirects forbidden. No arbitrary headers or recipients list.
- Frozen one-recipient payload: platform From, applicant Reply-To for applications,
  plain text and optional byte attachments. No URL attachments or file fetching;
  attachment limit must be explicitly supplied by future approved caller, otherwise
  attachments are disabled. No new numeric attachment policy was selected.
- Only a 201 with valid compact messageId is accepted. Acceptance is not delivery.
  4xx (except ambiguous 408) is definite failure; 5xx, redirect, timeout, malformed
  acceptance or unexpected transport errors are unknown. Never log raw provider
  bodies or exception text. No provider/network automatic retry loop.

Provider contract verified against [Brevo transactional API reference](https://developers.brevo.com/reference/send-transac-email)
on 16 October 2026. No authenticated API call was used to verify implementation;
all sending tests mock network access. No provider exactly-once guarantee claimed.

## Atomic accounting and eligibility

Defaults: 200 total attempts per Nairobi calendar day, fixed allocations 150
applications / 30 combined verification-reset / 20 alerts, and 10 applications per
user/day. Policy values are validated injectable configuration, not an activated
production setting. Allocations cannot borrow from each other. Conditional total
check also protects against legacy/changed policy counters already at the global cap.

Preflight checks payload/recipient/owner/purpose before reserving. Applications must
be email-ready and match the current verified mailbox; checks are repeated under
the reservation writer lock. Account recipients must match the account. Alert
delivery needs both notify_email and explicit confirmation supplied by a future
consent-aware caller; current historical preferences alone are insufficient proof.
No public account-email endpoint exists, and its request throttles remain a prerequisite.

The first DB operation inside the transaction is an insert-or-ignore global budget
row. On SQLite this serializes competing writers before read checks, including cold
initialization. One transaction conditionally reserves global/category and user
capacity and writes the validated unique receipt. Per-user failure rolls back its
global increment. Existing schema constraints guard unresolved application/alert
attempts and idempotency keys. No new cache, lock table or dependency.

Network I/O runs only after commit; caller transactions are rejected. Up to three
database-only lock attempts occur before any provider call, with short backoff.
If accounting stays busy, fail generically with no email attempted. No database
retry happens after a provider call. Payload/body/token/recipient address is never
stored in the ledger; only keyed recipient digest and minimal receipt metadata.

## Outcomes, retries and crash recovery

- Once reserved, accepted, definite failure and unknown all consume daily capacity.
  Invalid/preflight-rejected requests do not reserve. No refund API is exposed;
  a crash after reservation conservatively keeps capacity even if no send occurred.
- Repeating a key with the same purpose returns its receipt and never calls Brevo
  again. Reusing it for another owner/purpose/source/recipient fails without sending.
- A different key cannot repeat an accepted/reserved application/alert. Unknown
  outcomes block fresh attempts across midnight, preserving duplicate protection.
- A definite-failure application retry must explicitly name the failed receipt and
  use a new key; it consumes another attempt. Automatic retries are absent.
- Alert retry bounds have not been approved, so alert retries are disabled rather
  than inventing a count/backoff. Account resend/request limits remain future caller
  policy; no public path exists to exploit their missing integration.
- Unknown retries remain blocked until a separately reviewed reconciliation flow can
  resolve provider evidence and show a warning. A warning alone is not reconciliation.
  This package deliberately does not add an operator resend button or destructive
  state-reset command. Accepted/unknown expiry handling also remains pending.
- If the worker crashes or recording the receipt fails after provider acceptance,
  reserved state survives and blocks repeats. Database recovery can leave uncertainty;
  it does not justify retrying. Exceptions are replaced with generic safe messages.

The service writes accounting receipts only. It does not change existing Application
status or Notification.sent_email. Those lifecycle updates need a later coordinated
integration package; do not mix old senders and new services for real delivery.

## Actual verification

Focused tests (21 passed) cover payload/attachment limits/Reply-To, fixed endpoint,
redirect refusal, status classification, response limits, network ambiguity, redaction,
disabled defaults, verified ownership, ten-user cap, shared account allocation,
global/category boundaries, Nairobi midnight, idempotency conflicts, explicit failure
retry, alert consent/retry guard, unknown outcomes, DB-busy bound, no outer transaction,
sanitized unexpected errors, and durable reservation after receipt-write failure.

Two real-thread tests use the disposable SQLite test database with mocked transport:
same-request race produces one provider call; competition for the final platform
slot yields one acceptance and one quota rejection. Test transport asserts that no
network call occurs inside a transaction. No provider API key or real CV used.

Actual final gates: Python 3.12.6, pip check/system check/migration-drift check pass;
141 backend tests run in 75.542 seconds, 140 passed and one Windows symlink-privilege
skip. Node 24.19 locked npm ci, lint, 32 component tests and build pass. The Windows
skip still requires Linux CI after a future authorized push. No CI run claimed.
Frontend dist matches committed frontend_build byte-for-byte; verification build
only, with no artifact regeneration.
No changes to existing/new migrations from the previously approved schema package.

Reproduce locally in PowerShell:

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py test jobs.test_delivery_service --noinput
```

## Activation prerequisites / rollback / stop

Real delivery remains blocked pending authenticated sending-domain setup, sender/
reply handling, explicit owner-only recipient pilot approval, reviewed credentials
entry by Michael, account-email throttles, alert consent storage/confirmation, retry
bounds, attachment policy, bounce/complaint and unresolved receipt retention policy.
Website remains mathenge.pythonanywhere.com. michaelmathenge.dev DNS settings are
untouched. Console rollback halts real mail; no silent success claim should replace
real delivery after a later activation.

This package needs no production operation. Future integration requires review,
backup, schema migration before activation and end-to-end lifecycle/502/400/quota
UX tests. Until then, dormant service methods are internal building blocks, not a
supported sending API. To roll back this package, restore the reviewed code only;
keep additive schema and receipts. No DB restore, credential change or DNS rollback.

Stop for Michael's review. No push/deployment or further accounts/SMTP integration.
