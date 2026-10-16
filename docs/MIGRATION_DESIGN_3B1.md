# Checkpoint 3B1 migration design — decisions recorded; implementation gated

16 October 2026. Proposal only: no model field, migration or Phase B feature was
implemented. Approval of this document is a separate gate before schema work.
No AUTH_USER_MODEL definition or migration-history edits. All proposed tables and
columns are additive; no historical consent, verification or delivery backfill.

## 1. Account verification: prefer Profile, no User change

| Proposed field / location | Type | Null / default | Existing rows / purpose |
|---|---|---|---|
| profiles.Profile.email_verified_at | DateTimeField | null=True, blank=True, default=None | Every existing profile remains explicitly unverified; never infer ownership from past login or preferences |
| profiles.Profile.verified_email | EmailField(max_length=254) | null=False, blank=True, default='' | Empty for existing profiles; bind proof to the normalized email actually verified, so changing email never inherits old proof |

Verification is true only if timestamp exists AND verified_email matches the current
account email under the same normalization used by registration. A timestamp alone
must not survive an email-address change as proof. No new required registration
field, forced reset or is_active backfill is proposed. Existing accounts can log in,
browse, edit profiles and draft; real outbound application email is gated on proven
mailbox control in Phase B, as approved for the design. This does not certify legal consent.

Alternative without migration: an expiring signed session/cookie proves only that
browser's recent verification and does not provide durable cross-device/admin state.
An external verification store adds operational dependencies. Prefer the two Profile
fields; no per-account database token is necessary.

Reversibility: adding nullable/defaulted columns is compatible with old code. Old
code ignores them on rollback; LEAVE columns/data in place. A reverse migration
could drop proof, is destructive, and is not a routine rollback. No row rewritten
except future user-initiated verification. Missing Profile must fail safely until
the existing profile-creation flow is repaired; do not auto-mark verified.

## 2. Password reset: no reset-token table

Recommend Django's PasswordResetTokenGenerator, finite PASSWORD_RESET_TIMEOUT
(approved design: 30 minutes), owner mailbox delivery and anti-enumerating request responses.
Token derives from existing account state; store/send no raw token in DB/logs.
Password change invalidates previously issued reset tokens. Endpoint limits must
use existing throttling and independent delivery budgets. Tests must cover weak
password validation, expiry, replay and generic responses for unknown addresses.

The reset endpoint is NOT implemented in Phase A. A successful reset should
blacklist that user's outstanding refresh tokens through the existing blacklist
models, not a migration or new token lifetime. Already-issued access tokens can
remain valid for their existing 15-minute lifetime. Immediate access-token revocation
would need an explicitly approved additional mechanism; do not claim it for free.
No account-wide resets, historical password changes or auth-model edits.

Verification token proposal: Django timestamp signing with a separate purpose salt,
bounded age (approved design: 24 hours), account ID, normalized candidate email, and fingerprint
of verification state. Do not reuse reset tokens for verification. Recheck the account's
current email and atomically update Profile only if the previously signed state still
matches. Repeated verified clicks are a safe no-op; changed/expired state requires a
fresh link. Token material is a credential: never log it or place it in analytics.

Stored-token alternative: a purpose-bound hash, expiry, used_at and user FK would
allow explicit per-link revocation but adds sensitive state, cleanup and migration
complexity. Recommend no stored-token table at launch. Expiry defaults and reset access-token grace are design-approved; exact client/API
contracts and implementation still require the separate Phase B build prompt.

## 3. SMTP/API delivery ledger and shared quotas: jobs app

Use new tables instead of modifying Application.status or Notification history.
This retains the current application state choices while recording uncertainty.

### jobs.DeliveryAttempt (proposed)

| Field | Type / constraints | Null / default |
|---|---|---|
| id | UUID primary key | non-null; uuid4 for new rows |
| user | FK existing user, SET_NULL | null=True; None |
| application | FK jobs.Application, SET_NULL | null=True; None |
| notification | FK jobs.Notification, SET_NULL | null=True; None |
| channel | CharField(24), application/alert/email_verification/password_reset | non-null; no database default; explicitly provided on creation |
| state | CharField(24), reserved/accepted/definite_failure/unknown | non-null; 'reserved' |
| idempotency_key | UUID unique | non-null; uuid4 |
| recipient_digest | CharField(64), normalized-address keyed digest | non-null; no default, supplied by sending service |
| provider_message_id | CharField(255) | non-null; '' |
| failure_category | CharField(32), allowlisted category only | non-null; '' |
| created_at | DateTimeField(auto_now_add=True) | non-null; creation time for new rows |
| resolved_at | DateTimeField | null=True; None |

No body, subject, CV bytes, raw provider response, token or credentials. The digest
is pseudonymous personal data, not anonymization; key rotation and metadata retention
need legal/operations review. Use the application/notification link plus provider
receipt for reconciliation. No original recipient address is duplicated in this
ledger. If future operational needs require it, request approval first.

Proposed creation rules: application delivery has an application link; alert delivery
has a notification link; email_verification/password_reset have a user link and
neither application nor notification. Later SET_NULL erasure is allowed. Never store
verification/reset links or tokens in the ledger. Exact database/service constraints
for nullable historical links require review before generating migrations.
A partial uniqueness constraint permits at most one reserved/unknown attempt per
application or notification. Unknown outcomes must be reconciled before creating a
new attempt; a definite failure may retry with a new attempt. Accepted application
attempts plus existing Application.status prevent repeat send. For alerts, correct
only future sent_email flags after acceptance; no resend/relabel of historical rows.

### jobs.DeliveryDailyBudget (proposed)

| Field | Type / constraints | Null / default |
|---|---|---|
| id | BigAutoField primary key | non-null; automatic |
| scope | CharField(64): global or user:<id> | non-null; no default |
| day | DateField, Africa/Nairobi calendar date | non-null; explicitly supplied |
| application_reserved | PositiveIntegerField | non-null; 0 |
| alert_reserved | PositiveIntegerField | non-null; 0 |
| account_reserved | PositiveIntegerField, shared verification/reset allocation | non-null; 0 |

Unique(scope, day), nonnegative counters and indexes supporting that key. New empty
tables have no impact on existing rows. Do NOT prepopulate rows or derive past send
counts from sent/status history: console-only success was not real delivery.

Reserve global/application capacity and user capacity atomically with conditional
updates in one short DB transaction; create the attempt in that transaction. Enforce
10 applications/user/day and 200 total attempts/day: 150 applications, 30 account
emails and 20 alerts. Use Africa/Nairobi calendar days; no automatic borrowing
from another allocation. Account requests also require per-user throttling. At caps,
preserve application drafts and show availability guidance; reset requests retain
generic anti-enumeration responses. Network I/O occurs after
commit, never while holding SQLite locks. Accepted/unknown outcomes consume capacity. Michael approved the clarification: for an attempts-based cap, count
definite provider failures once a network attempt is made too; release only
reservations cancelled before any send attempt. This supersedes the earlier failure-refund proposal; retries cannot evade the provider allowance. No automatic unknown retry or midnight refund
of an old unresolved attempt. Bounded alert retries only after definite failure.
DRF file-cache counters are not the hard quota and cannot replace these tables.

Delivery metadata retention is approved at 30 days, subject to privacy review.
This covers attempts and daily budget metadata, not payloads or authentication tokens.
Unresolved outcomes at expiry need a reviewed minimization/reconciliation policy so
purging a ledger cannot unlock duplicate delivery. No purge command is authorized. Do not delete
attempts/budgets under WP22 backup retention: that command never prunes anything.
No hourly table is proposed; existing request throttles remain independent of daily
accepted/uncertain delivery quotas. If a hard rolling-hour quota becomes required,
design it separately before implementing rather than approximating it silently.

Alternative without migration: disable real delivery and retain manual owner-only
pilot controls. File/memory caches and provider daily caps cannot reliably enforce
shared user/global reservations or reconcile unknown outcomes. Provider idempotency
is useful if supported, but acceptance is not inbox delivery or exactly-once proof.

## 4. Deployment and rollback compatibility

1. Michael reviews exact schema/constraints and policy first. Future migrations add
   only these columns/tables; makemigrations is forbidden in this Phase A design work.
2. Back up, stage migration source, pause sending/sweeps, apply migrations, then
   activate reviewed Phase B code. Old code bypasses quotas/verification, so do not
   run old and new senders concurrently. No destructive data migration/backfill.
3. Keep real delivery operator-disabled until provider connectivity, sender/domain,
   global cap, application/alert allocation and account verification are approved.
4. Rollback: stop real sending first, preserve ledgers/proof, restore previous reviewed
   code/config without reversing additive schema. Do not return to old console code
   while presenting a false real-delivery success claim. Reconcile unknown attempts
   before resuming. Never roll back DB over newer writes.

Mechanically reversing the new tables/columns would lose evidence and is destructive;
separate explicit approval and an export/recovery policy would be required. Privacy
deletion later must cover ledger linkability/retention and backups under legal review.

## 5. Decision record — 16 October 2026

Michael approved, in this chat, DESIGN ONLY:

- The two Profile verification fields; all historical users remain unverified.
- Reset expiry 30 minutes, existing outstanding refresh tokens blacklisted after
  reset, existing access tokens retaining their up-to-15-minute grace.
- Purpose-bound signed verification links, 24-hour expiry, no token table.
- Unverified users can log in/browse/edit/draft but cannot send real applications.
- Delivery ledger, shared quotas, uncertainty counting and no automatic unknown retry.
- Ten applications per user/day; 200 global attempts/day with fixed 150/30/20
  application/account/alert allocation; cap UX and 30-day metadata retention subject
  to privacy review. Verification/reset categories and account budget extension
  explicitly approved afterwards. No actual migrations authorized by these answers.

Read-only provider evidence: a credential-free curl from Michael's PythonAnywhere
console returned HTTP 401 at https://api.brevo.com/v3/ on 16 October. DNS/TLS/HTTPS
reachability works; this does NOT prove authenticated API sending or account approval.
Brevo UI showed a 300-email daily allowance and one verified freemail sender, with
freemail compliance warning. Domains page had no configured sending domain. No keys
were opened, no email sent and no provider configuration changed.

The website remains https://mathenge.pythonanywhere.com. It is not a DNS-controlled
sending identity for this project. Michael will obtain domain/DNS control later;
no assumption of ajiri.co.ke ownership. Public email activation is blocked pending
sender authentication. Owner-only pilot allowlisting is recommended but NOT yet
explicitly approved; do not interpret 'continue' as delivery/credential authorization.
Console backend remains unchanged.

## 6. Remaining design details and build gate

- Review exact creation/partial uniqueness constraints for account-message attempts,
  repeated requests, null links after deletion, and concurrency; account messages
  must not reuse application/notification-only constraints.
- Select per-user account-email request limits and retry/backoff bounds. No new
  numeric default is approved by this document.
- Confirm metadata expiry handling for unresolved attempts, digest key rotation,
  provider receipt reconciliation, bounce/complaint handling and legal retention.
- Obtain controlled sending domain verification and explicit owner-only pilot policy
  before real delivery. Michael configures all credentials privately.
- Future tests: old rows remain unverified, migration/rollback compatibility,
  reset/verification expiry/replay/email change, overlapping budgets and Nairobi day
  rollover, fixed category capacity, repeated account requests, definite/ambiguous
  failures, alert opt-in, retention and erasure.

Phase B remains STOPPED until Michael sends a separate implementation prompt and
approves exact migrations. Domain setup can proceed independently; no production,
model, migration, auth, SMTP or provider-setting change is made in this update.

## 7. Subsequent schema-only build authorization

Michael explicitly authorized implementing the verification and delivery-budget
migrations with tests, keeping console email unchanged, no push/deployment, and
stopping after the package. This supersedes the earlier implementation gate only
for these additive fields/tables, not transport/accounts endpoints or sending.
See CHECKPOINT3B_SCHEMA_REVIEW.md for implemented constraints and remaining service
policy decisions. michaelmathenge.dev was confirmed active in the signed-in
Namecheap account, with Namecheap BasicDNS; DNS authentication in Brevo is pending.
No DNS/provider writes or secret access were performed.

## 8. Subsequent dormant transport/service authorization

After approving the schema review, Michael approved the isolated transport and quota
service package and confirmed that definite failed provider attempts count against
capacity. This does not authorize endpoints/tasks integration, real sending, provider
credentials, DNS changes, push or deployment. See CHECKPOINT3B_DELIVERY_REVIEW.md.

## 9. Accounts flow and approved reset-revocation extension

Michael approved reset/verification implementation with real delivery disabled, then
explicitly approved the discovered revocation fix: nullable Profile.password_reset_at,
password-bound new refresh claims and rejecting legacy refresh tokens after reset.
profiles/0004 adds DateTimeField(null=True, blank=True, default=None), no historical
backfill. New reset writes the marker; old rows otherwise stay None. No User change.
New auth code must follow migration. Rollback after resets MUST preserve the marker
and refresh guard: old code would ignore the marker and accept legacy untracked
refresh tokens. Dropping the marker loses revocation evidence and is destructive,
so code rollback is limited to retaining the guard or a separately reviewed session
invalidation plan. Existing access tokens keep their approved 15-minute grace.
See CHECKPOINT3B_ACCOUNTS_REVIEW.md for implementation, tests and activation gates.
