# Scanner and hosting decision package — 14 November 2026

Decision only, as Michael selected. No provisioning, purchase, account creation,
terms acceptance, credential entry, real file transfer or infrastructure activation.
Recommendation below is a future technical candidate, not a selected paid service.

## Measured baseline and growth

Production c88da83,11:56UTC read-only inspection: SQLite27877376bytes;16private
files335905bytes; account usage461045760bytes including1MiBmeasurement margin;
quota536870912bytes; available75825152bytes. Required next snapshot+transfer+16MiB
reserve73941075bytes; remainder1884077bytes. This narrow positive plan is not room
for a scanner or certificate growth. Recheck under a writer pause before release.
Web dashboard independently still shows expiry30November2026. No renewal was clicked.

The configured certificate design's20MiB/owner ceiling means10fully populated
owners add209715200bytes active evidence, already beyond current free capacity.
At least one old/new5MiBreplacement pair and quarantined candidates may coexist;
concurrency adds further transient space. With incompressible evidence, each
retained full snapshot and transfer ZIP can each add another approximately200MiB
for this10-owner scenario. These are planning calculations, not measured demand,
a retention policy or permission to prune. Keep runtime/DB/WAL/scan signatures,
quarantine, replacement, snapshot, download bundle and restore space separate.
The private erasure ledger must accompany recovery whenever present.

## Existing work to reuse; not live acceptance

Archive974dc6d contains profiles/scanner.py, certificate_scanning.py, certificates.py,
certificate views/tests, jobs/storage_copy.py and delivery_queue.py plus rehearsals.
The scanner is a bounded5MiB local ClamD adapter (Unix socket or loopback only),
10second overall deadline, explicit engine allowlist, UTC/signature attestations,
and24hour scan/signature freshness checks. Current deployed code has no real
scanner. Fake/socket-fixture tests are not proof against an installed engine.
Certificates remain inactive; existing text CV certifications are separate.
The archived scanner caller covers certificate evidence, not every upload path.
Inventory CV imports and any other user upload route before claiming AJ52 complete;
each relevant path needs the same fail-closed quarantine boundary.

The archive's jobs0018_durable_delivery_queue conflicts numerically with deployed
jobs0018_original_employer_submission and must NEVER be copied/applied wholesale.
Review schema dependencies and issue a new additive migration after current leaves
if later integrating. Preserve AUTH_USER_MODEL and populated migration history.
Storage-copy journals and broker-crash rehearsals do not establish a real private
S3 driver, historical PostgreSQL bootstrap/search or hosted broker durability.

## Options, prices and eligibility

Prices checked14November2026; taxes, FX, overage, account verification and regional
availability remain unverified until a specific quote/account decision.

| Arrangement | Current published cost basis | Assessment |
| --- | --- | --- |
| Existing PythonAnywhere free | $0,512MBstorage; no scheduled/always-on tasks in current plan table | Keep present pilot-readiness web release, SQLite/private media and external writer workflows. Insufficient scanner/certificate space; no hosted-worker claim. |
| PythonAnywhere Developer/custom plus separate scanner host | Developer$10/month with5GB and1always-on task; custom/PostgreSQL extra quote | Capacity bridge only. A remote ClamD connection is incompatible with the archived loopback-only adapter. Would require a separately reviewed authenticated gateway/processing destination; do not expose ClamD TCP or assume one task runs all services durably. |
| Self-managed EU VM plus private object storage (recommended future target) | Indexed official Hetzner June2026 table lists CX33EUR8.49/month excluding IPv4; primaryIPv4EUR0.50/month; optional host backups20%of server price. Backblaze B2 starts$6.95/TB-month | One8GiB-class x86 Linux node for a bounded rehearsal, local scanner, PostgreSQL and supervised workers; private B2 EU Central objects/backups. Account/stock and actual checkout quote required; no HA guarantee. |

The official Hetzner price-adjustment search result is indexed but its page returned
404 during direct fetch. EUR8.49 is therefore an indicative indexed rate, not a
firm purchasable quote. Illustrative VM+IPv4+20%backup arithmetic is EUR10.688/month
before tax, plus B2 usage/egress and operator time;20GB at the published B2 rate is
about$0.139/month before free allowance/tax/overage. Do not combine currencies or
promise this bill. Requote before any purchase; if unavailable, return the concrete
replacement quote to Michael rather than silently choosing another instance.

ClamAV's official minimum recommends3GiB+RAM and5GiBfree disk for the scanner
alone, with additional resources for colocated applications. An8GiBcandidate is
an engineering starting point, not measured capacity approval. Bound scan concurrency
at1for rehearsal; measure peak during signature reload plus DB/web/worker load.
If peak/exhaustion tests fail, propose a larger quoted node or separate scanner;
never disable scanning or use swap as evidence that capacity passed.

## Recommended architecture and processing destinations

Keep current PythonAnywhere production until synthetic rehearsal and the concrete
service decision pass. Future candidate: a Hetzner EU-central Linux VM in Nuremberg
(nbg1, subject to stock) serving Django through HTTPS, with local Unix-socket ClamD,
PostgreSQL, a durable Redis/Celery worker and a database-backed delivery outbox.
Use supervised processes, restricted service identities and a non-public DB/broker;
no direct Internet access to ClamD. This colocated node is a single failure domain,
so it is suitable only for a bounded initial service after explicit acceptance.

Private quarantine remains local to that host, inaccessible to web download until
the stored bytes/hash and a current clean verdict agree. Approved private objects
and encrypted application-consistent backups are proposed for Backblaze B2 EU
Central (Amsterdam). Region is chosen at account creation and cannot be changed
on that account. No public buckets/CDN/sharing links. Owner-authorised application
proxy downloads preserve no-store/ownership and verify bytes; access to objects is
least privilege. Recheck provider eligibility, terms/processing facts and transfer
requirements before any real personal data moves. No malware vendor upload service
is proposed. Freshclam contacts signature distribution endpoints for definitions;
user documents stay on the chosen host until explicitly approved private storage.

## Safety, legacy files and operations

- Pin a supported engine after real compatibility tests; freshclam updates and an
  observed UTC clock are prerequisites. Reject unavailable, stale/future signature,
  unsupported engine, timeout, malformed/oversized and interrupted scan outcomes.
- Retain the archive's24hour maximum verdict/signature age. Limit archive expansion,
  recursion, memory, CPU and stream size; hitting a bound is unavailable/quarantine,
  not clean. A clean verdict does not establish document authenticity or safety.
- No retroactive scanned claim for existing CV/application bytes. Preserve immutable
  originals and completed documents. Review a separate inventory/re-scan policy
  before legacy download behavior changes; do not silently relabel or erase them.
- Poll durable outbox/leases and reconcile provider receipts. Broker restoration
  or worker redelivery never repeats uncertain external IO. Stop/reconcile a lost
  lease; retain dead-letter/unknown records and require an explicit next action.
  Future broker persistence must survive restart (AOF policy plus outbox recovery);
  Celery acknowledgment/redelivery settings alone cannot guarantee exactly-once
  external effects. Rehearse process kill and full host/disk loss independently.
- Alerts: scan/update failures, stale signatures, disk/reserve exhaustion, DB backup
  failure, restore failure, worker heartbeat/lease age and unknown handoffs. Do not
  put mailbox/file contents or credentials into logs or public health endpoints.

## Staged future implementation and acceptance gates

1. Michael approves a specific service quote, processing destinations, operational
   ownership and budget. Credentials privately entered; no purchase by this phase.
2. Synthetic-only target: install reviewed runtime/engine, test actual clean/EICAR,
   stale signatures, reload peak RAM, resource bounds, outages and owner isolation.
   Verify no public scanner/DB/broker exposure and independent backup restoration.
3. Rebase inactive certificate/outbox schema additively against current migration
   leaves. Complete quotas/replacement/scan races/export/erasure/private recovery.
4. Rehearse historical PostgreSQL bootstrap, all tables/relationships/search triggers
   or reviewed equivalent search, private object bytes/ownership, interrupted copy
   journals and process/host-loss recovery. One authoritative writer throughout.
5. Fresh private recovery, writer pause, final delta/hash verification, apply reviewed
   migrations, then controlled code/storage activation. After new target writes,
   never fall back to stale SQLite; require reconciled reverse transfer if needed.
6. Run a consented bounded live acceptance only after real prerequisites exist.
   Rollback disables new uploads/workers/publication as appropriate while preserving
   freshness, newer data, private bytes, erasure ledger and all uncertain receipts.

## Primary sources

- [PythonAnywhere plans](https://www.pythonanywhere.com/pricing/) and
  [PostgreSQL eligibility](https://help.pythonanywhere.com/pages/Postgres).
- [ClamAV requirements](https://docs.clamav.net/) and
  [scanner networking](https://docs.clamav.net/manual/Usage/Scanning.html).
- [Hetzner indexed price adjustment](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/),
  [IPv4 price](https://docs.hetzner.com/cloud/servers/primary-ips/overview/),
  [billing/backup price](https://docs.hetzner.com/cloud/billing/faq/) and
  [locations](https://docs.hetzner.com/cloud/general/locations/).
- [Backblaze pricing](https://www.backblaze.com/cloud-storage/pricing),
  [data regions](https://www.backblaze.com/docs/cloud-storage-data-regions) and
  [security](https://www.backblaze.com/docs/cloud-storage-security).

- [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)
  and [Celery acknowledgment/redelivery](https://docs.celeryq.dev/en/stable/userguide/tasks.html).

These sources support published product facts. Architecture, sizing, estimates and
ordering are engineering proposals/inferences, not measured hosted acceptance.
