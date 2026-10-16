# Owner-only email pilot preparation

16 October 2026. Preparation only; no live sender activation, credentials, push or
deployment. Based on reviewed local account-email integration `92c739d` and
production reported at `e4eaefd`. Pin a separately reviewed release SHA later.

## Verified readiness and remaining gap

Brevo's UI reports michaelmathenge.dev authenticated and the Ajiri sender verified.
Zoho's admin UI shows the Ajiri alias attached to Michael's existing mailbox.
Website, primary mailbox and existing Zoho DNS were preserved. Receiving an actual
message at the alias has NOT been tested. Provider/domain setup does not activate
the application. No new credential exists from this preparation.

Source evidence:
- `jobs/brevo_transport.py`: isolated HTTPS adapter; redirects forbidden, bounded
  response/timeout, no automatic network retries, no credential loading.
- `jobs/delivery_service.py`: atomic ledger, daily partitions, disabled by default;
  application eligibility, verified address and recipient-purpose checks.
- `accounts/email_delivery.py`: ONLY explicit test capture plus the exact locmem
  backend enables the bridge. No production factory exists.
- `jobs/views.py` and `jobs/matching.py`: application/alert delivery still uses
  Django mail directly. Switching EMAIL_BACKEND to SMTP could bypass new controls.

Consequently this document is NOT an executable sending configuration. Do not
replace the test sink or enable SMTP to make the pilot work. Keep console email;
its existing output can contain private application/alert content. Do not publish
console logs. No application or alert real delivery is approved here.

## Proposed configuration contract — not implemented

Names below are proposed; adding them today has no activation effect. No secret
values or actual recipient addresses belong in this file or commits. Michael
enters configuration privately during a separately approved deployment.

| Proposed setting | Pilot policy |
|---|---|
| REAL_EMAIL_ENABLED | False by default; separate explicit activation |
| EMAIL_DELIVERY_MODE | owner_pilot only; reject unknown modes |
| EMAIL_PILOT_OWNER_ID | One approved active account, no wildcard |
| EMAIL_PILOT_RECIPIENT | One owner-controlled address, confirmed before activation |
| EMAIL_PLATFORM_FROM / EMAIL_PLATFORM_NAME | Verified domain alias / Ajiri |
| BREVO_API_KEY | Private runtime input; never printed, committed or supplied to Codex |
| BREVO_TIMEOUT_SECONDS | 10; validate range 1–60 |
| EMAIL_GLOBAL_DAILY_LIMIT | Existing approved ceiling 200 attempts |
| EMAIL_APPLICATION_DAILY_LIMIT | Existing allocation 150; channel disabled in first pilot |
| EMAIL_ACCOUNT_DAILY_LIMIT | Existing shared reset/verification allocation 30 |
| EMAIL_ALERT_DAILY_LIMIT | Existing allocation 20; channel disabled in pilot |
| EMAIL_PER_USER_APPLICATION_DAILY_LIMIT | Existing ceiling 10; channel disabled initially |
| EMAIL_PILOT_DAILY_LIMIT | Proposed additional 5 attempts total; approval needed |

EMAIL_BACKEND remains console and ACCOUNT_EMAIL_TEST_CAPTURE stays absent/false.
The new factory must reject incomplete or inconsistent activation configuration
visibly and must never fall back to SMTP/console for security links. Disabled mode
must retain today's truthful no-send behavior. No runtime CSRF-disable switch.

Allowlist checks must happen before token creation, budget reservation and network
I/O, and cover EVERY real transport caller. Require both owner account and exact
recipient; never rewrite a real user's or employer's recipient to Michael. Public
reset responses remain generic even when pilot-blocked. Validate normalized single
addresses; no suffix matching, aliases, CC/BCC, arbitrary Reply-To or recipients.
Recheck at the transport boundary. No credentials in exceptions or health output.

Use reviewed shared accounting across both account purposes; failure attempts
consume capacity. Implement the extra pilot cap atomically with existing reservation
accounting, without a migration or independent cache quota; stop for review if
schema changes are needed. Do not borrow category allocations. No automatic retry
after timeout/unknown/reserved outcome; retain receipt and investigate privately.
Never clear receipts to force a retry. Definite failures may be manually retried
with a new action ID and consume another slot. Keep digest derivation stable;
signing-key rotation and receipt expiry remain separate review items.

## Next implementation package and required tests

Separately authorize a production factory plus account-email pilot integration.
Keep real activation off and use mocked HTTP/locmem in all tests. No dependency,
DNS, CORS, ingestion or token lifetime change. Test disabled/incomplete configuration,
owner/recipient/channel rejection with no side effects, mixed-case canonicalization,
no recipient rewriting, 5-attempt concurrent cap, shared 30/200 accounting,
definite/ambiguous failures, idempotency, redaction and generic reset responses.
Run full existing backend/frontend gates and package frontend_build only if needed.

Start with account verification and password reset ONLY. Applications need a later
integration of lifecycle/status updates, Reply-To, attachments and the ledger;
alerts need confirmed consent, truthful sent state and bounce handling. A verified
Brevo domain is not approval for either channel. Do not run employer-facing pilot
applications against real jobs. Attachment-size policy remains unresolved; default
to disabled until explicitly approved and tested with synthetic documents.

## Michael's release checklist — future manual execution

Do not run this until the production factory is implemented, reviewed, all CI passes,
and Michael separately approves push, merge and deployment. This document grants none.

1. Confirm the owner account/recipient privately and approve the proposed 5-attempt
   pilot cap. Confirm Brevo sender is verified; receive a separately authorized
   harmless message at the Zoho alias before relying on replies. No send is performed
   during preparation. No live application or alert recipients.
2. Review the exact release SHA, diff, migration list and rollback. Do not deploy
   a moving main. Preserve the reset-revocation guard after any reset has occurred.
3. Pause ingestion and other writers for a fresh DB/media backup. Verify integrity,
   checksums and isolated restore, and download to the private encrypted backup
   location. Preserve the current virtualenv/configuration privately without exposing
   credentials. Check account disk quota, not the shared host filesystem capacity.
4. Stage the pinned reviewed code without reloading workers. In PythonAnywhere Bash,
   activate the existing virtualenv BEFORE strict shell flags (workon can fail under
   nounset). Example commands for the approved stage:

   ```bash
   cd /home/Mathenge/ajiri
   workon ajiri
   git status --short
   git rev-parse HEAD
   cd ajiri-backend
   python -m pip install --no-cache-dir --requirement requirements-prod.txt
   python -m pip check
   python manage.py check
   python manage.py makemigrations --check --dry-run
   python manage.py migrate --plan
   ```

   Stop on unexpected dirty files, dependency changes, errors or migrations. Expected
   unpublished prerequisites are jobs/0008 and profiles/0003/0004 if not yet applied;
   verify their exact filenames/content in the reviewed release. Then apply reviewed
   migrations with `python manage.py migrate` BEFORE code handles requests.
5. Privately create/enter a dedicated Brevo credential yourself, with the minimum
   permissions the provider offers. Codex must never receive, enter, print or save
   it. Use the existing approved private server configuration mechanism. Enter the
   reviewed non-secret pilot settings; leave activation false initially. Do not
   type credentials into shell commands/history or paste configuration here.
6. Activate paired reviewed frontend/server, reload and verify health, CSRF, login,
   profile, downloads, direct-media denial, shared throttle cache and private log
   permissions. Preserve redirect=False/HSTS=0 until the separate scheme gate passes;
   keep hosting Force HTTPS. Do not alter DNS or hosting during this release.
7. Only after explicit sending approval, enable owner-only mode and reload. Request
   one verification email, inspect inbox/spam privately and confirm the link. Request
   one password reset, change it privately, confirm replay fails and old refresh
   sessions fail; a fresh login must work. Never share links, cookies or passwords.
8. Verify non-owner requests cannot cause mail; use synthetic automated tests rather
   than real third-party addresses. Verify no automatic retry and one receipt per
   action. Inspect provider acceptance versus inbox delivery privately. A bounce or
   complaint stops the pilot; no automatic reconciliation or resend.
9. Resume ingestion and verify one normal run. Review sanitized errors and remaining
   quota. Record release SHA/results without private metadata. Stop for pilot review;
   do not widen recipients automatically.

## Rollback and stop conditions

Disable REAL_EMAIL_ENABLED and reload first; verify requests truthfully report
delivery unavailable and cannot contact the provider. Keep console mail unchanged.
Preserve ledger, verification state, reset marker and all newer database writes.
Never restore an old DB routinely or reverse proof/ledger migrations. A pre-reset
auth rollback is unsafe after resets: retain the patched refresh revocation guard
and prefer a forward fix. Review server/client rollback together. Restore a preserved
virtualenv only as part of the reviewed code/dependency rollback, not independently.

Stop on unexpected migrations, missing allowlist enforcement, non-owner mail,
ambiguous send, failed integrity check, unsafe log content, or invalid sender setup.
Operator reconciliation, bounce/complaint automation and legal metadata retention
remain open; a small supervised pilot does not resolve those wider-release gates.

## Preparation verification

Read-only inspection of the files above and the schema/delivery/accounts/integration
reviews. Browser-confirmed domain and sender/alias status was established in the
preceding setup. No live reachability, inbox delivery or production factory is
claimed. No application code, configuration values, migration, dependency, CI or
frontend build changed. Application suites are not rerun for this documentation-only
preparation; earlier package results remain historical, not new test claims.
