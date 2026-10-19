# Application and alert sending design

19 October 2026. D3 proposal only. No sender integration, email, provider request,
webhook, endpoint, consent model or migration is implemented by this document.
No expansion of the existing account-email pilot is authorized.

## Current gap and future delivery boundary

Applications currently claim SENT before calling Django EmailMessage; alert code
uses Django mail and then sets sent_email. The console backend can succeed without
inbox delivery. Those paths are not yet integrated with DeliveryService, which
already has Brevo transport, budget reservation, purpose checks and attempt states
reserved/accepted/definite_failure/unknown. Historical sent markers cannot prove
provider acceptance. Preserve them as historical records; do not backfill receipts
or reinterpret old rows as delivered.

Recommend one shared delivery boundary for all future application/alert callers,
including scheduled work. Keep preparation/review entirely free of send effects.
Require active owner, verified current mailbox, explicit reviewed application send
or current alert consent, unsuppressed recipient, valid immutable content and
approved pilot/attachment policy before reservation. No fallback to SMTP/console
when this boundary is disabled or misconfigured. Existing console paths must be
unreachable for real delivery before activation; Phase C changes neither path.
External-link applications retain user-confirmed submission and do not call Brevo.

Future application send interface keeps the owner-scoped send route, adds an
explicit copy_to_self choice and reviewed draft/content fingerprint, and returns
attempt ID plus delivery_state; client must not infer success from HTTP alone.
Persist accepted content/action identity before network I/O, freeze the approved
CV bytes, letter/email and recipient, and reconcile the same action ID after a
lost response. Reject stale reviewed content with 409 rather than sending changes
that were not reviewed. No mutation auto-retry. Proposed interface only.

## Recipients, Reply-To and applicant copy

Use verified platform From with display name Ajiri; applicant's verified current
address is Reply-To, never an arbitrary client header or From spoof. Validate one
normalized address, reject CR/LF, disallow CC/BCC and record recipient binding in
the delivery plan. Job recipient changes after draft creation do not silently
change an application's snapshotted destination; require explicit reviewed update.

Offer an optional copy to the verified applicant, OFF by default and explicitly
shown during send review. A copy is a separate one-recipient transport operation
and ledger attempt, with parent action and recipient_role=applicant_copy; it does
not prove the employer received anything. Each network attempt consumes global,
application-category and per-user message capacity, including definite failures.
The existing 200/150/30/20 partitions and per-user application ceiling are not
increased or borrowed. If copy is requested, reserve capacity for both messages
atomically before either network operation; reject before sending if unavailable.
Persist the copy sub-action so a later copy failure cannot resend the employer
message. Do not send a success-styled applicant copy after a definite/unknown
primary outcome. Unknown primary leaves the copy held for reconciliation. First
pilot leaves copies OFF to avoid duplicate messages to the same owner mailbox.

Current service recipient-purpose checks and unresolved-per-application constraint
cannot simply be reused for a second recipient. A reviewed recipient-role/schema
extension is required; never bypass the existing checks with a recipient override.

## Attachment policy awaiting approval

Default remains DISABLED: enabling real application delivery with required CV/letter
attachments must fail closed until Michael approves the policy. Proposed later
policy: exactly the saved approved CV and saved reviewed cover letter, DOCX only,
maximum 2 MiB each and 4 MiB raw aggregate, bounded reads plus MIME/base64 payload
preflight against a separately verified provider request limit. Reject empty,
missing, corrupt, wrong-content or oversized snapshots before claiming quota.
Validate DOCX package parts/bounds without modifying signed-off bytes. No uploaded
certificates, public URLs, provider fetch URLs or on-send regeneration.

Current transport allows ASCII attachment names up to 120 characters. Proposed
email attachment labels preserve company-last naming but use ASCII-safe 40-character
name/company components and Applicant/Company fallbacks to stay within that guard.
Browser download labels remain Unicode and 60-character components. Do not weaken
the transport guard silently or claim content validation is malware scanning.
The applicant copy, if later enabled, includes the same approved attachment set
only after explicit review. Provider limits, privacy terms and quota are rechecked
before activation; no historical provider limit is assumed current.

## Truthful states and failure handling

| Evidence | User-facing state | Retry behavior |
|---|---|---|
| Validated and reserved, network not resolved | Preparing / sending, not sent | Same action lookup only |
| Provider returned validated acceptance receipt | Accepted by email provider, delivery not confirmed | Never resend same action |
| Definitive rejection before acceptance | Could not send, review failure | Explicit new action only, consumes new capacity |
| Timeout, lost acknowledgement, crash or failed receipt write after I/O | Outcome unknown, reconciliation required | No automatic or fresh-action retry while unresolved |
| Correlated authenticated delivery event | Delivered to recipient server | Not proof of reading or human receipt |
| Correlated bounce/complaint | Bounced / complaint, delivery stopped | Suppress and investigate, never auto-resend |

Derive application/alert displays from authoritative attempts and outcome events;
do not set SENT/sent_email before acceptance. Keep submitted externally distinct.
Legacy sent_email needs a historical/unknown label unless genuine evidence exists.
An unknown/reserved attempt is an active blocker, including across process restarts
and duplicate action IDs. A definite failure consumes its reserved budget. Expired
reservation reconciliation is operator-reviewed, not a timer that blindly releases
or retries. Manual provider reconciliation must preserve evidence and record who
resolved which attempt and why, without sensitive free-text logs.

## Alerts, unsubscribe and abuse signals

Use D1's preference + current explicit consent + mailbox binding + suppression
checks immediately before send. In-app notification creation is independent from
email delivery. No historical catch-up blast; an old notification/sent flag is not
authorization to mail. New eligible alerts each have a stable action ID; scheduler
replay cannot duplicate provider I/O. Unsubscribe stops unsent alert work and stays
separate from account security email. Do not implement these changes in ingestion
endpoints; all proposed caller changes require separate scope approval.

Design authenticated provider event intake with verified signature/mechanism,
bounded request body, replay/event-ID protection and strict receipt correlation.
Do not trust a public JSON claim of delivery or accept arbitrary status mutations.
Store minimal provider event type, opaque event ID, attempt link and server time;
exclude bodies, private documents and raw request headers. Append events and apply
monotonic state rules so a late delivered event cannot erase a complaint/bounce.
Hard bounce and complaint suppress further affected recipient delivery across
appropriate channels; soft bounce is held for operator review, with no blind retry.
Define account-security alternatives under separate review if suppression blocks
reset/verification. Never clear suppression automatically on a profile save.
Until secure callbacks exist, use a small supervised owner-only pilot with manual
provider review and stop on any bounce/complaint; do not claim automated monitoring.

## First pilot and release gates

Use synthetic applications whose stored application_email is already an exact
allowlisted owner-controlled address. Never redirect or rewrite a real employer's
recipient to the owner, and never contact a real employer during the pilot.
Allowlist both account and actual target at service AND transport boundaries.
Keep account-email pilot permissions separate. Subject/body clearly identify a
test. Default copies OFF and attachments disabled until separately approved.
Require reviewed synthetic mailbox evidence, sender/Reply-To, budget/receipt counts,
attachment hashes after approval, failure/unknown handling and no off-allowlist I/O.

Future activation requires exact migration/schema and privacy approvals, complete
mocked tests, explicit pilot-send approval, pinned CI-green release, verified backup,
approved migrations before code activation, and small fail-closed feature gates.
No current approval to enable application or alert transport is inferred here.

## Proposed migrations only

- AlertConsentEvent and reviewed email-default AlterField from D1; existing rows preserved.
- DeliveryAttempt recipient_role/parent action or a DeliveryAction parent table, with
  idempotency and unresolved uniqueness scoped per application/notification AND role.
- Immutable reviewed send-plan fingerprint/copy selection and document hashes linked
  to application action; no raw tokens, no new AUTH_USER_MODEL fields.
- Minimal DeliveryOutcomeEvent (unique provider event ID, attempt, type, timestamp)
  and recipient suppression evidence keyed to a normalized-address digest.
- Additive current delivery-state metadata if needed for efficient display; historical
  application/notification sent values remain unchanged, with no inferred backfill.

Exact fields, constraints, defaults, mixed-version behavior and retention must be
handed back for migration review before implementation. Old code must not send
while new evidence/role constraints are partially deployed. No migration files now.

## Tests, rollback and privacy review

Mock Brevo and assert owner/recipient/channel rejection has zero side effects;
preparation never sends; verified Reply-To; explicit copy decision; per-message
and aggregate caps; concurrent primary/copy reservations; stable idempotency;
partial copy failure never resends primary; snapshot/hash integrity; invalid DOCX,
oversize/base64 expansion, secret-free logs, duplicate/signed/invalid webhook events,
out-of-order events, hard/soft bounce, complaint, unsubscribe/queue races and policy
or email changes. Test provider acceptance versus inbox-delivery labels and legacy
unknown history. Actual inbox testing is a separately authorized owner-only step.

Rollback disables application/alert delivery before reverting paired code/client.
Keep account security service, reset revocation, ledger, consent/suppression/events,
files and newer writes. Never resume an old console/SMTP bypass, reverse populated
evidence migrations or routinely restore an old DB over new writes. Prefer a
forward fix for ambiguous outcomes.

Legal/privacy review must settle employer contact sourcing/use, applicant-authorized
representation and Reply-To, consent wording/evidence/withdrawal, provider processing
and transfer terms, attachment/copy disclosure, bounce/complaint suppression,
retention/erasure/backups and incident/support access. These are review questions,
not a claim of legal compliance or an instruction to collect more personal data.
