# Next package: draft an application from an approved CV

Prepared 17 October 2026 after review of the personal CV builder. Local proposal;
no application behavior changed by the ingestion reliability package.

## Proposed behavior

On Job Detail, the user chooses an explicitly labelled owner-approved CV revision,
can download it for reference, and clicks Prepare application. The current approved
revision is the suggested choice; choosing an earlier approved revision is explicit.
If none exists, link to the CV builder. Browsing jobs stays available.

For a new application, `POST /api/jobs/<id>/apply/` requires `cv_version` (approval
UUID). Validate ownership and saved file size/hash, then copy those exact DOCX bytes
to the application's existing private generated_cv snapshot. Generate the job-specific
cover letter separately; preserve separate letter/email review before any send.
Never silently regenerate the approved CV from the current Profile.

Existing applications return their existing snapshot as today. Selecting a different
CV must not overwrite an application, silently regenerate documents or resend it.
Replacement/redrafting stays a separate explicit action and review. Old clients
creating a new application without a CV selection get a stable JSON 409
`cv_approval_required` and must reload/use the builder; no silent legacy fallback.

## Implementation boundary

Use existing Application document fields, private storage and owner download routes;
no model/migration or new dependency is proposed. The chosen DOCX bytes become the
application's independent snapshot. Approval UUID provenance is not persisted in
the current schema; adding audit provenance would require its own reviewed design.

The existing unique user/job constraint must arbitrate concurrent preparation.
Coordinate database commit and newly written files, cleaning only the losing
request's files. A failed/uncertain request must not automatically create another
application or trigger real email. The existing apply throttle remains in force.

No change to auth, refresh cookies, ingestion, CORS, CI, real sending, alert
preferences or existing sent documents. No push/deployment until batch approval.

## Acceptance and tests

- New draft CV bytes equal the selected approval's verified bytes even after
  Profile changes; cover letter and email remain reviewable separately.
- Missing selection gives the builder path; unknown/cross-owner versions give 404.
  Corrupt/missing selected CV returns a safe error without creating partial rows.
- Repeated/concurrent apply preserves one application and its initial snapshot;
  failed writes leave no request-owned orphan files where cleanup can complete.
- UI clearly labels revisions and old snapshots, disables duplicate submissions,
  and retains errors without auto-retrying a mutation.
- Run all backend/frontend gates, refresh frontend_build last, and hand back local
  package results for review. Real application delivery remains disabled/unchanged.

Recommended next implementation: require explicit approved CV selection for new
applications, retaining all existing application snapshots. Review this compatibility
change before replacing the current Profile-based drafting path.
