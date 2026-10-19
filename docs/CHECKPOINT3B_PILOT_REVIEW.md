# Checkpoint 3B — owner-only account-email pilot review

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026. Branch `codex/owner-email-pilot`, based on documentation preparation
`c4b6a37` and reviewed account-email integration `92c739d`. Suggested 5 points.
Michael approved building the pilot controls/tests with real sending disabled,
no push/deployment and stop for review. Scope supersedes the previous test-only
factory restriction; no token/reset/refresh logic, migration, dependency, frontend
source, CI, ingestion, CORS, DNS or production changes.

## Changes

`accounts/pilot.py` validates explicit owner-only configuration and constructs the
isolated Brevo adapter. `REAL_EMAIL_ENABLED` defaults false. Disabled settings do
not read BREVO_API_KEY; no credential was accessed or created during this package.
Activation requires owner_pilot mode, a positive owner ID, one exact recipient,
one sender address, HTTPS link origin, timeout 1–60 seconds, console Django backend
and test capture off. Wildcards, surrounding whitespace and header injection are
rejected. Invalid/incomplete configuration yields sanitized system check accounts.E001
and fails closed at runtime. System checks construct but never call the transport.

Only an active matching owner whose current account address matches the recipient
can request a pilot reset/verification delivery. Eligibility is checked BEFORE
creating a security token or budget row. Recipients are normalized case-insensitively,
never rewritten. Non-owner reset responses remain generic; authenticated verification
truthfully reports delivery unavailable. No public lookup reveals provider outcomes.
Synchronous pilot responses are not constant-time; enumeration resistance has no
timing guarantee. The owner mailbox must be confirmed privately before activation.

The service repeats owner/channel/address checks under the SQLite writer reservation
lock. The transport wrapper checks single-recipient payload, sender and configuration
again before provider I/O. No CC/BCC, attachments, Reply-To overrides, application
or alert channels. From display name is fixed to Ajiri; sender address is privately
configured to the verified alias. Existing standard-library adapter retains fixed
HTTPS endpoint, redirect refusal, timeout bound, response bound and sanitized errors.

An extra ceiling defaults to five attempts per Nairobi day; configuration may lower
it to 1–4, not expand it. The existing atomic global conditional reservation uses
min(200, pilot ceiling), counting ALL prior global usage that day. Fixed approved
allocations remain 150 application / 30 combined account / 20 alerts, per-user
application cap 10. Those existing limits are Policy fields, not new env settings.
No migration, independent cache counter or quota refund. If earlier non-pilot usage
already exceeds five, the pilot waits until the next Nairobi day.

Failed sends consume capacity. Unknown/reserved outcomes block further attempts;
same-key requests never resend. Only explicit new requests after definite failure
may retry, consuming another slot. No network/background retry or reconciliation
bypass. The budget/receipt transaction completes before network I/O. A configuration
change after reservation can conservatively leave an unknown receipt rather than
permit sending outside the allowlist.

Application and alert callers remain on the EXISTING Django console backend;
they are not wired to Brevo. Pilot configuration refuses SMTP or another Django
backend. Existing console output can still contain private application/alert text;
new security links never fall back to console. Do not publish platform console logs.

## Actual verification

Python 3.12 environment: system check, migration drift check and pip check passed.
Full Django suite: **178 run, 177 passed, one Windows symlink-privilege skip**,
75.048 seconds. No CI/Linux/production/inbox test claimed. Focused first run caught
two issues: wildcard email local parts needed explicit rejection, and an existing
test-sink connection-pinning contract needed preserving. Both fixed; focused
22 tests then passed, and the full suite includes two additional pilot tests.

New tests cover default-off no-link/no-write behavior, incomplete settings, wildcard/
header rejection, sanitized checks, non-owner/changed address/purpose blocking,
single exact recipient, case normalization, fixed sender name, same-key idempotency,
shared purpose cap, concurrent last slot, prior-day/global use and next-day reset,
consumed failures, unknown no-retry, final-boundary CC/recipient/disable rejection,
no printed account links, generic public reset and truthful private rejection.
Every provider send is mocked; synthetic data only, no credentials or real email.
Existing adapter/service/recovery/ingestion tests remain in the full suite.

Production-like dummy `check --deploy`: only W005/W021 (includeSubDomains/preload)
remain, intentionally disabled under the approved short-HSTS policy. No settings
were applied to production; redirect/HSTS scheme gate remains independent.

Node 24.19: explicit locked npm ci, lint, **44 frontend tests passed**, build passed.
No frontend source/build/lockfile diff. Existing committed frontend_build remains
unchanged because this is a backend package. Initial restricted runs hit filesystem
permissions and the default npm launcher used old Node 22.15; corrected by explicit
Node 24 npm-cli and approved execution permissions. The restricted backend run was
interrupted after media filesystem errors; the complete unrestricted run above
passed. These were local tooling limitations, not passing claims for those attempts.

## Local review script (PowerShell)

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:REAL_EMAIL_ENABLED = 'False'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test accounts.test_pilot accounts.test_email_integration --noinput
```

Expected: system check clean, no model changes, all focused tests pass with mocked
provider calls only. Do not set live pilot credentials or enable sending for review.
Tests temporarily override settings internally with synthetic values.

## Release, rollback and remaining decisions

Follow `docs/OWNER_EMAIL_PILOT.md` only after separate release authorization:
reviewed pinned SHA, green CI, private verified backup/restore, stage code, inspect
and apply the previously approved prerequisite migrations BEFORE activation,
private credential entry by Michael, paired release smoke checks, then separately
approved owner-only sending. No migration in this package. Existing schema/account
prerequisites are unpublished local work; do not deploy this patch in isolation.

No actual owner ID/recipient or secret is committed. Before activation confirm the
owner account still uses the mailbox selected for the pilot; do not silently change
account addresses. Alias receipt and Brevo connectivity/delivery remain unverified
by this implementation. Confirm provider account sending eligibility privately.
Credential setup, push/merge/deployment and real-message tests remain unperformed.

Rollback: set REAL_EMAIL_ENABLED false, reload and verify disabled responses/no
provider contact. Retain receipts, verification state, password-reset marker and
patched refresh revocation guard. Prefer a forward fix. Never restore an old DB
over newer writes or roll back to pre-reset auth code. Runtime credential rotation,
uncertain-receipt reconciliation/expiry and legal retention need separate review.
Bounce/complaint automation is not implemented: stop the supervised pilot on either;
do not expand to public users. Application integration, attachment policy and
consent-aware alert delivery remain later packages. Queued product UI fixes untouched.

Commits use the configured noreply author/committer identity; Git config/stash and
the original checkout's lockfile/coverage are preserved. Stop for review here.
