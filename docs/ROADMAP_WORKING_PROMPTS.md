# Ajiri roadmap: working prompts

15 October 2026. Michael's P0/P1/P2 tables are backlog input, not blanket approval
to install libraries, rewrite architecture or deploy. Use the prompts below only
when Michael invokes the relevant item. Keep acceptance focused and size each
package before building; do not force the whole roadmap into one checkpoint.

## Reconciled baseline

| Table item | Actual state / next action |
|---|---|
| Password validation, request throttling, content sniffing, deploy settings | Implemented locally in Checkpoint 3A, pending Michael's review and production verification; do not repeat them as missing |
| Refresh-cookie CSRF | Design complete, mitigation not implemented; protected auth approval needed |
| Throttling strength | Per-process approximate cache, live proxy hops unverified; request throttles do not require SMTP and are not daily mail quotas |
| Password reset / verification | Application features absent; already proposed in audit impact as WP17, not absent from planning |
| Real email | Console only; chosen direction is isolated dependency-free Brevo HTTPS, reachability pending; Gmail owner-only fallback |
| Privacy / rights / monitoring | Proposed, not implemented; legal wording DRAFT, manual verified rights at launch; backups automation not yet designed |
| Upload safety | Structural PDF/DOC/DOCX checks now exist locally; malware scanning remains a separate feasibility decision |
| API / tests / frontend tooling | Existing pagination/filtering, component tests, axios hook and oxlint; no schema, browser E2E or coverage/a11y gate established |
| Build / deployment | Committed frontend_build and exact CI comparison remain required; change only through an approved deployment design |
| Job deduplication | Unique source URL already prevents exact-source duplicates; cross-source/fuzzy deduplication is a separate product improvement |

Checkpoint 3A numbering superseded earlier proposal WP11-WP15. Use the prompt IDs
below until Michael assigns future work-package numbers; never mix the two sets.
See [3A review](CHECKPOINT3A_REVIEW.md), [audit](MODERNISATION_AUDIT.md),
[decision form](DECISIONS_NEEDED.md) and [SMTP design](SMTP_EMAIL_DESIGN.md).

## Common instruction block for every build prompt

Read AGENTS.md and the named design/review first. Confirm Michael's exact scope and
the reviewed base revision; do not assume local 3A is merged/deployed. Use one branch
per bounded package and stop conditions/quality gates from AGENTS. Preserve the
existing auth client, JSX and Python matrix. No secrets, production operations,
destructive data changes, migration-history changes, paid service, new dependency,
CI/hosting change, push or PR merge unless separately authorized for that action.
Design-required migrations need Michael's exact schema approval before implementation.
Report actual tests, limitations, manual review steps and suggested story points.
For a frontend package, package frontend_build once as its final commit unless its
replacement policy has been separately reviewed and approved.

## P0-A: finish the security release gate

**Working prompt:** Review Checkpoint 3A instead of rebuilding it. Reproduce its
password/upload/throttle regressions and deploy-profile checks locally. Separate
code that passed from production verification still pending. Design a practical
shared-counter strategy for the confirmed PythonAnywhere topology and a correct
trusted-proxy configuration; do not guess NUM_PROXIES or call LocMemCache a hard
distributed limit. Obtain separate authorization before implementing the chosen
refresh-CSRF option or changing silent-refresh 429 recovery. Preserve rotation,
blacklisting, cookie-only refresh tokens, CORS and ingestion behaviour. Show tests
for cross-origin rejection, legitimate browser flows and no redirect loops.

**Done when:** Michael has a reviewable security release checklist, tested fixes
within the approved scope and explicit open release gates. HSTS stays short with
subdomain/preload off; intentional W005/W021 advisories are documented, not hidden.
Production verification remains Michael-only. No repeated live load/brute-force tests.

## P0-B: delivery and account recovery

**Working prompt:** Implement real email only after provider reachability and
sender decisions are confirmed. Keep Brevo HTTPS in one isolated module using
existing/standard-library capabilities; Gmail is an owner-only pilot fallback.
Use verified platform From and applicant Reply-To. Enforce 10 accepted applications
per user/day and Michael's confirmed global budget below provider limits, prioritizing
applications over alerts. Define copy/attachment budgets, bounces, complaints,
suppression and minimal attempt metadata before schema approval. Retain 502 and
reviewable retry for definite failures; never auto-retry ambiguous acceptance, and
show a duplicate-delivery warning before a manual retry. Keep mail switchable off.

Then implement anti-enumerating password-reset and email-verification flows as a
separate package. Confirm what unverified/existing accounts may do, expiry/resend
rules and password-change session revocation before coding. Use Django validators
and token primitives; preserve auth boundaries unless explicitly approved. Mock
transport/use in-memory mail in tests and CI. No real provider calls from CI.

**Done when:** acceptance/failure/quota/concurrency tests pass; reset links expire
and cannot replay, invalid requests reveal no account existence, unverified identity
cannot be used for employer mail under the approved policy. Rollout starts with
synthetic documents to Michael's controlled inbox, performed manually by Michael.
Domain, global cap, provider reachability and remaining form choices stay unresolved
until supplied; placeholders are never configuration values.

## P0-C: privacy and usable rights at launch

**Working prompt:** Keep all legal text DRAFT pending the named reviewer's approval.
Propose a public privacy notice with controller contact, purposes/lawful bases,
processor/cross-border disclosures, retention and rights. Separate versioned notice
acknowledgement from optional email choice; alerts default off for new users and
existing users confirm in-app before any alert email. Record server timestamps and
consent versions without inventing historical consent or collecting unnecessary IPs.

Provide manual identity-verified export/deletion fulfilment for launch, with a
dry-run-first deletion command design and separate destructive-action approval.
Inventory owned DB rows, private media, auth sessions, pending sends, shared records
to retain, provider copies and backups. Define partial-failure/retry and a restore
procedure that does not resurrect deleted accounts. Self-service is deferred.

**Done when:** legal owner/contact and retention are confirmed, notice/choice UI and
owner-isolation tests pass, export excludes hashes/tokens, and deletion is rehearsed
only against explicitly disposable local data. Seven-day export expiry and 30-day
rolling backups are starting proposals, not final legal commitments.

## P0-D: operational visibility and recoverability

**Working prompt:** Design dependency-free sanitized error logging, a minimal
GET/HEAD health endpoint and visible ingestion/sweep failure ownership. Health must
not reveal versions, paths, secrets or private records, and does not prove mail or
feed freshness. Cover failure status and redaction tests; stop logging CV-bearing
content as if console delivery were safe production delivery.

Separately design automated private DB/media backups that fit the actual free-tier
CPU/disk/scheduler limits. Compare manual minimum plus verified restore against
approved automation; define consistent SQLite backups, encryption/access control,
off-host custody, retention, deletion replay and failure alerts. No server access,
credentials, GitHub secrets, scheduling workflow or production copy is authorized
by this prompt alone. Do not assume free-tier scheduled tasks are available.

**Done when:** a human can identify failed ingestion and stale data, perform the
documented recovery rehearsal, and renew the app before expiry. Automation is not
declared complete until its supported schedule, restore and failure path are proven.

## P0-E: repository controls (current authorized action)

For michael-mathenge/ajiri, require PRs, current-branch CI, frontend and backend
3.12/3.13/3.14 checks from GitHub Actions, resolved discussions, no force pushes or
branch deletion, and admin enforcement. Michael selected **zero approvals until
an independent reviewer is added**; don't impose an impossible self-review rule.

Protection, dependency graph, Dependabot alerts and security-update PRs were saved
and verified on 15 October 2026. Secret scanning/push protection were already enabled
and were preserved. [Dependabot version configuration PR #6](https://github.com/michael-mathenge/ajiri/pull/6)
contains only weekly npm/pip/Actions update proposals (Monday 09:00 Nairobi), limited
to three version PRs per ecosystem with minor/patch grouping. It has not been merged;
scheduled version updates activate after Michael merges the configuration to main.
No auto-merge is enabled. An already-installed YAML parser validated the configuration
and its Git blob hash matched the committed file. No dependency version was upgraded.

An owner-scoped connector has Michael's authority: these rules cannot distinguish
his manual merge from an API merge after checks pass. Human-only merge separation
needs a separately permissioned integration and/or independent reviewer, not a claim
that branch protection makes all agent merges technically impossible.

## P1-A: browser quality and supply-chain gates

**Working prompt:** Start from risk-based E2E scenarios: registration, sign-in/refresh,
profile upload, prepare/review/send/failure/dismiss and keyboard/mobile navigation.
Propose Playwright, axe, coverage and Lighthouse budgets with dependency/CI changes
itemized for approval first. Mock external mail; synthetic data must never reach an
employer. Establish baseline bundle/network/accessibility measurements before budgets.

Review existing oxlint, tests and Python stubs before proposing ruff, formatter,
eslint replacement, pre-commit and mypy/pyright. Keep JSX; no TypeScript migration.
Plan pip-audit/npm audit and focused patch review alongside Dependabot. Preserve
required check names or coordinate branch protection before renaming CI jobs. Free
secret scanning is already on; never print real findings containing credentials.

**Done when:** approved reproducible gates catch meaningful regressions without flaky
live services or silently skipped security tests. Coverage has measured evidence;
hooks remain convenience, CI is authoritative. No tool installation is implied here.

## P1-B: frontend data/forms and API contract

**Working prompt:** Measure duplicate fetches, stale state, retry needs and form
inconsistency before replacing the existing hook. Compare a small in-place fix with
TanStack Query; compare existing forms with React Hook Form/Zod. Obtain explicit
dependency approval, migrate one vertical slice at a time, preserve all field errors
and auth-client behaviour. Never retry send/apply automatically or persist private
documents/tokens in a cache. Account for mobile data cost and cache invalidation.

In a separate package, propose OpenAPI via drf-spectacular versus a docs-first contract,
with schema/security/error/pagination examples and compatibility tests. Decide whether
versioning solves an actual breaking change before introducing /api/v1; keep existing
/api consumers functional. Approval is needed before dependency or routing changes.

**Done when:** the approved slice demonstrates fewer duplicate requests, correct
loading/error/invalidation behaviour and accessible consistent form errors; contract
tests agree with server and client without gratuitous rewrites.

## P1-C: build, staging and repeatable deployment

**Working prompt:** Design a replacement for committed frontend_build before removing
it or its exact CI guard. Compare CI-produced immutable artifacts with deployment-time
builds under PythonAnywhere free-tier limits. Define revision/artifact linkage,
checksums, custody, download/authentication, release activation and rollback. Ensure
Dependabot frontend PRs can obtain a reviewed matching build until the policy changes.

Propose a staging environment and narrowly scripted deployment, with private media,
no real mail/production data, explicit server operations owned by Michael, and backup
-> migrate -> activate ordering. Audit existing .env.example before adding one;
templates list names/placeholders only. Devcontainer/setup additions need dependency
and platform support review rather than an assumed Docker requirement.

**Done when:** a disposable environment can build/recover the same revision and a
reviewed deployment design preserves data/security. No CI, hosting, generated-artifact
policy or production action is authorized until the replacement is approved.

## P2: discovery, scale and product experiments

Treat each row as its own discovery/design prompt, not a combined build request.

| Prompt | Required outcome before implementation |
|---|---|
| Public jobs / SEO | Decide public versus authenticated boundaries; verify source rights and job freshness; propose JobPosting structured data, canonical pages/sitemap and prerendering/SSR without exposing applicant data |
| Search quality | Measure current filters/results; assess SQLite FTS availability/tokenization/ranking and additive indexing/migration options before promising it; preserve existing queries and evaluate representative Kenyan jobs |
| Scale | Measure N+1/query counts, ingestion/matching budgets and SQLite contention first; compare Postgres, private S3/R2 and background work with real host/cost limits, migration/rollback and signed owner downloads |
| English / Swahili | Confirm audience/translation owner and terminology; design locale, fallback, dates/currency, mobile layout and tests; don't auto-publish legal translations |
| Payments / subscriptions | Validate Free/Starter/Pro demand; design M-Pesa entitlements, authenticated webhooks, idempotency, reconciliation/refunds and sandbox tests; no live payments or provider credentials |
| Application pipeline | Decide statuses and external-employer semantics; preserve saved-document/review history and explicit regeneration; design before any status migration |
| Saved searches / alerts | Define saved criteria, frequency, consent, quiet hours and sending budgets; keep application and alert quotas distinct |
| Moderation / deduplication | Define reviewer tools, flagged-job appeal/audit handling and cross-source duplicate criteria; preserve exact source-URL uniqueness and avoid destructive merge/delete automation |
| PWA / offline | Measure poor-network journeys first; propose installable public shell/retry UX with cache versioning/logout cleanup; never cache private CVs, tokens or authenticated API responses by default |
| Analytics | Define the questions/metrics first; compare no analytics, server aggregates, Plausible/Umami under actual hosting/cost constraints; consent wording, retention and third-party processing require legal review |

## Suggested sequence and handback

1. Review Checkpoint 3A and verify the repository controls; keep production gates open
   until Michael performs the proxy/cache/header checks. Do not infer deployment.
2. Launch readiness: CSRF follow-up, controlled mail, account recovery/verification,
   legal-reviewed privacy/rights and operational recovery; separate bounded packages.
3. Professional baseline: E2E/a11y/supply-chain gates, then measured frontend/API
   changes and an approved build/deploy replacement. No dependency shopping spree.
4. Product-led experiments: choose SEO, language, search, payments or analytics based
   on evidence; move infrastructure only when current limits or reliability justify it.

For each invoked prompt, hand back scope/branch, actual test results, risks/limits,
manual verification and story-point suggestion. Ask only decisions that block that
package. Existing open placeholders remain in DECISIONS_NEEDED.md; this roadmap does
not manufacture answers, legal approval, migration approval or access credentials.
