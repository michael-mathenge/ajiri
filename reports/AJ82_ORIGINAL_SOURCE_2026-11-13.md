# AJ-82: Ajiri-original employer vacancies

Michael chose Ajiri as its own original vacancy source on13November. This replaces
the proposed three-independent-feed requirement while retaining the planning
targets of50 genuinely eligible roles and10 genuine employers. Those targets are
not current inventory, authority to invent jobs, recruitment outreach or consent.
Jira's original proposal is preserved below the superseding acceptance section.

Feature branch `codex/mvp2-aj82-original-source` starts from reviewed MVP2 and
incorporates the checked AJ-87/AJ-85 merges, latest base `fbd8834`. It extends the
deployed employer organisation/draft/review/canonical-listing flow rather than
rebuilding it. Original main/user work and archived migration history are preserved.

## Resulting behavior

New employer UI vacancy requests retain a UUID decision through failed/unknown
responses. An exact same-owner, same-normalized-intent replay returns the existing
record200; first creation returns201. Ownership collisions or changed details
return a generic409 without exposing another employer. Defaults for omitted
requirements/job type are included in the comparison. New decisions remain distinct,
including legitimate roles sharing one application portal. No automatic retry or
publication follows. Legacy clients may omit the ID and historical drafts retain
null; the new guarantee applies to requests carrying a submission decision.

Publication still requires current account-email verification, independently
reviewed organisation, a different staff reviewer, current revision and future
closing date, with scam/no-applicant-fee controls and owner withdrawal unchanged.
Each accepted role already gets its stable Ajiri listing URL; new postings are
labelled Ajiri employer posting. API publisher/listing metadata is derived from
employer publication provenance, never from a feed's claimed source label. Official
application URLs remain separate. Public employer guidance and private workspace
explain this original-source flow while retaining the actual onboarding pilot limit.

The read-only `original_source_readiness` command reports aggregate eligible original
roles, employers with eligible roles, pending queues and explicit inventory gaps.
It creates no records and exposes no employer names/emails/private paths. Disabling
freshness cannot make it claim inventory readiness. Counts do not establish employer
authority, inbox delivery or a consented usability pilot.

## Schema and release order

Additive `jobs.0018_original_employer_submission` adds a nullable unique UUID to
EmployerJobDraft only. Existing draft IDs/content, publication links and review
relationships are preserved. It does not infer historical decisions or change Job,
application/document tables or existing FTS triggers. Forward/disposable reverse
tests verify historical draft/review/job relationships and working search triggers.
The checked OpenAPI contract documents nullable IDs and200/201/409 semantics.

Before release: exact required CI, fresh quota/capacity report, consistent private
snapshot, independently verified off-server copy/isolated restore, then source
staging while web/writers are paused, expected migration plan and0018, then activation.
New requests must not reach the new model before the migration completes. Runtime
dependency pins are unchanged. Production rollback keeps the additive field/IDs,
new employer records, current database/media/ledger and safety flags; revert code
and matching generated assets together. Reverse migration is a disposable rehearsal,
not routine production rollback.

## Actual validation

Initial original-source/freshness suite:24tests passed in9.312s. Final focused
original-source/migration suite:11tests passed in0.850s. Focused UI:11tests passed
in5.71s. Explicit Node24.19 locked npmci installed358packages; formatting,
Oxlint/ESLint,5tooling tests, all161components/28files (24.31s) and build1.62s passed.
Pinned Ruff0.17.4, backend system/drift checks and strict schema generation/comparison
passed. The full555-test suite passed in261.722s, one existing platform skip.
Required CI remains pending at source commit.

The browser journey now loses the response after a successful synthetic POST,
explicitly retries the same decision, then independently reviews/publishes the one
role, verifies the Ajiri-original label and official application link, and withdraws
it with provider calls blocked. Its actual result requires CI; local component/unit
results do not establish a browser pass or manual phone/real employer acceptance.

No production migration, original employer/vacancy creation, public publication,
normal email/alert activation or pilot is claimed by this implementation receipt.
Genuine employer participation and independent review remain external live gates.
