# MVP2 proposal — 11 November 2026

**Recommended goal:** help Kenyan job seekers find genuinely current, relevant
vacancies on a phone, understand why they match, and apply with reviewed documents
and explicit control. Prioritize useful inventory and trust before monetization.
This is a proposed product scope and target set, not a promise that the targets
are achieved or that every carried issue must activate in MVP2.

## Starting point

MVP2 starts from reviewed `main`, initially
`e682cac4299102f963c1193d580979ecdefa219f` (PR81). The latest available deployment
receipt is 4 November; no new runtime verification or deployment is implied here.
MVP1 already includes account security, private CV review/downloads, search,
application progress, consent foundations, moderation and bounded supplemental
browsing. Reuse these features rather than rebuilding them.

Supplemental browsing was personally activated and audited on 4 November. Its
availability remains unverified: it does not make a listing eligible for application
preparation, alerts, public vacancies or JobPosting metadata. Last recorded eligible
count was zero. MyJobMag advert expiry is not accepted employer closing evidence.

The 4 November receipt recorded 330/512 MB storage usage, superseding the historical
482.4/512 MB reading. Neither is a fresh 11 November quota measurement. Capacity
must be remeasured before storage growth or deployment. No backups were pruned.

## Market benchmark

Primary product/help pages were reviewed on 11 November 2026. These establish
advertised capabilities, not a market-share ranking, independent quality test,
permission to scrape, or proof of employer/deadline verification.

| Comparator | Observed capability | MVP2 response |
|---|---|---|
| [BrighterMonday Kenya](https://www.brightermonday.co.ke/) | Keyword/location search, experience segments, profiles and personalized alerts; career tools | Make local discovery and useful alert preferences work before adding a large service catalogue. |
| [Fuzu Kenya](https://www.fuzu.com/kenya) | Local jobs, employer directory, matching, learning and career guidance | Explain fit and help users improve their own reviewed documents; avoid an unsupported AI-outcome claim. |
| [Indeed alert help](https://www.indeed.com/help/job-seekers/articles/204488890-starting-stopping-and-managing-job-alerts?co=IN&hl=en) | Editable search terms/location, daily or weekly frequency, pause and unsubscribe | Complete AJ26/43 with independent opt-in, clear controls and no mail when no eligible new results exist. |
| [LinkedIn preference/visibility help](https://www.linkedin.com/help/linkedin/answer/a507508) | Role/location/employment preferences and visibility choices | Keep matching preferences candidate-controlled and profile/documents private by default. Recruiter discovery is a later, separately consented capability. |

Ajiri's proposed distinction is transparent vacancy evidence, candidate control and
low-data mobile use. The reviewed pages do not establish that competitors lack these
properties. Do not compete on fabricated inventory, mass applications or invented
employer reviews. Salaries must remain undisclosed where reliable values are absent.

## Proposed release goals

| Priority | Goal and scope | Proposed acceptance target | Existing work to reuse |
|---|---|---|---|
| P0 | Release readiness and dependency security | Triage GitHub alert31/PR82 first; required checks, recovery proof and adequate measured next-backup reserve before each release | Existing CI, private backups and deployment preflight |
| P0 | Trusted inventory and source quality | Pilot target: at least50 genuinely eligible unique open roles,3 permitted independent channels and10 genuine employers;100% accepted deadline/source evidence; zero sampled closed/scam listings | AJ53 provenance, moderation and strict eligibility |
| P1 | Mobile discovery and explainable fit | Pilot target:8/10 explicitly consenting participants find a relevant current role within5minutes; explain skills and editable preferences; honest empty/unknown states | AJ39 search, existing70% alert threshold and mobile UI |
| P1 | Relevant, controlled notifications | Daily/weekly saved-search choices; verified current mailbox/consent; zero duplicate or ineligible handoffs in acceptance; working withdrawal/unsubscribe | AJ17/26/43 archived transport and shared ledger |
| P1 | Reviewed application journey | A candidate can review/approve exact documents, authorize one handoff or follow original external instructions, and see accurate status; no automatic uncertain retry | Existing CV/package review, authorization and AJ50 progress |
| P1 | Shortlist and follow-up | Owner-only saved roles and manual follow-up; clearly distinguish external actions, provider acceptance and confirmed delivery | Existing private owner resources and application progress |
| Release gate | Mobile accessibility, performance and truthful safety | Zero serious/critical axe findings plus manual keyboard/mobile review; no false malware-scan/qualification/placement claim | Existing browser/performance suite and AJ52 scanner boundary |

The inventory and usability numbers are suggested pilot gates to approve/refine,
not current counts or commitments. If genuine source access cannot meet the inventory
gate, narrow/postpone the pilot; never relabel unverified rows or relax freshness.

Pursue LCP<=2.5s, INP<=200ms and CLS<=0.1 at the75th percentile, following
[Google's Web Vitals guidance](https://web.dev/articles/vitals). Controlled lab
measurements remain separate from field results. Real-user measurement requires an
appropriate privacy basis/choice; this proposal does not activate AJ51 analytics.
Do not claim WCAG conformance or a field percentile from automated lab checks alone.

## Carryover and sequencing

All13 unfinished stories retain their actual status and move to the MVP2 backlog.
`MVP2` is an unreleased planning version without an invented release date.

| Group | Issues | Remaining acceptance / recommended position |
|---|---|---|
| Core inventory and safe discovery | AJ53,AJ42 | Genuine employer/source authority, accepted current deadlines and independently reviewed listings; public SEO only for eligible inventory |
| Core email and saved searches | AJ17,AJ26,AJ43 | Port to current main, recheck current consent/mailbox/eligibility and shared budgets, then separately verify controlled transport and bounded callers |
| Safety foundation | AJ52 | Actual private scanner hosting, signatures and fail-closed acceptance; content validation alone is not malware scanning |
| Certificates | AJ79 | Conditional later scope: scanner, storage capacity, privacy/retention and fresh additive migration; uploaded evidence does not certify qualifications |
| Infrastructure | AJ47,AJ48 | Conditional: use measured scale/reliability need to justify actual private storage/PostgreSQL or durable queue hosting; no synthetic-host acceptance |
| Analytics | AJ51 | Conditional: actual purpose, notice/legal/retention facts and independent choice before collection |
| Commercial work | AJ44,AJ45,AJ46 | Carry over, schedule last or later release; genuine merchant/offers/retention, authenticated settlement/reversal and paid-action acceptance before any charging |
| Historical Jira cleanup | AJ80 | Keep all23 Update histories intact; provenance-based reconciliation remains a proposal |

Recommended order: dependency/recovery readiness -> genuine inventory -> mobile
discovery and fit -> consented alerts -> reviewed applications and shortlist ->
controlled pilot. Scanner acceptance precedes any feature requiring scanned files.
Certificates/analytics/queue/PostgreSQL/payments are not automatic core commitments.
No feature switch, live send, data export/erasure, production migration or purchase
is authorized merely by placing an issue in this planning version.

## Integration and release discipline

Michael superseded the original branch recommendation on 11 November 2026:
`MVP2` is the integration branch, created from fetched reviewed `origin/main`
at `a8f11fd728aeb0fbe4ff5d62027b7c64712f8a66`. All MVP2 feature branches
start from the latest reviewed `MVP2` and their PRs target `MVP2`. Use focused
`codex/mvp2-<issue>-<feature>` branches, run pinned checks/full suites and all
required PR checks before integration. Release to `main` through a separate
checked PR when the integrated release is ready; integration is not deployment.

The archived stack predates released `jobs.0017_job_browsing_settings` and contains
another jobs.0017 plus dependent0018–0021 files. It must not be merged wholesale.
Plan new additive migrations against the deployed history; never rewrite applied
migrations or reverse populated data as routine rollback. Use fresh disposable
databases for migration tests. Source staging, migration and activation order remains.

See [branch recovery](../reports/MVP1_CLOSEOUT_2026-11-11.md) and
[archive manifest](../reports/BRANCH_ARCHIVE_2026-11-11.json). Historical PR71/73
discussion and tests remain readable after closure. Restore an archive only as
reference, then port the intended change to a fresh branch from main.

## Scope decisions for Michael

The six new Jira items are To Do proposals/readiness work, not delivered features:

| Jira | Proposed work |
|---|---|
| [AJ81](https://michaelmathenge.atlassian.net/browse/AJ-81) | Dependency/security alert intake, targeted PR82 review first |
| [AJ85](https://michaelmathenge.atlassian.net/browse/AJ-85) | Current-main integration, migration compatibility and measured recovery capacity |
| [AJ82](https://michaelmathenge.atlassian.net/browse/AJ-82) | Multi-source inventory quality and duplicate controls |
| [AJ83](https://michaelmathenge.atlassian.net/browse/AJ-83) | Mobile filters and explainable candidate-controlled matching |
| [AJ84](https://michaelmathenge.atlassian.net/browse/AJ-84) | Saved jobs and transparent follow-up, extending existing progress |
| [AJ86](https://michaelmathenge.atlassian.net/browse/AJ-86) | Bounded pilot, accessibility/performance and honest safety disclosures |

| Decision | Recommended default | Consequence |
|---|---|---|
| MVP2 objective | Trusted mobile discovery plus controlled applications | Inventory/quality gates lead; feature count is secondary. |
| Pilot inventory/validation targets |50eligible roles/3channels/10employers and8/10 usability participants, refine at planning | No launch claim when genuine supply or evidence is missing. |
| Carried infrastructure and commerce | Conditional/last | Existing code is preserved without forcing premature activation. |
| Delivery boundary | Explicit consent, exact review and one controlled handoff | No mass apply, inferred consent or automatic ambiguous retry. |
| Schedule and effort | Refine proposals before committing sprint dates/estimates | Suggested points are not delivery promises or capacity measurements. |
