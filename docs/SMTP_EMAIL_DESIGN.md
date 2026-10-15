# SMTP and transactional email design — WP11

Proposal only, 15 October 2026. No provider selected or account configured.
Michael performs every server/provider/DNS operation. Codex never touches production
or requests, receives or writes credentials. Names below are configuration names,
not secret values. Privacy/provider processing sections are DRAFT for legal review;
Codex is not a lawyer. See [Checkpoint 3 decisions](CHECKPOINT3_PLAN.md#decisions-michael-must-answer-before-building).

## Current behaviour and acceptance boundary

`config/settings.py` reads EMAIL_BACKEND and existing SMTP fields from environment;
it defaults to Django console. Production therefore reports application sends as
successful without delivering real email. Console output can include message bodies
and attachment content; treat logs as sensitive and restrict access.

`jobs/views.py` atomically claims ready_for_review as sent before sending saved CV
and letter attachments. Definite delivery/attachment failure returns 502 and releases
that claim to ready_for_review with no sent_at, retaining documents for retry. Preserve
400 for already claimed/invalid state, owner checks and external-link confirmation.

`jobs/matching.py` currently uses fail_silently=True, then sets sent_email=True without
checking accepted count. Existing notification uniqueness also prevents a fresh retry
on the next sweep. Correct this prospectively: accepted means provider/backend accepted
one message, not inbox delivery. Never relabel old records as delivered or resend them
in bulk. Keep in-app alerts independent and ingestion successful on mail failure.

## Provider options and verification

Sources checked during planning on 15 October 2026, not through production probes.
Prices/limits and account policies must be rechecked by Michael before activation.

| Option | Free-tier evidence / feasibility | Trade-off |
|---|---|---|
| Gmail SMTP with app password | Google documents app passwords for eligible two-step-verification accounts. PythonAnywhere's official help search result describes a Gmail exception, but canonical SMTP help could not be fetched; current account connectivity is NOT fully verified | Uses Django built-in SMTP, no dependency; account-specific limits, abuse restrictions and shared consumer identity make it a small-pilot option |
| Brevo HTTPS transactional API (recommended) | api.brevo.com is on the current US PythonAnywhere allowlist; Brevo documents a free 300 sends/day plan and attachment/Reply-To support | Requires a provider transport adapter or approved dependency, account/sender approval and privacy review; allowlisting is not an end-to-end connectivity test |
| Brevo SMTP relay | SMTP exists, and relay hostname appears on the allowlist, but an HTTP(S) proxy allowlist does NOT prove outbound SMTP-port access | Do not choose this path on the free tier without explicit current platform confirmation |

References:
- [PythonAnywhere free accounts](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/)
- [Current US allowlist](https://www.pythonanywhere.com/whitelist/)
- [Canonical SMTP help — retrieval failed](https://help.pythonanywhere.com/pages/SMTPForFreeUsers/)
- [Official help development mirror — indexed historical guidance, not current proof](https://helpdev.pythonanywhere.com/pages/SMTPForFreeUsers)
- [Google app-password requirements](https://support.google.com/accounts/answer/185833)
- [Brevo free-plan limits](https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan)
- [Brevo transactional API](https://developers.brevo.com/reference/send-transac-email)

Recommendation: Brevo over HTTPS, conditional on Michael approving API delivery instead
of literal SMTP. Keep Django's EmailMessage interface and supply a small backend adapter
using Python's standard library (including environment proxy support), with all transport
calls mocked in tests. No dependency is approved by this proposal. If an SDK/Anymail would
be safer or materially simpler, explain its benefit and stop for dependency approval.
Send attachments as encoded bytes, never as public CV URLs. Provider limits, payload
sizes and processing terms must be checked against saved document sizes before selection.
Do not disable TLS verification or bypass PythonAnywhere network restrictions.

## Sender and user trust

Recommend a verified platform From address, branded as Ajiri, with request.user.email
as Reply-To on applications. Employer sees the platform sender and can reply to the
applicant. Clearly explain the relationship in the review UI; never suggest the
message originates from the user's mailbox. Alerts use the platform sender and a
platform-controlled reply/support address, not the recipient as Reply-To.

Alternatives: arbitrary applicant From risks SPF/DKIM/DMARC mismatch and spoofing;
per-user OAuth/mailbox delegation adds credentials, permissions and complexity outside
this checkpoint; mailto/manual external sending reduces automation and cannot confirm
delivery. Recommend neither arbitrary From nor per-user credentials for this release.
Michael verifies the sender/domain and provider-required DNS authentication, including
DKIM/SPF and DMARC alignment. Gmail may rewrite unauthorized From identities. Do not
claim domain control or promise deliverability before sender verification.

## Configuration contract (names only)

Existing: EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER,
EMAIL_HOST_PASSWORD, EMAIL_USE_TLS, DEFAULT_FROM_EMAIL.

Proposed: EMAIL_TIMEOUT, EMAIL_USE_SSL (only if required by selected SMTP transport),
BREVO_API_KEY, EMAIL_PLATFORM_REPLY_TO, EMAIL_PLATFORM_DAILY_LIMIT,
EMAIL_USER_DAILY_LIMIT, EMAIL_APPLICATION_DAILY_RESERVE,
EMAIL_USER_HOURLY_LIMIT, EMAIL_ALERT_MAX_ATTEMPTS, EMAIL_ALERT_RETRY_DELAY_SECONDS,
EMAIL_DELIVERY_ENABLED (operator control to stop email actions during outage/rollback).
Exact defaults/limits require Michael's decision; credentials have no committed defaults.
Only selected-provider variables are required. TLS and SSL modes are mutually exclusive.

Read configuration from environment; the existing private server loader may load the
private environment file that Michael maintains. No credentials in Django DB, frontend,
source, sample commands, screenshots, chat or commits. Codex lists names only. Missing
configuration for an explicitly selected real backend must produce a sanitized startup
check error. Do not silently downgrade production SMTP/API failures to console.
Local default remains console; tests override to Django in-memory backend and do not
inherit production delivery credentials. Timeout is finite and must fit the worker budget.

## Failure handling, retries and limits

- Require accepted count of one for application success; zero is failure too. Preserve
  502/reviewable retry for definite failure and unchanged external-link behaviour.
  No transaction is held over network delivery; preserve the conditional claim.
- A provider can accept then lose its acknowledgement. Do not automatically retry an
  ambiguous attempt. Record a sanitized uncertain outcome for manual reconciliation;
  no new application status value is proposed. If a stronger state machine is needed,
  stop for separate approval. Sent in the current UI is not proof of inbox delivery.
- Alerts record sent_email only on confirmed acceptance; definite failures retain
  independent in-app visibility. Add attempt/budget records so a bounded retry can
  happen through the existing matching service invocation, without rewriting ingestion
  endpoints, changing workflow schedules or creating a daemon/Celery dependency.
  Any ingestion-flow change beyond that boundary requires explicit approval.
- Recommend additive SQLite-backed delivery reservations shared by both channels and
  workers, not per-process caches or DRF's approximate throttle as a hard global cap.
  Atomically reserve platform/user budgets before delivery and release only definitely
  unaccepted attempts. Keep uncertain reservations consumed for safety; no automatic
  crash reset. Do not hold SQLite locks across network calls.
- Define daily windows in Africa/Nairobi and a user rolling-hour control; provider
  windows may differ, so use conservative application caps beneath provider quotas.
  Count accepted plus unresolved reservations. Reserve a configurable portion for
  applications so alert fan-out cannot consume everything. Exact caps are decision 3.
- Local quota rejection proposes 429 with a safe retry hint and no state change; it
  is separate from provider failure (502). Provider quota rejection must not be
  mistaken for successful delivery. Alerts over quota stay pending only until bounded
  attempts/expiry, never unlimited catch-up bursts. Exact expiry belongs in approval.

Migration proposal: new delivery-attempt and budget tables with constraints supporting
atomic reservations; no destructive data migration, AUTH_USER_MODEL change or historical
consent/delivery backfill. Present exact schema and mixed-version deployment behaviour
before coding. All writers must be paused for cutover because old code bypasses quotas.

## Test plan — no live email in tests or CI

Use Django's in-memory backend for end-to-end message composition and current concurrency
suite. Assert platform From, applicant Reply-To, recipients, saved attachment bytes,
preferences and no duplicate sends. Mock transport for rejected auth, zero accepted,
timeouts, provider quota response and ambiguous acknowledgement. Assert 502 resets only
the winning claim, 400 remains for invalid sends, and retry after definite failure works.

Exercise atomic caps with overlapping reservations, day rollover, hourly limits,
application reserve and alert fan-out. Check alert failure never creates false success
or breaks ingestion, bounded retry does not duplicate confirmed acceptance, and in-app
visibility stays independent. Assert errors/logs contain no credential, address, payload
or attachment content. Future implementation runs all AGENTS quality gates; this planning
round does not claim those tests have been run.

## Manual activation instructions — Michael only, after separate approval

These are instructions, not actions taken by Codex. Existing deployment checklist remains
required; no production operation is authorized by approving a design document alone.

1. Select the approved provider, review processing/retention and verify the platform
   sender/domain in its dashboard. For Gmail, enable two-step verification and confirm
   app-password eligibility; create credentials privately. Never paste them into chat.
   For Brevo, verify transactional sending approval and attachment limits. Confirm current
   PythonAnywhere restrictions with platform documentation/support if SMTP is chosen.
2. Choose a quiet window; record old revision and backend privately. Pause all writers,
   ingestion/sweep callers and sending. Back up SQLite with its backup API and verify
   integrity, plus private media and private server configuration, following
   [deployment checklist](DEPLOYMENT_CHECKLIST.md). Stop if restore rehearsal fails.
3. Stage the reviewed revision containing migration tools without activating new code.
   Review check/migrate plan in the Python 3.12 environment. Stop on unexpected/destructive
   operations; apply approved additive migrations before web reload:

   ```bash
   cd /home/Mathenge/ajiri/ajiri-backend
   workon ajiri
   python manage.py check
   python manage.py migrate --plan
   python manage.py migrate --noinput
   ```

   Expected: no system-check errors and only approved migrations applied. The exact
   approved revision and schema will be documented when implementation is reviewed.
4. In the private server configuration editor, enter only the selected backend's
   variables yourself. Keep environment file permissions owner-only. Do not put secret
   values in shell command history, public files or Git. Confirm required names are
   present through sanitized checks, never printing the environment. For HTTPS delivery,
   retain the platform proxy; for SMTP use the provider's documented TLS mode/port.
5. Activate/reload reviewed code only after migration and configuration checks pass.
   Leave private media mappings unchanged; no public download URLs are needed. Keep
   writers paused until health, login and owner download checks pass.
6. Send a synthetic application only to an inbox you control, then a synthetic alert.
   Confirm actual arrival, From/Reply-To, correct saved attachments and provider receipt.
   Never send a deployment test to a real employer. Exercise failure/double-send paths
   in local captured-mail tests, not by corrupting production credentials.
7. Inspect sanitized server/provider events privately, caps and acceptance counts.
   Resume callers only after checks pass; verify one ingestion/sweep run stays healthy.
   Recheck renewal/quota and provider rejection/bounce evidence in the manual routine.

## Rollback and risks

On failed validation, keep writers paused. Michael restores the prior backend selection
privately and reloads the reviewed compatible revision. If returning to console, **real
email stops**, and console output can contain sensitive content. Pause email application
sending and alert dispatch until the failure is resolved; do not tell users console
success means delivery. If no existing way safely disables these actions, keep traffic
paused rather than silently accepting sends. Designing an operator delivery-disable
control is a prerequisite of WP11 implementation, not a change made in this document.

Keep additive tables in place; do not reverse migrations or restore an older DB over
new writes. Preserve delivery-attempt evidence and reconcile accepted/uncertain sends
before any retry. Never bulk reset sent applications. A compromised credential is
revoked/rotated by Michael through the provider, never shared with Codex. Rollback
cannot recall mail already accepted or copies held by employers/providers.
