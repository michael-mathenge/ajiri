# Checkpoint 3B — password reset and email verification review

16 October 2026. Branch feature/account-recovery-verification, based on reviewed
dormant delivery package 1e0e412. Suggested 8 points. Michael authorized these flows
and separately approved the narrow reset-revocation design extension after the
existing untracked rotated-refresh issue was identified. No push or deployment.

## Changes and boundaries

New APIs under /api/accounts/:

| Route | Access / operation |
|---|---|
| password-reset/request/ | Public POST, generic 202 for eligible/unknown/inactive accounts |
| password-reset/confirm/ | Public POST, token plus matching validated new passwords |
| verification/request/ | Authenticated POST for current address |
| verification/confirm/ | Public POST with purpose-bound signed proof, explicit confirmation |
| verification/status/ | Authenticated GET, verified boolean for current address |

Every mutation uses existing Django CSRF/token plus exact Origin checks; no CORS
expansion. Public recovery endpoints ignore stale JWT headers and the existing
axios client gains only their public/CSRF classifications. CSRF retries remain
bounded and occur only for identified pre-side-effect csrf_failed rejections.
All new API responses are private/no-store. No JWT or token link in JSON responses.

Reset uses Django's standard PasswordResetTokenGenerator with PASSWORD_RESET_TIMEOUT
1800 seconds, explicit validation against configured password validators, every
field-keyed error, password confirmation, active/usable account checks, atomic
password/revocation updates and replay rejection. No automatic login. Password/email
changes invalidate old reset links. Existing hashes are never changed en masse.

Verification uses a separate signature purpose salt and 86400-second expiry,
binding user/current email/profile verification state/password state. GET does not
verify. Valid repeated clicks are harmless; mismatched/changed/expired/tampered links
fail. Resetting an unverified account's password invalidates its old verification
link. Status compares current address to proof; historical accounts remain unverified.
Email verification is not optional-processing consent or legal compliance.

## Real email remains disabled

Existing Django console EMAIL_BACKEND and the dormant Brevo service are unchanged.
New security links are NEVER written to console, sent through SMTP/Brevo, returned
through the API, or stored in a token table. A closed test-capture path requires BOTH
ACCOUNT_EMAIL_TEST_CAPTURE=True and the exact Django locmem backend. There is no
environment activation flag for real email. Default/mismatched backend does not
generate a reset token or send mail. No credentials were read or written.

UI explicitly states "Email delivery is not enabled yet. No email was sent."
This is a testable feature scaffold, not a functioning public mailbox recovery
service until a later reviewed sending integration. Future real email must go
through approved budgets, owner-only rollout controls and provider/domain setup;
do not simply replace the test backend with SMTP. Existing console job mail remains
unchanged and can still contain private content outside the new security-link flow.

## Approved reset revocation extension and migration

profiles/0004_profile_password_reset_at depends on profiles/0003. Adds only a nullable,
blank DateTimeField default=None. No User model change or historical migration edit.
Existing rows remain None; reset is the only new flow writing the marker.

Previously RefreshView manually rotated identifiers but did not persist the new
token in OutstandingToken. Blacklisting only recorded tokens after reset would
miss those old live tokens. New login tokens include a keyed password fingerprint;
refresh checks the current account/password, rejects inactive/missing owners,
and registers rotated tokens through the existing library outstand() method.

Legacy no-fingerprint tokens remain valid for accounts without a reset marker.
After that account resets, all legacy tokens fail, including untracked rotated
tokens. Fingerprinted tokens fail after password change. Reset also blacklists
recorded outstanding tokens and deletes the requesting browser's refresh cookie.
New login after reset works immediately. JWT lifetimes, existing rotation/blacklist
configuration, HttpOnly/Secure/Lax behavior and access-token validation are unchanged.
Existing access tokens retain up to their ordinary 15-minute lifetime.

The reset transaction's first operation is a no-op user update, serializing SQLite
writers BEFORE checking the token/password; select_for_update alone is insufficient
on SQLite. Verification similarly claims its Profile before checking/updating proof.
No SMTP/network I/O inside either transaction. No reusable stored raw reset token.

## Request limits and token handling

| Setting name | Default | Key |
|---|---|---|
| THROTTLE_ACCOUNT_EMAIL_RATE | 5/hour | Resolved IP for public reset; user ID for authenticated verification |
| THROTTLE_ACCOUNT_TARGET_RATE | 3/hour | Combined reset/verification, keyed digest of normalized email |
| THROTTLE_ACCOUNT_CONFIRM_RATE | 10/hour | Resolved IP |
| THROTTLE_VERIFICATION_STATUS_RATE | 60/min | User ID |

Rates are env-overridable and use the existing shared throttle-cache alias and
NUM_PROXIES configuration. These are approximate abuse controls, not atomic
delivery quotas. Target limits apply to unknown emails too; no plaintext address
is placed in cache keys. Generic reset status/body avoid account enumeration;
no claim of constant-time real provider delivery is made (none enabled here).

Frontend adds /forgot-password, /reset-password, /verify-email and authenticated
/email-verification. Login links to reset; Profile links to verification. Code is
lazy-loaded. Token links use fragments, not server-visible query/path credentials;
the component removes fragments from browser history and holds values only in
memory, clearing them on success. It supports React StrictMode without losing the
token. Refreshing the page after removal requires requesting a new link. It does
not store credentials in local/session storage. Requests render all field errors,
429 wait guidance, pending/disabled states and explicit success. No automatic
verification on page load or automatic retries of normal mutation failures.

## Actual verification

Python 3.12.6, pinned Django 6.1.2/PyJWT 2.15.1. pip check, Django system check and
makemigrations --check --dry-run passed. Full Django suite: 154 run in 88.184 seconds,
153 passed, one Windows symlink-privilege skip. Focused recovery plus existing CSRF
suite: 17 passed. No real email/production database used; capture only in memory.

Node 24.19: locked npm ci, lint, all 42 component tests (6 files) and build passed.
Focused recovery/client tests: 17 passed. First full frontend run exposed Profile's
test lacking router context for its new Link; corrected fixture, then lint/full
suite/build passed. No protection or assertion was removed. Linux CI/real-browser
end-to-end/production verification were not run. One committed build packaging is
the final package commit; no dependency/lockfile change.

Tests cover generic request responses, disabled and console no-send behavior,
validators/mismatch, reset expiry/tampering/email-change/replay, tracked blacklist,
untracked legacy rotation revocation, current fingerprint rejection, successful new
login, old access-token grace, signed verification expiry/purpose/address/reset
binding, idempotent confirmation, authorization/status, strict CSRF/stale JWT,
target throttle/reset, fragment cleanup under StrictMode, all frontend errors,
explicit verification click, missing links and truthful unavailable-email UI.

## Local review script (PowerShell)

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py test accounts.test_recovery accounts.test_csrf --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Tests generate synthetic credentials only internally; do not print mail/token
contents or point test settings to a live DB. On a separately prepared local app,
visit Forgot password and Email verification and confirm requests explicitly say no
email was sent. Missing/expired token forms must give recovery guidance. Automated
locmem tests exercise valid links without manual token handling or real sending.

## Future rollout and rollback — not performed

This branch includes unpublished schema/delivery prerequisites. After separate
push/review/CI/merge/deployment authorization, back up and verify DB/media, pause
writers, stage exact approved migration source and inspect migrate --plan. Expect
jobs/0008 and profiles/0003 then profiles/0004 if not already applied. Apply before
new model/auth code handles requests, then activate the paired frontend/server.
Never silently apply an unexpected migration. Keep host HTTPS and the currently
approved redirect=False/HSTS=0 until the separate scheme gate is resolved.

CRITICAL rollback: retain the new reset revocation guard and reset marker once
password reset has been used. Pre-package refresh code ignores that marker and
could accept old untracked tokens. Prefer a forward fix, or roll back UI/endpoints
while retaining patched refresh validation. A full old-auth rollback requires a
separately reviewed account/session invalidation plan. Do not reverse/drop the
marker, restore old DB over newer writes, or change signing credentials casually.
This supersedes older generic code-only rollback advice for the reset-bearing release.

## Remaining scope / stop

No real delivery activation, sender/domain configuration, secrets, CI/CORS/ingestion,
payments, registration styling, no-skills match prompt or alert-default changes.
No change to existing application send API or alert lifecycle. Account-email budget
integration and pilot recipients need the next separately authorized package.

References: [Django reset settings](https://docs.djangoproject.com/en/6.1/ref/settings/#password-reset-timeout),
[Django password recovery](https://docs.djangoproject.com/en/6.1/topics/auth/default/#django.contrib.auth.views.PasswordResetView),
[SimpleJWT blacklist](https://django-rest-framework-simplejwt.readthedocs.io/en/stable/blacklist_app.html).

All new commits must use Michael's configured noreply identity. Stop for review;
no push or deployment was performed.
