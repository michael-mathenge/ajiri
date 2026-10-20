# Provisional backlog: requirements and test integrations first

21 October 2026. Michael explicitly selected requirements and test integrations
before live implementation for AJ-42–AJ-52. The contracts below refine the previous
one-line placeholders. They are not claims that providers, payments or new hosting
are active. Record test results before moving any item to Done.

| Issue | Concrete first scope | Required test integration / release boundary |
|---|---|---|
| AJ-42 Public jobs | Django-rendered public job detail, canonical URL, active/non-scam sitemap and truthful eligible JobPosting metadata; no profile/match/application fields | Synthetic active/inactive/scam/missing-date jobs; HTML escaping, canonical/sitemap exclusions, no private fields. Do not invent publication dates, salary or expiry to obtain rich-result eligibility. Keep private APIs authenticated. |
| AJ-43 Saved searches | Owner-only saved query/filter records; explicit in-app/email frequency choices; email never enabled by saving a search alone | Isolate owners; independent channels; email requires verified address plus current explicit consent and shared quota; daily/weekly windows deduplicate, start no earlier than consent, and honor withdrawal before handoff. Unknown provider outcomes never auto-retry. |
| AJ-44 M-Pesa spike | Identify merchant ownership, sandbox access, transaction reconciliation, supported terms/refunds/tax treatment and privacy needs | Document a mock checkout/status/callback contract first. Existing displayed prices are previews, not authority to charge. No purchase, merchant account creation or real transaction by the agent. |
| AJ-45 Daraja integration | Test-only initiation and authoritative reconciliation adapters using synthetic payer data; server-owned amount/currency and immutable checkout identifiers | Fake success, failure, cancellation, timeout, duplicate/out-of-order/spoofed callbacks, status-query disagreement and interrupted receipt writes. Callback content alone cannot grant entitlements. Live credentials, merchant terms and a user-approved real transaction are separate prerequisites. |
| AJ-46 Entitlements | Server-side tier/expiry and capability checks derived from verified payment records, not client labels | Anonymous/owner isolation, duplicate receipts, concurrent upgrades, expiry, refunds/revocation and Free fallback. Preserve browsing and existing documents. No premium state from an ambiguous payment or unchecked callback. Final commercial limits/terms must be explicit before charging. |
| AJ-47 Storage migration | Repeatable dry-run export/import into an isolated PostgreSQL/object-storage test target; canonical row/file checksums and a single authoritative writer | Verify row counts, canonical field values, FK constraints, UUID file identity and private owner downloads. Simulate failed copy/cutover and resumed writes. Never switch back to a stale SQLite database after newer PostgreSQL writes without a reviewed resynchronization plan. Provider/account eligibility and cost remain unverified. |
| AJ-48 Background queue | Queue adapter behind the same delivery idempotency/authorization ledger; fake executor before provisioning a worker | Duplicate/delayed jobs, withdrawal, stale documents, quota contention, worker crash before/after handoff, unknown outcome and reconciliation. Queue retries must not repeat an uncertain provider call. Current free-tier WSGI hosting is not an always-on worker service. |
| AJ-49 Moderation | Existing Django JobAdmin is the baseline; refine a reasoned flagged-job review action with actor/time/before-after audit evidence | Permission denial, CSRF, required reason, concurrent edits, single-job release and active/scam visibility. Avoid bulk approval of unreviewed jobs. Do not grant new staff access or create credentials as part of tests. |
| AJ-50 Pipeline | Owner view of prepared/reviewed/dismissed/external-reported/provider-accepted/unknown states, plus explicit user-entered progress | Never label acceptance as inbox delivery or an employer website visit as submission. Preserve immutable documents and separate user reports from provider receipts; isolate owners and paginate. No inferred interview/hiring decisions. |
| AJ-51 Analytics | Minimal first-party aggregate event contract; no analytics network activity before an independent explicit choice | Allowlisted event names only, no bodies/query strings/identities/documents/fingerprints; default off; revocation stops subsequent collection. Registration/privacy acknowledgement and email consent do not authorize analytics. No vendor SDK until processing/retention choices are settled. |
| AJ-52 Malware scanning | Private quarantine plus a scanner adapter with explicit clean/infected/unavailable outcomes, initially fake | Spoofed content, bounded size/archive expansion, infected/unavailable/timeouts, owner-only quarantine, race with download/replacement and no bypass. A clean scan does not prove a document trustworthy. Do not transmit real documents to a vendor or provision an always-on service without selecting the specific processing destination/access. |

## Shared requirements

- Existing rows receive no inferred consent, payment, verification, submission or
  employer outcome. Additive schema must have existing-row/mixed-version/rollback
  analysis and preserve newer writes.
- Test providers use synthetic data and make zero real financial/email/document
  submissions. Provider acceptance and status callbacks are not stronger evidence
  than the actual verified receipt.
- No automatic retries for ambiguous external effects. Stable idempotency keys,
  retained evidence and private operator reconciliation precede any explicit retry.
- Private data stays out of Git, CI artifacts, logs and public documentation.
- Legal/privacy review, hosting eligibility, credentials and commercial terms remain
  genuine release prerequisites where relevant. Do not mark an integration deployed
  merely because a design or fake adapter exists.
