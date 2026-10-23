# Job trust and freshness

Michael approved these requirements on23 October2026:

- Hide RSS listings without a reliable future closing date or current explicit
  employer/source confirmation. Feed presence and retrieval time are not proof of
  a vacancy being open. Never manufacture deadlines or reset age on every import.
- Employers sign in, submit their organisation and job for staff review, and
  supply a mandatory closing date. Review does not guarantee an employer's conduct.
- No payment is required from a job seeker to apply. Employer advertising must be
  separate from application access; no hidden job-seeker subscription charge.
- Closed/expired/unverified jobs disappear from active search, public pages,
  sitemaps, match alerts and new application preparation. Existing documents and
  application history remain available to their owners.

Implementation sequence:

1. Add publication evidence, explicit closing/confirmation timestamps and archive
   reasons without deleting or labelling historical rows verified. Centralise the
   eligibility predicate; check expiry at read time as well as during archiving.
2. Parse only supported explicit feed deadline fields. Invalid/past/missing
   evidence stays unpublished. Repeated URLs update closure evidence without
   resetting review, reviving archives or creating duplicate alerts. An unavailable
   feed/link alone does not prove a job closed. Arbitrary source crawling needs
   SSRF controls and source-specific contracts before use.
3. Add employer-owned drafts and organisation review, moderation reasons/audit,
   mandatory future deadlines, withdrawal and re-review after material edits.
   Employers cannot grant themselves verification or publish another owner's job.
4. Display provenance, review/confirmation time, closing date and archive reason
   clearly on phones. Avoid claiming employment or employer authenticity is
   guaranteed. Preserve actual reported/provider application states.
5. Cover expiry boundaries, unknown dates, stale duplicates, review/ownership,
   concurrent changes and all browse/alert/application paths; migrate only after
   a verified private backup. Rollback preserves new evidence and employer drafts.

This document records approved scope, not implementation or production evidence.
No real organisation is verified by these notes. The existing publication
prototype remains disabled until the shared freshness gate is integrated.
