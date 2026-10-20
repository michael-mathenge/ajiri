# Application package roadmap and schema handback

> P4a update, 20 October 2026: the P4 design was reviewed and approved for schema
> implementation. New authorization/link tables and migration tests are local for
> review; see APPLICATION_SEND_SCHEMA_REVIEW.md. No service/API/dispatch activation,
> push or deployment is included. Later P4b/P4c/P5 work remains gated.

> P4 design update, 20 October 2026: Michael reviewed P3 `9f08327` and instructed
> proceeding to P4's separate authorization design review. The design-only proposal
> is APPLICATION_SEND_AUTHORIZATION_DESIGN.md; defaults/schema/attachment policy
> await review. No sending implementation, pilot, push or deployment is authorized.

> P3 approval update, 20 October 2026: Michael reviewed P2 through `ae8d05f` and
> instructed proceeding with saved-package review, downloads and document approval.
> P3 is local and awaits its own review. P4-P5 delivery authorization, sending and
> pilot remain separately gated. See APPLICATION_PACKAGE_APPROVAL_REVIEW.md.

> P2 approval update, 20 October 2026: Michael reviewed and approved P1 commit
> `e1e8f94`. P2 editing is now implemented locally for its own review. P3 approval
> controls and P4-P5 sending/pilot remain later work. See
> APPLICATION_PACKAGE_EDITOR_REVIEW.md; no push or deployment is authorized.

> P1 approval update, 19 October 2026: Michael reviewed this schema and instructed
> implementation of the additive migration package with tests, followed by a stop
> for review. P2-P5, real sending, pushes and deployment are not authorized by that
> instruction. Historical proposal wording below is retained; see
> APPLICATION_PACKAGE_SCHEMA_REVIEW.md for the actual P1 implementation and limits.

19 October 2026. Proposal for Michael's review following successful owner review
of CV and cover-letter downloads. Branch `codex/application-package-design` starts
from the reviewed local concurrency repair `09b76a1`; recorded production remains
`894d1eb`. This document introduces no models, migrations, runtime behavior or
provider calls. It extends APPLICATION_ALERT_SENDING_DESIGN.md, not its approval.

## Verified starting point

Job Detail already selects a private owner-approved CV for initial preparation.
Application preparation copies its exact bytes into a private application snapshot
and produces a job-specific letter. Existing applications return their original
snapshots rather than replacing them. My applications currently exposes downloads
and the email/external-site action, not editable document selection. The current
Application schema has no persisted selected approval provenance, package revision
or immutable approval/authorization record. A checked frontend box is insufficient
to bind future sending to exact documents.

The delivery concurrency repair is committed locally, tested and reviewed, but is
not yet pushed or deployed. Include it in a later separately authorized release;
do not silently call it production behavior.

## Sequence and review boundaries

| Package | Result | Suggested points | Gate |
|---|---|---:|---|
| P1 | Reviewed additive package/revision/approval schema and migration tests | 3 | Approve the schema below before implementation; stop after migration package |
| P2 | My applications CV selection, job context, letter draft editor and revision selection | 5 | Local implementation after P1 review; no sending |
| P3 | Exact package preview, private downloads and explicit document approval | 5 | Review invariants and tests before release |
| P4 | Per-application email authorization, shared-ledger integration and truthful outcomes | 5 | Separate sending, privacy and exact migration review; disabled by default |
| P5 | Supervised synthetic owner-only pilot | 3 | Separate pinned release/deployment and explicit pilot-send approval |

Certificates, alert defaults, alert consent and broader alert/employer delivery
remain separate. No website-submission automation is in P1-P5. No new dependencies,
auth/CORS/ingestion/hosting/CI changes or real emails are included in P1-P3.

## User journey for P2-P3

Within each editable draft or ready-for-review application:

1. Show the snapshotted job title/company, job-description context and application
   method. Describe job text as source material, not instructions to execute.
2. Show the currently saved package, including a legacy snapshot label where no
   approval provenance exists. Do not infer an approval from an old document.
3. Choose an owner-approved CV revision, with download/preview and a builder link.
   No automatic best-match selection or replacement of an existing application.
4. Choose a saved cover-letter revision for this job, or draft/edit one using the
   selected CV and the displayed job description. Initial drafting reuses the
   existing deterministic generator; no AI service, invented qualifications or
   automated claims of suitability. Preview highlights missing information.
5. Save a new package revision explicitly. File selection/typing alone does not
   mutate the saved application. Warn before leaving unsaved edits.
6. Preview/download the exact CV and letter, then explicitly approve that package.
   Approval is document approval only; it does not authorize sending.
7. For external listings, download and open the employer website. Keep the current
   user-confirmed external-submission flow and truthful explanation.
8. For email, P1-P3 show that managed sending is awaiting activation; do not call
   the legacy console sender or present document approval as a successful send.

Choosing an older letter creates a fresh package revision with the current selected
CV and displayed job context; it never rewrites the older revision. The first scope
is letters belonging to this application's job, not a global uploaded-letter
library. Reuse across jobs, uploaded CV/letter libraries and AI tailoring require
separate format/provenance/privacy decisions. Sent, dismissed or unresolved-delivery
applications cannot be redrafted through these controls.

## Proposed P1 additive schema — not implemented or approved

Retain Application and its existing files/status/history. Do not alter User or
backfill historical review/consent. Proposed new tables:

| Model / field | Type, null/default | Purpose and existing-row impact |
|---|---|---|
| ApplicationPackage.id | UUID PK, uuid4, non-null | New package identity only |
| .application | Application FK CASCADE, non-null | Ownership follows existing application |
| .revision | PositiveInteger, non-null, no default | Server-assigned positive revision; unique per application |
| .cv_approval | CVApproval FK PROTECT, non-null | Exact owner-approved source; cross-owner rejected by service |
| .job_snapshot | JSON, non-null, no default | Allowlisted title/company/description/method/recipient/source context shown at review; bounded text, never fetched URLs |
| .letter_text | Text, non-null, no default | User-reviewed content used to render the saved letter |
| .email_subject / .email_body | Char(255) / Text, non-null, default empty string | Saved email preview; empty permitted for external applications |
| .cv_document / .letter_document | Private FileField max_length=100, non-null, no default | Fresh UUID storage; exact CV bytes and rendered letter; no public mapping |
| .cv_sha256 / .letter_sha256 / .content_sha256 | Char(64), non-null, no default | Byte hashes and canonical package fingerprint |
| .cv_size / .letter_size | PositiveInteger, non-null, no default | Bounded snapshot reads; positive constraints; proposed 2 MiB each, 4 MiB aggregate for future email compatibility, awaiting attachment approval |
| .template_version | Char(40), non-null, no default | Explicit letter renderer provenance; no rerender at download/send |
| .created_at | DateTime auto_now_add, non-null | New snapshot creation time |
| ApplicationPackageApproval.package | OneToOne ApplicationPackage CASCADE, non-null | At most one immutable approval per package |
| .approved_by | Existing User FK PROTECT, non-null | Must equal application owner; no User schema change |
| .approved_at | DateTime auto_now_add, non-null | Server-recorded document approval time |
| .content_sha256 | Char(64), non-null, no default | Must match server-verified saved package at approval |
| .policy_version | Char(40), non-null, no default | Exact document-approval wording version, not email consent |

Constraints: unique (application, revision), revision >= 1 and positive document
sizes. Owner identity and hash/file checks require transactional service validation;
ordinary SQL foreign keys cannot enforce cross-table ownership equality. Package
rows/approval rows are immutable in application APIs. No update/delete endpoint is
proposed for approved snapshots. Retention/account deletion must preserve current
policy boundaries; these new private files join existing backups, without claiming
that backups are immediately erased. Review PROTECT relationships against the
future account-erasure policy before implementation.

Avoid adding a mutable current-package pointer in P1. Define current as the highest
revision; clients supply expected latest revision (0 for none). A transaction first
performs a conditional write on the existing Application row to serialize SQLite
writers, rechecks editable state/latest revision and delivery blockers, then creates
the next immutable package. Unique revision arbitrates competing requests. Approval
must name the current revision and fingerprint; stale changes get 409. Older
approvals remain historical but never authorize a newer package. Do not rely on
SQLite select_for_update alone.

Initial historical applications acquire no new rows automatically. Their existing
documents remain downloadable and visibly legacy/unapproved in the new flow.
Explicit selection and save create the first new package. Missing/corrupt files
fail closed with safe errors; downloads never regenerate them. Stage new files
under request-owned UUIDs; transaction failure cleans only that request's new files.
Crash orphan reconciliation is report-only, not automatic deletion.

All new columns exist only in new tables: no existing-row defaults or data rewrite.
Old code ignores the tables, but it also ignores approvals. P2-P3 must gate the
legacy email action before exposing new package controls. Do not permit a mixed
old/new fleet to send; this requires a reviewed paired client/server rollout.
Rollback retains populated tables, approvals, newer writes and files; reverting
code is preferred to reversing a populated migration. Any proposed reverse migration
must warn about data loss and is not routine operational rollback.

## API contract to review in P2

- Owner-scoped GET packages lists safe revision/approval/hash metadata, not storage
  paths; supports bounded pagination. Cover-letter text is private/no-store.
- POST packages takes selected CV approval UUID, editable letter/email content and
  expected latest revision. Server supplies bounded job context, documents and hash.
  Return the immutable revision; safe 409 on stale revision/state. No email or ledger
  changes on save, preview, approval or download.
- POST package approval takes exact revision/fingerprint plus explicit true
  approval. Server validates owner/state/latest content and stored-byte hashes.
  Repeating identical approval is idempotent; no implicit send authorization.
- Private GET/HEAD document routes use existing owner checks and safe content
  disposition; same bytes as previewed package. Cross-owner/unknown return 404;
  anonymous requests denied. Existing auth/CSRF and configured throttling are reused.
- No automatic mutation retry. On network uncertainty, GET current package/approval
  to reconcile before the user chooses another action. Reset local approval UI
  whenever revision/content changes; never trust checkbox state across updates.

## P4-P5 authorization and sending boundary

Separate document approval from an explicit per-application authorization showing
recipient, selected package revision, attachment names, email subject/body and
verified Reply-To. No prechecked consent or authorization covering future jobs.
Authorization binds those values, purpose/policy version and server time; withdrawal
blocks work not yet dispatched, without pretending it retracts an accepted email.
Exact schema/idempotency and transaction boundary need a further P4 design review.

Use the shared Brevo delivery ledger only. Recipient changes require a new reviewed
package/authorization. Copies remain OFF, attachments and real delivery remain
disabled until separately approved. Never claim provider acceptance is inbox
delivery. Persist reserved/accepted/definite-failure/unknown states honestly;
uncertain outcomes block retries and require reconciliation. Never activate legacy
console/SMTP fallback. Owner-only synthetic pilot uses a genuinely owner-addressed
job, not recipient rewriting of a real employer listing.

## Tests, rollout and next decision

P1: migration from populated current schema adds empty tables without changing
Application, CVApproval, ledger, preferences or document bytes; constraints fail
correctly; inspect migration plan and test compatibility. No production migration.

P2-P3: owner/cross-owner, stale revision, concurrency/last revision, immutable hashes,
approval invalidation, profile/job edits, missing/changed files, replacement races,
failure cleanup, letter regeneration restrictions, long/synthetic content, keyboard
and mobile controls, bounded errors, no provider/mail/ledger effects. Assert the
legacy email action cannot bypass new approvals. Existing external confirmation
and ingestion remain unchanged. Run complete backend/frontend gates and refresh
committed frontend_build as the final frontend package commit.

P4-P5: apply the existing sending design's explicit authorization, budget, duplicate,
failure, unknown, suppression/privacy and owner-pilot gates. No automatic website
submission or employer communication is authorized by this roadmap.

**Next review:** approve or amend P1's exact schema, per-job letter-revision scope,
and proposed snapshot limits. Then implement and test the additive migration package
locally and stop for its review. No pushes, merges or deployment are authorized by
this document. This is a design artifact; no new runtime tests are claimed for it.
