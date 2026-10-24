# Remaining roadmap: 24 October 2026

Live Jira reconciliation returned12 unfinished non-Epic issues with no next page.
AJ49 (reasoned moderation) and AJ50 (pipeline first scope) are now Done with deployed
evidence. This list distinguishes tested implementation from missing live acceptance.
No test provider is a live service. PR51 preparation and PR52 moderation are
deployed; PR53/54 offline contracts are included in verified release b6cc6af.
The final local suite passed467 tests (one platform skip), all six CI checks passed
for each PR, and production source/build/health checks passed. No analytics,
scanner, financial service or broader sending was activated. Use JIRA_ROADMAP_PROGRESS.md for actual revisions.

| Issue | Existing evidence | Next concrete boundary |
|---|---|---|
| AJ17 application/alert delivery | Shared ledger, exact document/plan approval, owner-only transport and preparation UI | Complete personal owner application authorization/pilot; reconcile actual outcome before broader delivery. Application sending remains off. |
| AJ26 notification email | Explicit choice/revocation and owner synthetic inbox/unsubscribe proof | Normal production transport/eligibility and bounded live acceptance remain gated. Earlier enabled preferences do not grant new consent. |
| AJ42 public jobs | Public templates/sitemap/metadata and strict freshness tests | Anonymous publication flag remains off; confirm publication/source evidence and release eligibility. Never publish unknown or stale jobs just to populate search. |
| AJ43 saved searches | Deployed owner queries, frequency windows, in-app integration and captured email contract | Real saved-search email transport/consent/budget acceptance remains pending. Saving alone does not opt into mail. |
| AJ44-46 payments/entitlements | Offline synthetic checkout/status/reconciliation contract and expiry/refund cases | Merchant ownership, real sandbox access, commercial/refund/tax/privacy terms, durable financial evidence and verified adapters. No transaction or premium upgrade is authorized by a fake callback. |
| AJ47 storage migration | Source/backup inventories; isolated copy/restore tools | Approved actual test target, PostgreSQL schema/bootstrap/search strategy and object-storage privacy/recovery rehearsal. See STORAGE_MIGRATION_REHEARSAL.md. No cutover. |
| AJ48 queue | Inline fake executor through the existing authorization/idempotency ledger | Eligible durable broker/worker target, crash/recovery and actual deployment. The free WSGI app is not proof of an always-on worker. |
| AJ51 analytics | Merged memory-only independent-choice/aggregate contract | Actual purpose, consent wording/schema, retention/cohort/report-access and provider/legal decisions; no production collection yet. |
| AJ52 scanning | Synthetic quarantine/fixture scanner under test | Real engine/host, private storage, signature/result freshness, legacy-file policy, bounded deadlines/resources and processing authorization. Existing uploads are not malware-scanned. |
| AJ53 employer posting | Deployed expiry/evidence, owner dashboard and independent staff review | General employer verification/onboarding beyond owner-only security mail, plus genuine organisation/listing review. No real employer was approved by Codex. |

The owner may enter credentials only through the actual approved service privately.
No purchase, legal acceptance, personal consent, irreversible deletion or live
financial transaction is inferred from the implementation request. Routine backups
remain automated where access is available, with verified off-server copies and
isolated restoration; retention stays report-only. Hosting renewal is still due
before19 November2026. Account quota was427.9/512MB after the latest release backup;
no retained backup has been deleted. A concrete pruning policy needs its own decision.
