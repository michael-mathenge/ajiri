# Analytics: offline requirements and test contract (AJ-51)

This is a memory-only synthetic integration, not production analytics or consent.
No endpoint, browser instrumentation, vendor SDK, cookie, migration or transport
has been added. No real user data is collected. Enabled defaults False, and even
an enabled fixture needs a separate explicit analytics choice before recording.
Email choice, account registration and privacy acknowledgement do not grant it.

The first questions are deliberately narrow: are search and document/application
review screens being used? Proposed allowlisted names are search_used,
cv_review_opened and application_review_opened. No event attributes are accepted:
no queries, paths, URLs, identities, files, free text, device details, IP addresses,
fingerprints or performance traces. Only Nairobi day/event/count is retained in
the fake aggregate. Small cohorts can still be identifying; aggregate does not
mean anonymous or legally compliant. No product hiring outcome is inferred.

The synthetic session records channel analytics, explicit choice, aware decision
time and proposal policy version. It begins without a choice. Revocation prevents
subsequent counts and leaves earlier aggregate values unchanged; a stale policy
or backwards/naive clock is rejected or fails closed. Thread-safe fixture counts
exercise concurrent calls. The exact memory collector is the only accepted adapter;
it has no network method. In-memory decisions are lost on restart and cannot be
used as a durable consent audit. There is no production caller or environment flag
that activates this contract.

## Before any live collection

Refine and approve the actual measurement purpose and lawful processing basis,
independent in-app choice wording, versioned durable consent/revocation evidence,
retention/deletion period, cohort disclosure limits and authorized report access.
Compare no analytics with minimal server aggregates before considering a vendor.
If a vendor is chosen, processing terms, geography, onward transfers, real host
eligibility/cost and privacy/legal review remain prerequisites. No legal approval
or personal choice is inferred from feature approval. Do not install an SDK first.

An approved implementation must default off, avoid network/storage before choice,
honor withdrawal at the collection boundary, survive reloads without inferring
choice, preserve account/email settings and test missing/expired/stale decisions.
Specify what withdrawal does to historical anonymous aggregates and identifiable
records separately. A retention policy is not selected by this fixture, and it
never prunes real data. Rollback disables collection first and preserves evidence
until the approved retention/removal process is available.

## Verification

Eight synthetic contract tests passed0.008s. Full459 Django tests passed332.771s
(one known platform skip); system/migration-drift, Ruff and strict offline schema
checks passed. Node24.19 locked install audited364/zero findings, lint/ESLint and
build1.96s passed. All36 committed build files and source/runner matched exactly.
Frontend source is unchanged; the prior141-component pass remains regression
evidence, not a new package run. Required remote CI remains pending. This advances AJ51's requirements/test-integration scope;
AJ51 must remain In Progress until the separately gated live scope is verified.
