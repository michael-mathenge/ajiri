# Durable aggregate analytics — inactive

AJ-51's memory fixture is historical test-contract evidence. The new backend uses
real additive jobs.0017 tables: AnalyticsChoice (owner/decision/version/time) and
AnalyticsDailyCount (day/event/count only). It does not import the fixture service.

ANALYTICS_ENABLED=False, ANALYTICS_PURPOSE_CONFIRMED=False and an empty
ANALYTICS_POLICY_VERSION block collection by default. No legal purpose, lawful
basis, notice approval or processing facts are invented. Final approval must supply
those actual facts and a published version before enabling collection. Registration
and email preferences never opt anyone in.

Owner API: GET/POST /api/jobs/analytics/choice/; POST requires decision_id UUID,
strict enabled boolean and the actual current policy_version for opt-in. Withdrawal
remains available while collection is disabled. Event API
POST /api/jobs/analytics/events/ accepts only event, one of search_used,
cv_review_opened or application_review_opened. Unknown fields/attributes are rejected.
It returns 204 without echoing private input; disabled collection returns 404.
Choice and event throttles have separate budgets so event submissions cannot consume
the withdrawal budget. No client instrumentation/third-party SDK is activated.

Owner locking serializes revocation at collection. Only daily aggregate counters
are stored for events, with atomic increments and allowlisted names. There are no
per-event user/session/document/path/query/IP/fingerprint records. Counters are
event-submission totals, not distinct-user/cohort metrics; duplicate requests can
count twice. There is no public or staff cohort/report endpoint, pending Michael's
purpose, access and suppression decisions. Do not claim k-anonymity from counts.
Host/access logs and operational backups require their own actual privacy review.

report_analytics_retention --before YYYY-MM-DD reports candidate bucket counts and
changes nothing. No retention/deletion policy is assumed. Choice records are included
in owner exports and cascade under the existing verified-request erasure workflow;
anonymous counters have no link permitting per-owner subtraction. No real account
export or erasure was performed by implementation/testing.

Activation order: verified private backup/off-server restore, apply additive schema,
activate paired code, then separately approve purpose/notice/retention/report rules
and actual flags. Rollback disables collection, preserves withdrawals and all newer
data, and retains populated tables. Never reverse populated migrations or prune
buckets/backups without an approved concrete retention policy.
