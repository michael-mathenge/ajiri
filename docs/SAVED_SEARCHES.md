# Saved searches and frequency windows

24 October 2026. AJ-43 requirements and test-integration first package. This
document does not claim a production email rollout. Check the release evidence in
JIRA_ROADMAP_PROGRESS.md for the actual deployed revision and activation status.

## User workflow

Open **Saved searches**, or **Save this search** on the jobs page. Name the query
and choose keywords, location and job type. Each account can retain ten searches.
Choose in-app and email frequency independently: Off, Daily or Every seven days.
Both default Off. Saving a frequency never enables global email consent or sends.

In-app choices also respect the Profile in-app preference. Open **Show matches**
to see collected current results. Only verified current vacancies appear; closed,
scam and unverified listings are excluded again when you open the results.
Filters are never treated as a hiring prediction or as a 70% skill-match claim.

Daily windows close at the next Africa/Nairobi midnight. Weekly windows close at
midnight seven days after the choice. The existing matching sweep processes due
windows, so collection can occur later than the boundary. Only jobs first ingested
after your saved choice are considered. A window retains at most 50 current jobs,
newest first; browse/search for the complete current inventory. Missed windows
coalesce rather than sending a backlog of separate old alerts.

Editing uses the displayed revision and resets future windows. Conflicting edits
require a reload. **Remove** stops future collection and removes this preference's
private matches, while shared delivery accounting remains intact. Historical match
evidence is not a claim that a role remains open.

## Email boundary

Production email sending is disabled for saved searches. Frequency is a stored
preference only. A future email route also requires verified exact-address proof,
current explicit Profile consent, unsubscribe/revocation, current availability,
shared daily allocation and rechecks immediately before handoff.

The included integration requires three closed test-capture conditions and real
email disabled. It uses Django's memory backend only, with no Brevo/SMTP path and
no production caller. Tests cover overlapping queries, quota use, unknown outcomes,
changed addresses, changed revisions and revocation before handoff. No uncertain
receipt is automatically retried; provider acceptance is not inbox delivery.
Existing account/application/alert pilots and their recipient limits are unchanged.

## API and data

Owner-authenticated routes, with equivalent `/api/v1` aliases:

- `GET/POST /api/jobs/saved-searches/`
- `GET/PATCH/DELETE /api/jobs/saved-searches/<uuid>/`
- `GET /api/jobs/saved-searches/<uuid>/matches/`

PATCH requires `expected_revision`. All other-owner reads/mutations/results return
404. Responses are private/no-store; mutations use a user-scoped rate limit.
Filters reuse the bounded literal job-search contract. Pagination links are never
followed to arbitrary external URLs by the client.

Additive `jobs.0014_saved_search_windows` creates preferences and per-window match
records. No existing user receives a new choice or consent. Owner exports include
the preferences, matches and relevant job context while excluding internal receipt
links; verified account removal cascades these owned records. No real account
erasure is part of this package.

## Activation and rollback

Keep `SAVED_SEARCHES_ENABLED=False` until a fresh consistent private backup,
off-server verification and isolated restoration pass, then apply jobs.0014 before
the new code handles requests. Enable the feature only after the checked release
is staged. The existing matching sweep gains in-app collection; no scheduler,
CI, ingestion credentials, authentication or hosting configuration is changed.

Disable this switch to stop routes/collection while retaining rows, cursor windows,
consent and receipts. Do not reverse migration history or restore an old database
over later writes. Keep vacancy freshness enforcement enabled. The memory-email
test constant is not an environment switch for production sending.

## Verification status

Initial focused 15 tests passed after correcting scoped-throttle construction;
the expanded 21 scheduling/privacy/delivery tests passed. Five client regressions
passed, then the full 137-component suite passed. Node24.19 locked installation
audited 364 packages with zero vulnerabilities; lint/ESLint/build passed. The
verification directory required explicit lint paths because its parent is ignored.

Initial full Django run: 401 tests, one known platform skip, one alias-fixture
error for the new UUID primary-key route. The fixture now supplies an actual UUID;
exact legacy/v1 view assertions remain unchanged. Schema enum collisions were
resolved with consistent labels and a named shared enum; strict offline validation
passes without suppressing warnings. Final full Django run passed 402 tests in
304.617s (one known platform skip); system and migration-drift checks passed.
The new Chromium saved-search journey passed in 29.854s, including axe and zero
provider/mail/consent/ledger effects. A sandbox run failed because temporary
storage creation was denied; the full pass used local temporary-storage access.
All eight local browser journeys passed in 193.183s. CI and release gates remain
pending; local results are not deployment acceptance. Hook-safety and exact
source/runner/build comparison passed (36 generated files).
