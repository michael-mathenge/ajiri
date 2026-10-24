# Reasoned flagged-job review (AJ-49)

The existing Django JobAdmin is the entry point. No new staff access or credentials
are granted. An active staff member with jobs.change_job opens one flagged job,
checks its source text, scam signals, closing date and confirmation evidence, then
chooses Keep scam flag or Clear scam flag and gives a reason (1-1,000 characters).
No bulk approval is provided. Do not put applicant or private account data in reasons.
The source URL is displayed as reference text; the page never fetches it.

A review records actor, time, decision, reason, exact before/after evidence and a
fingerprint of the reviewed state. A changed job, deadline or prior decision makes
an old form stale (409); reload and check history before deciding again. SQLite
writer contention returns503 without pretending a review was recorded. A writer
claim precedes the evidence read; no uncertain decision is automatically retried.
HTML and reasons are escaped; Django admin permission and CSRF protections apply.

Clearing a scam flag changes that flag only. It does not verify the employer,
activate an inactive job, reopen an archive, extend a deadline or renew RSS evidence.
The common freshness predicate still controls browsing, alerts and preparation.
Current eligible jobs may become visible after a reasoned flag clearance; expired,
unverified and archived jobs stay hidden. Existing application documents and
snapshots are untouched. Staff should keep a flag where evidence is insufficient;
review is not a guarantee of authenticity, employment or legal compliance.

The normal admin form exposes active/scam flags as read-only so it cannot bypass
this reasoned decision. Audit records have no add/edit/delete admin actions.
Additive jobs.0016 creates a separate table, preserving the job table and its SQLite
search triggers. Actor/job foreign keys protect evidence from deletion. Existing
account-erasure preflight now stops for moderation evidence and requires a reviewed
retention/removal plan before any writes. This does not authorize actual erasure.
No automatic retention pruning, deduplication, employer appeal adjudication or
real organisation verification is introduced. Those need separately concrete scope.

## Release and rollback

Run all package gates, then backup/verify private off-server copy and isolated
restore, apply jobs.0016 while writers are paused, then activate reviewed source.
Do not reverse the audit migration or restore an old DB over later decisions.
A source rollback can preserve the audit table, but must not reopen the old admin's
unaudited flag-edit path: keep admin review unavailable until a safe fix is deployed.
This package changes no public API, auth/CORS, ingestion endpoint, CI or hosting.
No frontend change, dependency or real moderation decision is required for testing.

## Local verification

Initial nine tests found only an over-specific cache-header assertion: Django admin
adds stronger no-cache directives. The test now requires private and no-store and
keeps those additional protections. Ten focused tests passed0.883s, including CSRF,
permission denial, escaped text, reasons, stale changes, audit/erasure protection,
unchanged publication/application and actual concurrent same-evidence decisions.
After SQLite writer-claim hardening and an add-form None guard, focused ten tests
passed1.117s. An added migration preservation regression brought the focused suite
to11 passed2.706s and checks historical job/application values plus search triggers.
The preliminary450-test full run passed346.440s (one platform skip) but predates
those final changes. Final451-test full suite passed379.607s (one known platform skip).
Node24.19 locked install audited364/zero findings, lint/ESLint and build2.17s passed;
all36 generated files remain unchanged. All141 components passed81.08s. Ruff,
strict offline schema drift and three hook-safety tests passed. PR52 passed all six checks (CI40085261401) and deployed as
bc456497ac84eea5fb3055a887be3aabb857873d. A fresh private off-server backup and
isolated restore passed before jobs.0016. All pre-existing table values were
preserved, excluding expected Django migration/permission metadata. The new audit
table is empty: no actual job review or new staff access occurred. Check/drift and
empty migration plan passed; exact workflow states and enabled web app were
restored. Health200/HSTS300, exact live HTML/entry bundle and clean source passed.
Real staff review remains unperformed; the synthetic admin HTTP tests cover it.
