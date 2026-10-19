# Checkpoint 3B — account-email integration review

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026. Branch feature/account-email-integration, based on the approved
accounts package 5e98331. Suggested 5 points. Scope explicitly approved: integrate
account emails with delivery accounting, tests, real sending disabled, no push,
deployment or DNS changes, stop for review. No new migration/dependency.

## Changes

accounts/email_delivery.py bridges reset/verification link creation to the reviewed
DeliveryService. Requests use the common atomic ledger/daily budgets rather than
bypassing accounting with a direct EmailMessage call. Both purposes consume the
same 30-message account allocation, within the approved global 200 and fixed
150 application / 30 account / 20 alert partitions. Failed provider attempts count;
no refund for an attempted send. Existing IP/user/target throttles remain unchanged.

There is deliberately NO production transport factory in this package. The only
bridge sink is MemoryTransport; it requires explicit ACCOUNT_EMAIL_TEST_CAPTURE=True
AND the exact Django locmem backend, checked again at send time. Other backends,
including console/SMTP, cannot activate it. No Brevo credentials/configuration read,
API call, live email, DNS write or provider setting change. Existing console job
mail is untouched. Real activation needs a separately reviewed provider factory,
sender/domain and pilot controls; do not swap a backend to activate this test path.

When disabled, requests do not generate security tokens, create receipt/budget
rows, construct the test transport, or send email. Existing truthful disabled-email
UI remains. Opt-in tests exercise the real accounting service with an in-memory
message sink; mock results cover rejection and uncertainty without network calls.

## Request identity and retry behavior

Reset and verification request serializers accept optional request_id UUID in JSON;
absent IDs are generated server-side for older callers. Modern frontend creates a
UUID per logical action. Network errors keep it for a manual repeat, so a completed
request whose response was lost does not send again. Changing the target email
starts a new action. Explicit requests after accepted responses or definite 502
failures use a new ID. No new custom header or CORS change.

DeliveryService remains authoritative for same-key binding, atomic quota, concurrent
duplicates and uncertain receipts. A matching repeated ID reuses the old receipt;
another user/purpose/recipient cannot reuse it to send. A NEW explicit request may
select its latest definite-failure receipt for retry, consuming another slot. There
is no background/provider retry. Unknown/reserved outcomes block fresh sends even
after midnight; this API does not reconcile/reset them or provide a bypass button.

Only keyed recipient digests and minimal receipts enter the database. The bridge
derives its digest key from Django signing configuration using a separate purpose;
no new secret is stored. Email bodies, links and token material stay in memory and
the test outbox. Signing-key rotation and metadata expiry must be separately reviewed
to preserve uncertain-outcome duplicate protection. No automatic retention cleanup.

## Safe response contract

Public password-reset requests retain the SAME 202 JSON for known/unknown/inactive/
unusable accounts and for accepted, failed, quota-blocked or uncertain delivery.
They expose no receipt ID or provider state. Generic text warns that a previous
attempt may already have been accepted and to check the inbox before requesting
again. Validation errors and request throttles remain account-independent 400/429.
No claim of constant-time real provider sending is made: none is enabled here.

Authenticated verification can report its owner's outcomes:

| Outcome | HTTP / behavior |
|---|---|
| Disabled | 202, delivery_available false; no send |
| Already verified | 200, no new attempt |
| Accepted | 202; provider acceptance is not inbox delivery |
| Definite failure | 502; states capacity consumed and a new explicit request may retry |
| Account/platform quota | 429 plus Retry-After until next Nairobi midnight |
| Unknown, reserved or accounting unavailable | 409; check inbox and require reconciliation |

New responses retain private/no-store via existing account view finalization.
Frontend renders safe detail/error arrays, 429 guidance and network uncertainty
warning. Existing bounded CSRF retry remains limited to pre-side-effect rejection;
ordinary 409/429/502/network failures never automatically repeat a mutation.

## Tests / gates

Focused final integration plus existing recovery suite: 26 passed. New tests prove shared
purpose accounting, 30-slot cap, no allocation borrowing, one send per request ID,
generic public uncertainty/quota/absence, authenticated 409/502/429, consumed failed
attempts with explicit new retry, SMTP/Brevo no-call guards, no disabled token/DB
side effects, bad request IDs/origins, and Nairobi midnight Retry-After. No real
messages or credentials used. Existing service thread tests remain in full suite.

Recovery tests now use TransactionTestCase instead of TestCase because the delivery
service intentionally rejects outer database transactions before network I/O.
Fixtures/assertions remain; isolation now matches real non-atomic request handling.
Frontend adds tests for retained UUID after network failure and no automatic retry
of uncertain verification. Final gates: Python 3.12.6, pip check/system check and
migration-drift check passed; 167 backend tests run in 76.113 seconds, 166 passed
and one Windows symlink-privilege skip. Node 24.19 locked npm ci, lint, all 44
component tests and build passed. No CI/production/E2E run claimed. The memory sink
pins its connection explicitly to locmem even if configuration changes after the
gate; a dedicated test confirms it cannot open SMTP. Already-verified requests also
prove no charge or duplicate mail. frontend_build is packaged once as the final
package commit from the verified dist. No source dependency/lockfile changes.

## Local review (PowerShell)

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py test accounts.test_email_integration accounts.test_recovery --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Use synthetic test DB only. Tests themselves opt into memory capture; do not print
captured message bodies/links or enable it on production. On an independently
prepared local app with default settings, request reset/verification and confirm
the UI says no email was sent. No backend/credential change is needed for that check.

## Rollout, rollback and remaining prerequisites

No rollout is performed. This branch contains local schema, delivery and accounts
prerequisites. Any future approved release needs verified backup, staged migration
source, reviewed migrate --plan (jobs/0008 and profiles/0003/0004 if not yet applied),
migrations BEFORE code activation, and coordinated frontend/server smoke checks.
No new migration in this package. Keep production redirect=False/HSTS=0 pending the
independent host scheme gate. No changes to production configuration or deployment SHA.

Rollback must retain the reviewed password-reset marker/fingerprint refresh guard
after resets have occurred; see CHECKPOINT3B_ACCOUNTS_REVIEW.md. Disabling the new
bridge/test capture leaves real mail disabled. Retain ledger/budget rows and newer
DB writes. Do not restore an old database, reverse proof migrations or blindly revert
to pre-reset refresh code. Preserve receipts for uncertainty reconciliation.

Before real sending: authenticate domain/sender, approve owner-only recipient pilot,
configure credentials privately, review production factory/digest-key rotation,
bounce/complaint handling, uncertain-receipt reconciliation/expiry and legal retention,
then authorize a separate activation package. Account reset/verification consent is
not optional job-alert consent. Applications, alert defaults, pending UI fixes,
payments, auth-token logic and DNS/provider settings are untouched here.

All commits must use configured noreply identity. Stop after this package for review.
