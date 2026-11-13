# AJ83 owner-controlled suggestions

Branch `codex/mvp2-aj83-candidate-choices` starts from reviewed MVP2
9db23ab333e39d3bb12dbf30920d6f875ee7a0f3, the checked PR96 merge.

## Behaviour and boundaries

The private suggestions view ranks currently eligible roles using the existing
listed-skill overlap arithmetic, without a70% cutoff. Existing normalized filters
apply identically. Unknown skills still score0. Browse jobs remains unchanged.
The candidate can explicitly dismiss a role and restore it later. Restoring an
expired role never changes its eligibility. Existing applications, saved searches,
alert preferences and sending authority remain independently controlled.

Choices are owner-scoped, private/no-store and revision checked. A stale replay
cannot overwrite a later choice. SQLite claims the writer slot before deciding
whether the first choice exists; locks return generic503. Strict input cannot
assign another owner. Only existing owned history remains readable after expiry;
new choices require a currently eligible role. Freshness-off suggestions fail closed.
The existing owner-preference throttle budget is reused, with no new host setting.

The UI never retries a mutation automatically. After any failure, it disables the
mutation until an explicit authoritative owner-state read succeeds; the resulting
revision is used for a subsequent explicit choice. Every returned validation
message is retained. Dismissed rows remain paginated, and query invalidation
refreshes both the current suggestions and owned dismissal history.

Private verified-request export includes owned choices and their Job context,
excluding other owners. Erasure cascades only the owner's preference and retains
shared jobs; it still requires the prepared signed journal and existing guards.
No real account was erased or exported. Privacy tests use disposable synthetic data.

## Migration and rollback

jobs.0020_owner_recommendation_choices adds only RecommendationChoice, with unique
(owner, job), an owner CASCADE and shared-job PROTECT. No historic choice or consent
is inferred. Disposable forward/reverse checks preserve existing job metadata,
application progress and all three SQLite search triggers. No historical migration,
auth/cookies/interceptor/CORS, ingestion/key endpoint, CI or hosting setting changed.
Production order remains verified private recovery, paused writers/web, reviewed
additive migration, preservation, then activation. Code rollback retains this table
and new choices; reverse tests do not authorize deleting production preferences.

## Executed checks and corrected failures

- Check and migration drift passed. Ruff0.17.4 and strict generated OpenAPI
  comparison passed; safe synchronization verified39 generated frontend files.
- First nine API tests passed6.036s. The expanded12-case run initially had one
  error because the new erasure fixture attempted execution before preparing its
  required journal. The fixture was corrected; no guard was weakened. All12
  focused API/schema/export/erasure tests then passed9.963s.
- Complete backend suite:577 tests passed302.855s; one existing platform skip.
- Node24.19 locked npm ci installed358 packages, zero audit vulnerabilities.
  Oxlint/ESLint passed; two focused UI recovery tests passed7.33s; full166
  components/29 files passed37.20s; five tooling tests passed4.359s; build2.40s.
- Initial expanded real-browser journey failed16.951s: saved searches were disabled
  in that fixture. This also exposed that PR96's older prefill assertions could
  match the previous page's controls before navigation completed. The disposable
  fixture now explicitly enables saved searches and waits for its destination
  heading before reading fields. Production settings were not changed.
- Corrected actual Chromium journey passed17.041s: independent employer review,
  explicit zero/normalized mobile filters, actual saved-search destination/prefill,
  dismissal, retained normal job-detail access, restore, mobile accessibility and
  withdrawal. The provider remained mocked and uncalled. This is not a manual
  phone journey or consented participant acceptance.
- `git diff --check` passed. The generated build is committed after source.

## Remaining acceptance

The AJ83 implementation slices are locally verified but not production activation.
Required exact-head CI, release and private recovery/migration gates remain.
The8/10 consented participant target within5 minutes and genuine current vacancy
inventory remain unverified. No employer, participant, vacancy, consent, staff
access or production preference was fabricated. Production remains93cf55e.
