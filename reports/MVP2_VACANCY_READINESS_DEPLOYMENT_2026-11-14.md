# Vacancy-pilot readiness release — 14 November 2026

## Current checkpoint

Release PR109 passed all six exact-head checks on84394e1 and merged to main as
ef1c102ccf4f2d5c64353b7698a8fc4a7374b3e4. All six merged-main checks also passed.
That exact source was activated and independently verified over HTTPS at
14:45:04UTC on14November. Prior runtime/rollback source isc88da83; no schema or
dependency installation was required. Documentation-only follow-up merges do not
establish a newer activated runtime.

## Reviewed packages and actual validation

- PR105 c0f974f passed six checks; merged4eab005. Aggregate readiness now separates
  first1role/1employer inventory, larger50/10targets, safe mail configuration and
  required private evidence. Current onboarding procedure and blank private
  evidence template create no participant consent or real records.
- PR106675e7a1 passed six checks; merged387a0bf. Focused closed PR73 adapters were
  ported without replacing newer discovery/ownership/migration work. New normal
  application, match-alert and search email switches default off; shared ledger,
  final-handoff eligibility and no-uncertain-retry behavior preserved. A new test
  exposed/fixed programmatic batch-limit validation. No live scheduler or sends.
- PR107 final4a596a1 passed six checks; merged260521b. Scanner/hosting decision
  package only; no service purchase/provisioning, terms or real document transfer.
  Archived queue0018 collision and real-engine/target/durability gaps are explicit.
- PR108 source0973bff/build-last6ecb14b passed all six checks; merged84394e1.
  Correct public employer guide and defer private query-cache code/construction
  until a signed-in session. Per-session reset clears/cancels old private reads.
  JWT/interceptor/server permissions unchanged. No schema/dependency/CI changes.

Full backend results:594tests294.024s for readiness,608tests270.573s before source
integration,611tests297.040s for combined delivery,594tests311.032s for decision
baseline,611tests302.848s for guide baseline; each retained one existing platform
skip. Check/drift and Ruff passed. Node24.19 locked npmci/lint/build passed in each
package, audit0. After the cache correction bothlinters,177components28.21s and
11real Chromium journeys74.607s passed; network assertions prove private cache
chunk deferred until sign-in, and component tests cover cancellation/account
isolation. Manual phone/pilot acceptance is not inferred. Build47files exactly
matches dist; index SHA256
c1a069b2ec992fbb5714a2a7a017e01b0337ac0fdd33df9b2dd53aa3e9a42448.

## Retained performance failure and corrected Linux measurement

Initial PR1081ed83ed Linux43602973332 passed11journeys but failed login TBT251ms
against unchanged250msbudget. Register230ms passed; artifact14116813650 digest
395c5f20b562a1ec7a559e9321d373823cc65ab18bb436c58d72d495821d21c9 retained.
No unchanged metric rerun or relaxed budget. Product fix reduced main JS395.30kB
to362.34kB and removed unused private-cache initialization from public first load.

Actual corrected Linux43604274331, artifact14117487152 digest
c7c778917f0359305f59905a8294f7fc60a45f621a3df47cb2abf888ad293ba5:

| Median | Login | Register |
| --- | ---: | ---: |
| Performance |83|86|
| LCP ms |3933.49435|3783.36810|
| TBT ms |160|181|
| CLS |0.0996482599|0.0622485528|
| Initial transfer bytes |450236|447355|
| Trace retries |0|0|

All unchanged lab budgets passed. These measurements do not establish field p75,
manual-device accessibility, actual delivery or genuine participant acceptance.

## Recovery, capacity and activation prerequisites

Current runtime/account settings were read-only inspected11:56UTC and13:55UTC.
General account-security mail is actually enabled in account_security mode and
configuration validates; outside-employer onboarding/inbox remains unverified.
Posting/publication/searches/application-alert sending stay off; freshness stays on.
The three dormant new general transport environment flags were independently
parsed before staging and all false. Current provider credentials were not read
or printed. Dashboard expiry was rechecked as30November2026; no renewal clicked.

At13:55UTC usage461045760bytes with1MiBmargin; available75825152, next snapshot+
transfer+16MiBreserve plan73941075, remainder1884077. No further deletion approved
or performed. Release must recheck under paused/drained writers/web, and after
staging. Rollback is source-only toc88da83 with current rows/private files/receipts
and flags preserved. No migrations/dependency installation expected; verify actual
empty plan and all33 installed pins before activation.

Today's completed consistent recovery backup-20261114T103614144596Z-cea25a60
(source9676fc4) and private off-server/isolated restore were reverified read-only:
ZIP11206918bytes SHA256
1e8d8bf4496a3cf50c08b1202311ca58cc1f924c10810e84f9a6de93962c133f;
manifest SHA256020efbc59a5ba96a5e5fc22a2ddae4416eae7818b8def4571fea15e22547662b.
Exact ZIP/raw members, SQLite integrity, retained isolated DB hash/integrity and
all16restored private media hashes passed. This is re-verification of a completed
consistent snapshot/restore, not a new backup, download or unattended scheduler.
It may serve this release ONLY if a fresh paused comparison proves all45current
tables/columns/rows, three triggers,16files and absent erasure ledger unchanged.
If changed, stop staging, restore existing service/writers and obtain fresh
consistent recovery/capacity evidence. Never overwrite production with old data.

## Actual activation evidence

Both writer workflows were independently observed active, disabled and drained:
five run-state queries found no active/queued/requested/waiting/pending writer runs.
Web was reversibly disabled before comparison/staging. At14:38UTC all45current
tables/columns/row hashes, three triggers and16private media hashes matched the
completed14November recovery exactly; erasure ledger remained absent. Existing
account-security/freshness flags and all disabled gates were recorded. This actual
paused comparison qualified the reverified snapshot for reuse; no redundant new
snapshot/ZIP, new download or new unattended backup is claimed.

Clean sourcec88da83 fetched origin/main and asserted exactef1c102 before detached
checkout. Production release_preflight passed with expected migrations[] and
pip_install_requiredFalse. Index hash/47file inventory matched checked bytes.
check, makemigrations --check --dry-run and migrate --plan passed; MigrationExecutor
independently asserted an empty plan. No actual migrate or pip install ran.
All three newly parsed transport settings were asserted false before activation.

At14:39:29UTC post-staging capacity passed:461844480bytes used with margin,
75026432available,73941075required including next snapshot/transfer/16MiBreserve,
1085357remaining beyond the complete plan. A14:40:49read repeated that pass.
No additional file or backup deletion was approved or performed in this phase.

All33 installed production pins matched requirements-prod. Direct owner view
checks returned200 for jobs, CV draft, employer drafts, suggestions, dismissed
choices, saved jobs and applications. Last four counts0/0/0/1. Existing approved
private CV returned200 with bytes matching its stored SHA256, private/no-store;
anonymous equivalent401. Saved searches correctly403while disabled. These checks
used APIRequestFactory/force_authenticate, not a new browser/network owner login.
Actual CLI readiness reported configured_not_delivery_verified account mail,
first inventoryFalse,0roles/0employers, larger50/10shortfalls and external evidence
not_established_by_this_command. Match/search delivery commands were called only
after asserting their switches false and returned disabled/no changes; no send
was invoked. Application/alert sending and saved-search availability remain off.

At14:41UTC the post-staging/post-smoke preservation proof again matched all45tables,
three triggers,16files and flags exactly; no records or private files replaced.
A fresh Python process loading the actual WSGI file before reading settings also
confirmed general account-security configuration valid, freshness on and all eight
posting/public/search/normal sending switches false. This is fresh-process WSGI
configuration reproduction, not secret disclosure or live-worker introspection.

Web was re-enabled and explicitly reloaded; its reload control returned enabled.
Both writer workflows were restored and independently listed active. External
HTTPS health200/HSTSmax-age=604800, all47exact asset hashes including root index,
and three anonymous private endpoints returning401passed. Completion timestamp
2026-11-14T14:45:04.618376+00:00. Owner reads did not claim an outside-employer
onboarding, real delivery, provider inbox, participant consent or manual-phone result.
No manual ingestion, live normal sending, staff grant, service purchase/provisioning
or storage/queue/scanner activation occurred. Runtime is exactef1c102; source/data
rollback retains current rows, files, receipts and safety flags.

## Deployment receipt package gates and remaining work

On the release-equivalent source, actual receipt gates passed: check/drift,
611tests278.415s(one existing platform skip); Node24.19 locked npmci358/audit0,
lint/build1.60s and47-file exact regenerated/committed comparison. This package
changes documentation only; its own required CI/merge outcome is recorded in Jira.
All private off-server copies, completed restore, server snapshots/retained ZIPs
and unrelated files remain. Original checkout, stash and unrelated work preserved.

No participants are confirmed; first1genuine employer/1reviewed eligible role,
larger50/10inventory,8/10candidate usability, manual devices/field p75 and actual
normal-delivery acceptance remain unfinished. Scanner/certificate/storage/worker
stories retain the real engine/target/processing/quote/durability prerequisites;
this phase delivered the selected decision package only. All16unfinished non-Epic
stories retain their actual external gates. MVP2 is not declared complete.
