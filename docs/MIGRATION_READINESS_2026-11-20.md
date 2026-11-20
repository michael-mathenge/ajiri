# Migration readiness and service decision -20November2026

This report distinguishes implemented source, actual rehearsals and missing live
acceptance. It supplements HOSTING_MIGRATION_PLAN_2026-11-16.md; preserve that dated
checkpoint. No service has been provisioned/purchased, agreement accepted, access
granted or real document transmitted to a proposed provider.

## Engineering position

| Package | Evidence | Remaining before its exit |
| --- | --- | --- |
| A: current outbox | PR125 merged into MVP2 as3b919b5 after all six exact-head checks. Actual Redis/Celery registered-task run passed three target types, nine hard crashes, ten eligibility/disabled cases, deduplication/reservations, lease contention and dead letters. | Fresh-resource combined recovery and actual hosted durability remain separate. |
| B: private storage | Source covers bounded local/pathless private workflows, exact identity cleanup, versioned journals, export and resumed object copying. Historical16November689-test/full and10-test HTTP emulator passes are retained. |20November changes require their final full-suite/CI results and updated emulator run, including partial historical-version cleanup and legacy document routes. |
| C: PostgreSQL | Alternate graph/model-state generation, bound native-query contract, literal folding and unchanged SQLite search regressions pass locally. | Actual empty-target bootstrap,27-case membership/ranking measurements, populated data import and forward migration rehearsal. |
| D: combined recovery | Recovery/cutover acceptance sequence is defined below; provider documentation refreshed. | Actual interruption and restoration across database, private objects, erasure ledger and worker/broker state in fresh isolated resources. |

The Docker engine cannot currently start:20November diagnostics reported
VirtualMachinePlatform disabled and no hypervisor, while firmware virtualization
was already enabled. Michael enabled the Windows feature successfully; restart
and Docker readiness remain necessary. This is an environment blocker, not proof
that the proposed PostgreSQL or object-store implementation has passed.

Production's last verified runtime remains e3e8f74, SQLite/private media, with
operational sending/publication/certificate/scanner/queue gates disabled. The
last measured recovery-plan headroom was3100474bytes on16November; it is not a
fresh20November capacity measurement. Dashboard expiry was last observed as
16December2026. Recheck both before any new production release. No new backup
deletion authority or continuing retention policy is assumed.

## Recommended arrangement and proposed budget

Keep one8GiB x86 Linux VM in Nuremberg for Django/PostgreSQL, supervised Redis/
Celery and Unix-socket ClamD, plus private B2 EU Central in Amsterdam for objects
and independently verified recovery copies. This is self-managed, with one main
compute failure domain; patching/monitoring/recovery ownership must be accepted.
Eight GiB is a starting rehearsal size, not measured production scanner capacity.

Proposed ceiling for the preferred offer: **EUR15/month compute, primary IPv4 and
host backups, plus USD1/month pilot object storage**, before tax/FX/overage. It is
not an approved spending limit or permission to order. CX33 is still unavailable
on the public product page; wait for an available quoted offer or return a separate
alternative for a decision. Do not substitute a more expensive tier automatically.

| Public option rechecked20November | Indicative monthly price | Eligibility/availability limitation |
| --- | --- | --- |
| Hetzner CX33,8GB/80GB | Indexed June compute EUR8.49 + primary IPv4 EUR0.50 +20% host backup EUR1.698 = **EUR10.688**, excluding B2/tax. | Public page says unavailable; direct price-adjustment fetch still404. An indexed tariff is not a current purchasable quote. |
| DigitalOcean Basic,8GiB/160GiB | Published USD48 +30% daily backup = **USD62.40**, excluding objects/tax. | Amsterdam/account/stock and processing eligibility need confirmation; outside the preferred budget and not selected. |
| PythonAnywhere Developer | Published **USD10**,5GB storage. | Potential temporary capacity bridge only; does not establish scanner privileges/resource isolation, PostgreSQL or a complete supervised stack. |
| Backblaze B2 | Published USD6.95/TB-month, first10GB free;20GB gross estimate **USD0.139** before allowance/rounding. | EU Central is selected at account creation; account region cannot subsequently be changed. Confirm current account tariff and processing terms. |

Hetzner's public primary IPv4 rate is cloud-specific EUR0.50/month; do not confuse
it with the dedicated-server IPv4 tariff. Its host backups cost20% of server price.
Host backups supplement consistent application recovery; they do not replace it.
B2 includes egress up to3x average stored data, then publishes USD0.01/GB overage.
No KES conversion, free-tier entitlement or combined-currency invoice is assumed.

## Processing, sizing and activation prerequisites

The proposed destinations are the approved German VM and private Amsterdam object/
recovery account. Signature downloads contact ClamAV infrastructure; documents
stay with the local scanning engine, not an external document-scanning vendor.
Provider eligibility, processor terms, cross-border handling, named operational
owner and privately entered restricted credentials remain decisions before use.
PostgreSQL, broker, scanner and storage management interfaces must remain private.

ClamAV publishes3GiB minimum/4GiB preferred container RAM and describes temporary
engine duplication during signature reload. Measure real signatures, reload peaks,
Django/PostgreSQL/worker contention and disk use together before selecting capacity.
Start scan concurrency at one. Keep input5MiB, scanner time/expansion bounds and
24-hour signature/verdict freshness. Missing/stale/unsupported/limited outcomes
remain quarantined. Legacy/restored files acquire no inferred clean verdict.

Private growth includes uploaded CVs, all immutable CV/application revisions,
certificate/quarantine objects, historical object versions and report-only orphans.
Certificate active quota alone permits20MiB per owner: ten owners add200MiB before
staging replacements, backups or transfer/restore copies. Measure PostgreSQL/WAL,
Redis persistence, signature download/reload space and at least two complete
recovery operations independently; do not size from current live media bytes alone.

## Combined recovery and cutover acceptance

1. In an isolated synthetic stack, stop/drain every writer and reconcile delivery
   states. Record one authority/cutoff, current graph/source manifest and shared
   receipt/budget identities. No old/new writer may run concurrently.
2. Capture consistent database data/schema, exact private object versions/hashes,
   independent signed erasure ledger and broker persistence. Verify every archive
   member/hash in a separate recovery location before creating restoration targets.
3. Inject interruption after database import, during object copying and before
   worker restoration. In fresh labelled resources, verify exact data/relationships,
   object bytes, graph state, quarantine and completed erasure evidence before writes.
4. Re-deliver the same immutable targets through the registered worker with captured
   transport. Accepted receipts must be reused; reserved/unknown states must stop
   for explicit reconciliation. Verify no extra handoff or shared reservation.
5. Record actual resources/timings, failures and restore receipt. A fresh-container
   simulation proves the procedure; it does not establish physical hosted disk-loss,
   regional disaster recovery or cloud-provider durability acceptance.
6. Only after a concrete service decision and separately reviewed bootstrap/ledger
   mapping: pause production web/writers, take fresh consistent recovery/off-server
   restoration, migrate/copy under one writer authority, apply reviewed migrations,
   then activate readers with all feature gates still off. Check HTTPS/assets,
   private owner/anonymous access, preserved permissions and exact files.
7. Resume ingestion/matching against only the chosen authority using reviewed host/
   endpoint configuration. Before any target writes, source-only rollback can use
   the consistent source. After target writes, stop and forward-recover or perform
   explicitly reviewed resynchronisation; never reopen a stale writable SQLite copy.
8. Activate scanner, private uploads and bounded workers separately after actual
   resource/recovery acceptance. Normal sending and genuine vacancy/participant
   acceptance remain independent. Retain recovery evidence; propose pruning separately.

## Official sources rechecked20November2026

- [Hetzner cost-optimised availability](https://www.hetzner.com/cloud/cost-optimized/)
- [Hetzner indexed June price adjustment](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/) (direct fetch unavailable)
- [Cloud primary IP pricing](https://docs.hetzner.com/cloud/servers/primary-ips/overview/)
- [Hetzner backup billing](https://docs.hetzner.com/cloud/billing/faq/)
- [DigitalOcean Droplet prices](https://www.digitalocean.com/pricing/droplets)
- [DigitalOcean backup prices](https://docs.digitalocean.com/products/backups/details/pricing/)
- [PythonAnywhere plans](https://www.pythonanywhere.com/pricing/)
- [B2 prices](https://www.backblaze.com/cloud-storage/pricing)
- [B2 data regions](https://www.backblaze.com/docs/cloud-storage-data-regions)
- [ClamAV resource/reload requirements](https://docs.clamav.net/manual/Installing/Docker.html)
