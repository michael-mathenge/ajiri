# Normal delivery reconciliation — 14 November 2026

## Exact source reconciliation

Baseline reviewed main/runtime c88da83. Archived PR73 is closed/unmerged at
38bf953c3a1a99c8efd3205d7a23fa68bde01cd2, not deployed normal transport. Its
focused adapter/test source was reviewed and ported, not wholesale merged. A full
old-branch replacement would remove newer browsing, normalized filters, owner
choices, shortlist and migrations0017–0021. These are preserved.

| Path | Existing state | This package / remaining live gate |
| --- | --- | --- |
| Account verification/reset | General adapter and shared ledger already deployed;14Nov actual configuration validates in account_security mode | No replacement. Genuine outside-employer onboarding/inbox remains unverified. |
| Application | Exact immutable authorization and owner pilot ledger deployed | Port general adapter and dispatcher hook; recheck owner/mailbox/job/plan/document bytes at final boundary. Two independent flags remain off. |
| Match alerts | Consent/revocation, notifications and owner-pilot evidence exist | Port bounded manual batch adapter/command; current consent,70%threshold and fresh vacancy required at handoff. No ingestion/sweep modification or scheduler activation. |
| Saved-search alerts | Owner searches/current normalized filters/durable windows/capture contract exist; production feature off | Port real transport behind independent flags; retain current county/work/experience collection and cross-search deduplication. |

New default-off settings: GENERAL_APPLICATION_EMAIL_ENABLED,
GENERAL_ALERT_EMAIL_ENABLED and SAVED_SEARCH_EMAIL_ENABLED. Existing application,
alert, saved-search, freshness and general account-security gates also apply.
Unknown modes/configurations never select a fallback SMTP/console sender.
No API shape, migration, dependency, JWT, CORS, ingestion or CI change.

## Bounded execution and failure handling

`python manage.py deliver_match_emails --limit 20` processes at most20 candidate
notifications in this invocation (allowed1–50, checked inside handle as well as
argparse). Counts are operational diagnostics, not inbox acceptance. Ineligible
old candidates can remain; this is a manual bounded caller, not a durable scheduler
or proof of fair automatic backlog progress. Inspect remaining acceptance before
wider automation. No command is run against production in this package.

`python manage.py deliver_saved_search_emails --search-id <UUID>` collects one
search's current due email window, with at most50 matches per delivery batch.
Saving/searching alone creates no email consent. No cross-owner public command
endpoint is added. Application dispatch still requires the current explicit exact
send authorization. Existing receipts reconcile before a new provider call.
Unknown/reserved outcomes must never automatically retry; failed attempts consume
shared capacity. An accepted receipt is not delivered-inbox evidence.

## Verification and activation gaps

The original13 archived adapter tests passed on current code. Four new regressions
cover mailbox change at final handoff, programmatic invalid batch limits, current
normalized saved-search filters and feature disable at handoff. Initial regression
run failed on the real unchecked-limit gap and a test county slug; handle validation
was added and fixture corrected to canonical nairobi-city. All17 targeted tests
then passed2.864s. Full package gates are recorded in the progress ledger.

Before any actual normal-path pilot: genuine eligible role, current verified
mailbox, exact authorisation or independent alert consent, provider/privacy facts,
reviewed attachments, shared budgets and a concrete permitted send are required.
Retain prior owner-inbox evidence without substituting it for a new normal path.
No production flag, provider call, scheduler, staff grant or participant consent
is inferred. Live AJ17/26/43 acceptance remains unfinished. Roll back source with
new receipts/data retained; disable channel-specific switches, never erase receipts
or replay ambiguous attempts. No storage cutover or queue activation occurs.

## Bounded continuation follow-up

Match command --limit (default20) and saved-search command --limit (default50)
accept1-50 and --cursor. Each invocation examines at most that many candidates;
ineligible/deleted candidates advance the signed continuation, without changing
consent or fabricating receipts. JSON output contains examined, aggregate outcomes,
next_cursor and exhausted. Pass the returned cursor explicitly until exhausted.
A fresh pass reconsiders previously skipped rows and sees new inserts. This is
manual keyset progress, not a scheduler or a durable processing guarantee.

Saved-search continuation binds the search UUID and revision; edits require a new
pass. The initial invocation may collect the existing bounded due window; continuation
never recollects it. Existing deliver_due callers retain their list return/default
50-row behavior. All current transport, consent, freshness and ledger checks remain.
Disabled commands perform no handoff. No normal live send is authorized here.
