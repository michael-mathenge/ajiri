# Checkpoint 3B Phase B preparation — schema package review

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026. Branch feature/verification-delivery-schema, based on deployed,
merged Phase A e4eaefd21f839281d306d6f68cf4fc7c0218cd85. Michael explicitly approved
implementing this additive schema package with tests and stopping afterwards.
The previous AGENTS design-only migration rule is superseded only for this package.
No push, deployment, email delivery, provider/DNS write or further Phase B work.

## Package / scope / suggested points

| Package | Branch | Suggested points |
|---|---|---:|
| Verification and delivery accounting schema | feature/verification-delivery-schema | 5 |

Profile proof columns, new ledger/budget tables, schema constraints, migration and
API-isolation tests, concepts, and this review. No new WP number was invented.
The design decision commit was cherry-picked locally from integration/checkpoint-3b
onto the merged release; original dirty checkout, coverage, stash and config remain.

## Exact new migrations and existing-data impact

- profiles/0003_profile_email_verified_at_profile_verified_email adds nullable
  email_verified_at (None) and blank verified_email ('', max length 254). All
  existing profiles remain unverified. No proof, consent or preferences backfill.
- jobs/0008_deliverydailybudget_deliveryattempt depends on jobs/0007 and the
  existing swappable user dependency. It creates two initially empty tables;
  it does not change the User model, old migrations, application status choices,
  notification receipts, passwords or private files.

DeliveryAttempt contains UUID identity/idempotency, nullable SET_NULL owner/document/
notification links, four channels, four outcome states, keyed recipient digest,
provider reference, bounded category and timestamps. No email address, body,
attachment, token or credential is added. Digest remains personal data for privacy
purposes. There is no sender populating this table yet.

DeliveryDailyBudget stores an explicit day, scope global/user:<id>, and independent
nonnegative application, alert and account counters. Account counter combines
verification/reset. No rows or past sending counts are inferred from console mail.

## Enforced guarantees versus future service responsibilities

Database checks enforce known channel/state/failure categories, channel/link shape,
nonnegative counters, unique idempotency keys, unique (scope,day), and at most one
reserved/unknown attempt for each linked application or notification. Partial
uniqueness remains authoritative if callers bypass model validation.

Creation ownership, required source links, digest format and scope format are
model-validation rules: future services MUST call full_clean (or equivalent explicit
validation) before reserving. Django save()/bulk_create()/update() do not automatically
call full_clean. The database permits null links so SET_NULL erasure works. It cannot
distinguish an erased historical link from a deliberately missing link at insertion.
No false claim of cross-table ownership enforced by SQLite CHECK constraints.

Verification/reset channels forbid document links. Account-message throttles,
deduplication/replay policy and any future account-purpose partial unique constraint
remain service design work; this package does not arbitrarily serialize all account
messages or generate a token table. Receipt state transitions also remain service
work; accepted means provider acceptance, never inbox delivery.

The approved 10/user and 200/platform daily policy (150/30/20 categories) is NOT yet
enforced. Future services need atomic conditional reservations/attempt creation in
short transactions, Nairobi day calculation, no network I/O under SQLite locks,
quota UX, unknown reconciliation and bounded retries. The definite-failure capacity
accounting clarification still needs confirmation. No numeric cap is hardcoded into
schema, keeping approved runtime configuration possible without another migration.

## Verification

Actual local outcomes (Python 3.12.6 / Node 24.19): pip check, Django check,
migration-drift check all passed. Focused schema suite: 9 passed. Full backend:
120 run, 119 passed and one Windows symlink-privilege skip (85.674 seconds).
Locked npm ci, lint, 32 component tests and Vite build passed. No frontend_build
regeneration. The skip requires Linux CI after a future authorized push; no CI or
production tests were triggered by this package. Focused schema tests cover:

- Existing/new profiles start unverified; public Profile serializer cannot write proof.
- Account categories create without document links; no token/payload fields.
- Invalid ownership/missing links/digest validation; database enum/link checks.
- Unique idempotency and unresolved application/notification attempts.
- Separate retry record after definite failure; no actual sending invoked.
- User/document erasure retains null-linked receipt.
- Budget nonnegative checks, duplicate date/scope, separate days/user scope.
- Migration from representative old user/profile/job/application/notification rows,
  preserving hashes, snapshots/preferences/receipts, no ledger/budget backfill, and
  historical model reads against additive schema (normal code rollback strategy).

Tests use only disposable synthetic local databases. MigrationExecutor briefly moves
the TEST database to historical schema; this is not a production reversal. This is
not a quota-service concurrency or token-expiry test: those services do not exist.
No new dependency, frontend source or committed-build changes. Verification builds
only; the packaged frontend must still match dist byte-for-byte.

## Manual local review / reproduction (PowerShell)

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test jobs.test_delivery_schema --noinput
.\.venv\Scripts\python.exe manage.py test --noinput
```

Only these tests apply the migrations locally in this package; no existing local
development database migration was performed. Do not point test settings at a live
database. Production mail settings remain untouched and console-only.

## Future owner deployment and rollback — instructions only

After separate review/push/CI/merge/deployment authorization: record exact release,
pause writers, back up DB/private media and verify recovery, stage migration source,
review migrate --plan for ONLY profiles/0003 and jobs/0008 (plus already-reviewed
history), apply before activating model code, then reload and verify. Stop on an
unexpected migration. Keep redirect=False/HSTS=0 pending the independent host gate.

New model code must not serve before new columns exist. Old code reads the expanded
schema; new ledger tables are unused by old code. Roll back reviewed code WITHOUT
reversing additive schema or replacing newer data. Dropping populated tables or
verification fields loses evidence and requires separate destructive-change approval.
Schema migrations are mechanically reversible but that is not routine rollback.

## Domain inspection and remaining decisions

Read-only Namecheap UI inspection confirmed michaelmathenge.dev ACTIVE through
19 August 2027 with Namecheap BasicDNS in Michael's signed-in account. It is a viable
domain for later sending authentication. This does not prove Brevo authentication,
mailbox existence, DNS propagation or actual deliverability. No domain/private
contact data was copied into source, and no DNS, MX, website or provider settings
changed. Website remains mathenge.pythonanywhere.com. DNS authentication and exact
sender mailbox/reply handling need a separate setup step and authorization.

Still gated: actual transport, reset/verification endpoints, quotas and retries,
account-email throttle defaults, uncertain receipt retention, legal review,
bounce/complaint handling and owner-only pilot approval. No automatic cleanup.
Queued UI fixes remain untouched. Stop after this package for Michael's review.

Reference for database constraints/model validation separation:
[Django constraints documentation](https://docs.djangoproject.com/en/dev/ref/models/constraints/).
