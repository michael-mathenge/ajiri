# P4 application-email authorization — design for review

20 October 2026. Based on reviewed P3 `9f08327`. **Proposal only:** no model,
migration, endpoint, transport integration, provider call or production change.
P3 review authorizes preparing this design; it does not approve this schema,
attachment policy, email activation, employer contact or a pilot message.

## Baseline and narrow first scope

P1-P3 provide private append-only packages, exact saved-document verification and
explicit document-only approval. The legacy application email route returns 409
before any status claim or send. External website confirmation is a user report.
DeliveryService already reserves shared budgets and tracks reserved, accepted,
definite_failure and unknown outcomes. Its current account pilot rejects application
channels; do not weaken that account-only policy to enable this proposal.

Recommend a primary-email-only P4 implementation, disabled by default and tested
with mocked transport. No copies, CC/BCC, certificate uploads, employer website
automation, job-alert delivery/consent, webhooks, background queue or scheduler.
P5 is a separately approved, supervised synthetic owner-only pilot. Broader delivery
requires its own suppression/event, privacy and operational reviews.

## User decisions and proposed wording

1. Review/approve an exact saved CV and letter using P3. This grants no sending right.
2. Request a private send-plan preview for that latest package. Show actual recipient,
   verified applicant Reply-To, platform From, attachment filenames/sizes, exact email
   subject/body, package revision, copies OFF, expiry and the one-application purpose.
3. With an unchecked box, explicitly authorize that plan. Suggested wording:
   “I authorize Ajiri to email this exact application and the two listed documents
   to the displayed recipient for this job. Copies are off. This permission covers
   this application only. I can withdraw it until sending starts; after that Ajiri
   may be unable to stop or recall it.” Wording is proposed, not a compliance claim.
4. Authorization creation records evidence only: no quota, provider I/O or automatic
   send. A separate **Send this authorized application** button requests dispatch.
5. Before the dispatch handoff, **Withdraw authorization** prevents that action.
   After handoff, show “Sending has started or may have started; cancellation cannot
   be guaranteed.” Never imply recall. Account-email consent and alert preferences
   remain independent; no global or future-job authorization is inferred.

Proposal: authorization expires **24 hours** after server authorization time.
Any expiry, withdrawal, superseding package, changed destination/job context,
verified mailbox, sender/configuration policy or file bytes requires a new reviewed
plan and authorization. No automatic renewal. Historical proof remains evidence.

## Immutable send plan

Server builds a strict, versioned JSON object, bounded to 64 KiB UTF-8:

- schema_version=1; application ID, owner ID, package UUID/revision/fingerprint and
  document-approval ID/fingerprint/policy version;
- one normalized recipient from the application's saved destination; verified
  current account Reply-To; configured verified platform From and fixed name Ajiri;
- exact saved email subject/body, with subject header controls rejected;
- exactly two descriptors: role, DOCX MIME, filename, byte size and SHA-256 for the
  saved CV and saved letter; no file paths, public URLs or document bytes;
- copy_to_self=false; send-policy and attachment-policy versions.

SHA-256 covers the canonical complete object, including identity/purpose bindings.
This is a fingerprint, not a credential or evidence of delivery. POST reconstructs
and validates the plan server-side; it never trusts client recipients, hashes,
filenames, policy versions or an uploaded payload. Normalize/compare addresses with
the existing validated strip/casefold policy; never remove plus tags/dots, expand
aliases, use suffix matches or rewrite an employer address to the pilot mailbox.
Reject unsupported addresses instead of silently changing them.

The plan stores necessary private addresses and email text, like existing package
snapshots. Owner-scoped no-store APIs only; no plan bodies, addresses, document
names, tokens or provider exceptions in logs/Jira/commits. Do not claim new at-rest
encryption. Retention/erasure must be resolved with AJ-25 before broader launch.

## Exact additive schema proposal

Both tables start empty. No backfill, existing-row edits, User fields, historical
status reinterpretation or changes to existing ledger constraints are proposed.

### ApplicationSendAuthorization

| Field | Type, null/default | Purpose |
|---|---|---|
| id | UUID PK, uuid4, non-null | Server action identity |
| request_key | UUID, unique, non-null, no default | Client-generated non-secret reconciliation key, required on explicit creation |
| application | FK Application, PROTECT, non-null | One application; service verifies owner and package relationship |
| owner | FK existing User, PROTECT, non-null | Acting owner; does not alter User |
| document_approval | FK ApplicationPackageApproval, PROTECT, non-null | Exact latest approved package, never legacy inference |
| plan | JSON, non-null, no default | Strict immutable send-plan schema above; service validates keys/bounds |
| plan_sha256 | Char(64), non-null, no default | Lowercase canonical plan fingerprint |
| policy_version | Char(40), non-null, no default | Proposed application-send-v1 wording/version |
| authorized_at | DateTime, non-null, no default | Explicit server-assigned time |
| expires_at | DateTime, non-null, no default | Same server time plus proposed 24 hours |
| state | Char(16), non-null, default authorized | authorized / withdrawn / superseded / expired / dispatch_started |
| closed_at | DateTime, nullable, default None | One-way lifecycle transition time; dispatch cutoff when dispatch_started |
| retry_of | FK DeliveryAttempt, PROTECT, nullable/default None | Explicit definite-failure retry reference, otherwise absent |

SQL constraints: valid state; expires_at > authorized_at; authorized implies
closed_at IS NULL, other states imply closed_at IS NOT NULL; at most one
state=authorized row per application. request_key is globally unique. Owner/package/
approval/plan correspondence is transactional service validation, not an SQL FK
guarantee. Immutable fields never have PATCH/delete APIs; state closes once only.
Expired authorized rows are closed in an explicit mutation transaction before a
replacement is created. GET derives effective expiry without writing anything.
Proposed constraint names: app_send_state_valid, app_send_closed_time,
app_send_expiry_valid and app_send_active_unique.

### ApplicationSendAttemptLink

| Field | Type, null/default | Purpose |
|---|---|---|
| id | BigAutoField PK | New association identity |
| authorization | OneToOne ApplicationSendAuthorization, PROTECT, non-null | At most one dispatched attempt per authorization |
| attempt | OneToOne DeliveryAttempt, PROTECT, non-null | Prevent one ledger attempt being attributed to several authorizations |
| previous_attempt | FK DeliveryAttempt, PROTECT, nullable/default None | Retry edge; must equal authorization.retry_of |
| created_at | DateTime auto_now_add, non-null | Server association time |

Conditional unique previous_attempt when non-null prevents two actual retries of
one failed attempt (app_send_retry_unique); app_send_retry_not_self rejects a link
whose previous_attempt equals its own attempt. Only application-channel attempts with matching application,
owner, recipient digest and idempotency key may be linked. Existing account and
alert attempts get no links and retain their existing semantics. Do not add copy
roles or relax delivery_app_unresolved; copies need a later reviewed parent/role
design. No current SQL constraints are removed.

### Migration, compatibility and reversal

Every proposed field is confined to a new empty table; existing rows need no
defaults or data conversion. Nullable fields start None, not inferred evidence.
PROTECT preserves evidence but blocks some account/application deletion paths;
that is a deliberate review item, not an implemented erasure policy. New links and
plans join private backups; no automatic pruning/deletion is added.

Migration proposal: CreateModel twice, add only the constraints described above;
review generated operations before implementation. Old P3 code ignores new tables
and already blocks legacy email. Old P2/P3 saves may not close stale authorizations,
so the new dispatch path must independently recheck latest revision and fingerprint.
Do not run older ungated senders concurrently. On rollback retain populated tables,
plans, attempts, documents and newer writes. Reversing these CreateModels destroys
evidence and is not a routine rollback; no old DB restore over newer writes.

## Proposed owner-only API contract

All endpoints require existing authenticated owner access, existing JSON/auth/CSRF
behavior and private,no-store responses, including errors. No auth/CORS changes.

| Action | Proposed behavior |
|---|---|
| GET /applications/{id}/send-plan/ | Validate latest package approval, saved bytes and eligibility; return exact server plan/hash, versions and disabled-mode explanation; no writes/I/O |
| POST /applications/{id}/send-authorizations/ | Required request_key, package UUID, expected revision/plan hash and explicit true; reconstruct/check under application lock; create evidence only |
| GET /applications/{id}/send-authorizations/?request_key=... | Owner lookup after uncertain creation; no auto-repeat POST, no token/credentials in query |
| GET /applications/{id}/send-authorizations/{uuid}/ | Plan, effective lifecycle and linked safe attempt state; reconcile lost replies |
| POST .../{uuid}/withdraw/ | Explicit owner withdrawal before dispatch cutoff, idempotent; never deletes evidence or sends mail |
| POST .../{uuid}/dispatch/ | Explicit send intent; same authorization always maps to same attempt; disabled in P4 mocked implementation |

Creation replay with the same request_key and identical owner/application/plan
returns the existing record (including expired/closed state); changed binding is
409, cross-owner is 404. A new key does not bypass one-active-authorization or
unresolved/accepted delivery blockers. No mutation auto-retry. A distinct explicit
retry after a definite failure gets a new plan/authorization/action and names the
prior attempt. Proposed bound: **one manual retry per application**, never after
unknown/reserved/accepted, never by deleting receipts; each actual attempt costs quota.
Look up an existing owned request key before reconstructing a fresh plan, so a
lost creation reply does not turn into a duplicate consent record after an edit.
Similarly, an already-linked dispatch returns its authoritative receipt without
new eligibility checks, quota or network I/O; GET can still show that receipt when
documents/mailbox later change. Only a genuinely new dispatch must pass every
current-eligibility and integrity check. Ownership/authentication always applies.

Latest document approval can be previewed when delivery is disabled, but dispatch
must return a truthful disabled response without claiming status or quota. The UI
must label any mocked/test-only authorization as unavailable for real sending.
No new consent is inferred from the old frontend checkbox or legacy sent markers.

## Reservation, dispatch and withdrawal ordering

1. Before any quota or network operation, freeze verified document bytes and exact
   MIME/base64 payload in memory. Reject changed/invalid/oversized files, recipients,
   unverified mailbox, unsupported policy, inactive/scam jobs or disallowed pilot.
2. Extend DeliveryService's application path to require authorization identity and
   fingerprint; direct application calls without them fail closed. Preserve account
   callers. Do not expose a second transport entry point that skips this boundary.
3. In the existing budget-reservation transaction, acquire the writer before reads,
   then recheck owner, authorization state/expiry/hash, latest document approval,
   current job/destination, verified Reply-To, suppression/pilot eligibility and
   exact frozen payload. Recheck immutable byte hashes against the current package.
   Existing idempotency lookup returns the existing linked attempt without I/O.
4. Atomically reserve existing shared/category/per-user/pilot capacity, create the
   application attempt and link, and close authorization as dispatch_started.
   Commit all or none. No transaction remains open over provider I/O.
5. That commit is the authoritative dispatch handoff/cancellation cutoff. Withdrawal
   taking the same application writer claim first wins and prevents dispatch;
   withdrawal after handoff cannot promise cancellation, even if the socket call
   has not begun. Show this limit before authorization. A concurrent new package
   either wins before handoff and blocks dispatch, or is blocked by the reserved
   attempt. Pre-existing active authorizations are superseded on new package saves
   in the same Application transaction after P4 integration.
6. Send the frozen one-recipient payload once through the allowlisted Brevo adapter.
   Persist the returned outcome using the reviewed database-only receipt retry;
   never repeat provider I/O after a receipt-write/read failure. Crash after handoff,
   timeout or lost acknowledgement retains reserved/unknown as a durable blocker.

There is no asynchronous queue or worker added. A future queue needs separate
lease/revocation design. Account/mailbox or filesystem changes after the handoff
cannot be atomic with an external network call; future sends recheck, and the
already-started action cannot be advertised as retractable.

Job/destination changes must never silently retarget an application. Minimal P4
**blocks dispatch** on mismatch with saved job context and the current source
listing. It does not add arbitrary-recipient editing or rewrite stored application
destinations. A separate explicit destination-refresh design is needed for changed
listings before those applications can resume; the synthetic pilot uses a stable,
genuinely owner-addressed listing. This is an intentional limited first scope.

## Truthful outcomes and retries

Keep Application.status history unchanged for email; derive new email display from
linked attempts. Do not mark legacy SENT/sent_email as provider acceptance. External
submission continues its existing user-confirmed sent marker, labelled separately.

| Evidence | Label and next action |
|---|---|
| Authorization only | Authorized, not sent; may withdraw before handoff |
| Dispatch claim with reserved receipt | Sending/outcome pending; lookup only |
| Provider acceptance | Accepted by email provider; inbox delivery not confirmed; no resend |
| Definite rejection | Could not send; one new explicitly authorized retry if eligible/capacity allows |
| Unknown/lost receipt/crash | Outcome unknown; blocked pending private operator reconciliation |
| Existing legacy sent flag | Historical application status; provider delivery unverified |

No automatic retry, no timeout-based quota refund and no auto-release of unresolved
attempts. Phase P4 provides no operator state-edit/reconciliation endpoint. Unknown
stays blocked; a reconciliation workflow and its audit schema require separate
review. Provider acceptance is never described as delivered/read/submitted to a
website. Future bounce/delivery callbacks cannot be fabricated from public JSON.

## Attachment and pilot proposals requiring approval

- Exactly the saved approved CV plus saved approved cover letter, DOCX only;
  **2 MiB each, 4 MiB raw aggregate**. Bounded integrity/content checks, no malware
  scanning claim. No certificates, URLs, provider fetches or on-send regeneration.
- ASCII-safe name/company components of 40 characters, Applicant/Company fallbacks,
  unsafe/control/separator removal; transport filename <=120 characters. Freeze
  filenames in the reviewed plan. Browser download labels keep existing Unicode
  rules and may differ; UI must show actual outgoing attachment names.
- Base64/MIME serialized request must fit a **currently verified Brevo limit** and
  a reviewed conservative runtime ceiling. No number is guessed here; missing or
  unverified ceiling means disabled. Provider limit/current terms are unverified
  in this design and must be checked before activation, not assumed from history.
- Proposed future settings: APPLICATION_EMAIL_ENABLED=False and
  APPLICATION_DELIVERY_MODE=disabled by default; only explicit owner_pilot mode is
  supported initially, together with existing global real-email gate. A separate
  validated owner ID/actual-recipient allowlist is required at service AND transport.
  Account-pilot settings do not implicitly grant application permission.
- Proposal: **one application attempt per Nairobi day** during P5, within the
  existing additional **five-total-message** shared pilot cap and fixed 200 total /
  150 application / 30 account / 20 alert / 10 per-user-application ceilings.
  Count all prior reservations, including failures/account messages; no borrowing
  or quota increase. A manual retry may therefore have to wait for another day.
- Copy_to_self stays false. No CC/BCC or applicant-copy action is implemented.
  Copies need separate role/ledger constraints and atomic multi-message reservation.
- P5 uses one explicitly allowlisted owner-controlled recipient and synthetic job,
  applicant and documents. Never rewrite a real employer destination. Subject/body
  visibly identify a test. No pilot call is authorized by approving this design.

Until authenticated suppression/events exist, any proposed P5 activation requires
manual provider review immediately before and after each supervised attempt and
an immediate stop on bounce/complaint. No automatic monitoring is claimed. Broad
application or alert launch remains blocked on secure event intake, suppression,
unsubscribe/consent and privacy review. Do not clear suppression on profile edits.
P4 cannot claim an automated suppression check that does not exist: real dispatch
stays off until P5 separately specifies and approves this supervised operating
procedure. A missing automated suppression integration never permits broad mode.

## Tests required before any activation

- Populated-schema upgrade creates only empty tables, preserves all existing rows,
  CV/package/file bytes, account-pilot receipts/preferences and migration history.
  Test constraints, code rollback with retained tables and PROTECT consequences.
- Plan ownership, current approval, latest revision, exact recipient/Reply-To/From,
  package/job/mailbox edits, expiry, text/filename bounds, malformed inputs and
  no paths/secrets in APIs/logs. Cross-owner/unknown 404, no-store errors/HEAD.
- Authorization create/lookup/replay, same-key changed plan rejection, duplicate
  active records, expired/withdrawn/superseded state and zero provider/quota effects.
- Withdrawal-versus-dispatch and save-versus-dispatch on real SQLite writers;
  one authorization maps to one attempt, duplicate dispatch keys never repeat I/O.
- Shared/global/category/per-user/pilot capacity across account/application calls,
  failure consumption and rollback of failed reservations. Primary-only constraints
  remain unchanged; copy/CC/BCC/off-allowlist paths have zero side effects.
- Exact saved byte attachments, missing/corrupt DOCX, expansion/base64/request limits,
  no regeneration, prepared payload consistency across the transaction and redaction.
- Provider accepted/definite/unknown/malformed outcomes, crash checkpoints and
  post-I/O receipt-lock failure; never resend on reconciliation GET or lost reply.
  Explicit retry has a new consent/action and at most one linear failed-attempt edge.
- Client separates document approval, authorization and dispatch; all boxes start
  off; edits invalidate reviewed plan; requests are single-flight, no mutation retry;
  provider acceptance is not styled as inbox delivery; external confirmation unchanged.

Run complete existing backend/frontend gates and regenerate frontend_build only
for the future frontend implementation's final commit. Use mocked HTTP/locmem;
inbox/pilot tests require separate send approval. No new dependencies, auth/CORS,
token lifetime, ingestion, CI, SMTP or DNS changes are part of this proposal.

## Review, rollout and rollback

Approve exact schema/lifecycle, wording/expiry, primary-only attachment limits,
retry bounds and pilot ceilings separately from activation. Recommend implementation
in three reviewable packages: P4a additive schema/tests; P4b authorization/withdrawal
and mocked shared-service integration; P4c client/send-plan flow and full gates.
Keep all real application transport disabled throughout these packages. Stop after
each package; do not infer P5 approval from a successful mock or merged code.

Before P5: privacy/legal review of employer contact use, applicant representation,
attachment disclosure, Reply-To/copies, provider processing/transfers, retention,
erasure/backups and support access; verified current provider size limits, sender,
owner mailbox and manual bounce/complaint stop process; pinned CI-green release,
fresh consistent backup, reviewed expected migrations before activation and paired
server/client verification. These are review needs, not legal advice or compliance
claims. No domain, recipient, credential, schedule or account policy is changed now.

Rollback first disables application dispatch, then reverts only to a reviewed
version that retains the email-disabled boundary (P3 or forward safety fix). Keep
account security delivery, authorizations, attempts/links, files, newer writes and
all reserved/unknown blockers. Do not reverse populated evidence tables, delete
receipts to force retry or restore an old database routinely. No SMTP/console bypass.
