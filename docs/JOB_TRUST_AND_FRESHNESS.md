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

## Local implementation status - 23 October 2026

Implemented locally; not yet released. The shared eligibility check covers job
lists, detail, matching, alerts and new application preparation. A vacancy needs
published evidence and a future closing date or confirmation expiry. RSS evidence
must also have been confirmed within 24 hours. Unknown legacy entries are archived
as unverified, not represented as proven expired. A feed outage never proves that
an employer has closed a vacancy. Archived entries are not automatically reopened.

Employer owners submit an organisation and a vacancy with a mandatory closing
date. A separate staff account reviews both before publication. Self-review is
forbidden; decisions retain the actor, revision, time and reason. Owners can
withdraw listings. Browsing and applying remain free; no payment collection was
added. Review is a documented check, not a guarantee of authenticity or employment.

Additive migrations jobs.0012 and jobs.0013 preserve existing jobs and documents.
The optional application URL is nullable so SQLite can add it without rebuilding
the full-text-search table and losing its triggers. Regression tests exercise
migration, search update/delete triggers and preservation of old rows.

Deployment requires the verified backup, migrations, then code activation.
JOB_FRESHNESS_ENFORCED must be true for the new workflow. The independently
controlled EMPLOYER_POSTING_ENABLED and PUBLIC_JOBS_ENABLED switches can disable
new posting/public pages while keeping freshness protection enabled. Do not roll
back to exposing unverified rows or restore an old database over subsequent writes.
Existing application documents remain private and accessible to their owners.

Account-security email remains an owner-only pilot. General employer verification
onboarding is not live until that delivery boundary is expanded and verified.
No real employer was approved or real application sent during these tests.
Employer/moderation records currently block account erasure pending a reviewed
ownership/retention plan; implementation approval is not an erasure request.

Final backend, component, browser and CI gates are pending. Counts from earlier
runs are regression evidence only, not a claim that this package is deployed.

Final local browser journey gate: all seven tests passed in 187.825s, including
owner submission, independent organisation/vacancy staff review, correct external
application portal, accessible employer dashboard and withdrawal. Synthetic mail
provider remained uncalled. Earlier selector failures were corrected against the
actual accessible labels; no application assertions were removed. All 378 backend
and 132 component tests passed. Performance and remote release gates remain pending.
