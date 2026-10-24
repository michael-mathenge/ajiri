# Application pipeline and personal progress

24 October 2026. AJ-50 implementation is local until the release record explicitly
states otherwise. No sending expansion or employer decision is part of this feature.

## User guide

In **My applications**, review saved documents separately from **Track my
progress**. Record Applied, Interview, Offer or Closed and an optional private
note (1000 characters). These are your own reports, not employer confirmations.
Saving an update never sends/submits an application, changes delivery receipts,
authorizes email or rewrites approved document bytes. Choosing No update reported
with an empty note clears the current personal report. The last update time and
revision are retained; this is a current-state tracker, not a historical journal.

Delivery evidence is independent:

| Evidence | Meaning |
|---|---|
| Draft / Ready for review / Dismissed | Existing preparation state; inspect the saved package for document approval. |
| External submission reported by you | You recorded submission; Ajiri did not verify it with the employer. |
| Provider accepted | A receipt records provider acceptance; inbox delivery is unconfirmed. |
| Outcome uncertain / awaiting reconciliation | Unknown or reserved receipt; do not infer delivery or repeat provider IO. |
| Latest email attempt failed | Failed attempt evidence, not an employer decision. |
| Historical email record, evidence unavailable | A legacy sent row without a provider receipt; no new delivery proof is inferred. |

Opening an employer link is not submission. A personal Offer/Interview selection
does not prove an employer response. Reports do not change the preparation/sending
state or auto-complete a job. Notes remain private to the application owner and
are included in their private export through the existing field inventory. They
follow existing application removal/backup retention; no immediate backup purge
or new legal consent is claimed.

## API and data preservation

Authenticated owner-only `PATCH /api/jobs/applications/<id>/progress/` (and its v1
alias) accepts only expected_revision, stage and note. Revision claims serialize
updates; a stale edit returns409 and must be reloaded, not automatically retried.
Oversized revisions/notes and attempts to write sending fields are rejected.
Private list/update responses use no-store. List evidence comes only from the
owner's application receipts and exposes no provider IDs or accounting keys.

The client updates the shared query cache, allowing later receipt refreshes to
replace its saved progress response. It does not keep a sticky local row that
can mask new server evidence. Errors retain all messages and accessibility IDs;
inputs cannot change during a pending save. The shared Button requires explicit
type=submit for form submission; a component regression verifies the real click.

Additive jobs.0015 gives old rows not_reported/empty note/revision0/no reported
time; it preserves application state and snapshots without inferring consent,
interviews, offers or successful delivery. Apply it after a verified private
backup and before new code handles requests. A data-preserving source rollback
leaves these columns and later reports in place. Do not reverse history or restore
a stale database over newer reports/delivery decisions.

## Verification status

Initial10 focused backend/migration tests passed1.066s; an extra cross-owner
receipt regression was added afterward. Four focused client regressions passed,
including refresh after a save. Initial140-component run had one CV focus timing
failure: the test now waits for the same existing post-render focus effect.
No CV focus requirement was weakened. Strict offline JSON schema passed.
Full434 Django tests passed365.125s (one known platform skip); all141 components
passed62.01s, Node24.19 locked install audited364/zero vulnerabilities, lint/ESLint,
Ruff and build2.00s passed. Source/runner and exact36-file generated-build checks
passed. The real Chromium progress save/reload journey passed31.108s, including
axe and zero email/provider/ledger effects. All nine local browser journeys passed
246.544s; strict schema regeneration matched exactly. CI and deployment remain
pending. No real owner progress or employer outcome was entered by Codex.
