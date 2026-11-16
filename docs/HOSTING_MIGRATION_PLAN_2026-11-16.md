# Costed hosting migration proposal - 16 November 2026

Michael requested a fresh PythonAnywhere audit, safe unused-space cleanup and an
online cost comparison. This is a proposal, not an order, provisioned service,
processing agreement or authorisation to move personal documents. Keep the
14 November decision package as historical evidence.

## Observed account and cleanup

Read-only console inspection confirmed runtime
276f37ae05285c7fbe978994f6bf521add99d5fe and a clean checkout. The web dashboard
still displayed expiry **30 November 2026**; no renewal or plan change was clicked.
Account allocation before cleanup: 457,912,320 bytes, including 263,495,680 bytes
of private recovery directories, 121,692,160 bytes of virtual environments and
59,105,280 bytes of checkout. No frontend node_modules or pytest cache existed.

Removed only verified generated pip downloads and virtualenv seed caches:
449 files, 11,173,574 content bytes, **12,480,512 allocated bytes reclaimed**.
The installed environment remained usable (its pip version/path verified), source
HEAD/status stayed unchanged, and the complete backup/private-media file size and
mtime inventories matched before/after. No backup, private file, installed package,
Git configuration, authentication cache or user work was removed.
Measured account allocation afterward: **445,431,808 bytes**; approximately
87.2 MiB remains before measurement margin and release reserve. This is temporary
headroom, not scanner capacity or a continuing backup-pruning policy. A fresh
consistent snapshot, off-server hashes and isolated restore are still required
before deploying this package. Repeat capacity measurement under the writer pause.

## Recommendation and priced alternatives

Prefer a single **8 GiB x86 Linux VM in Nuremberg, Germany**, with PostgreSQL,
Django, a supervised worker and local Unix-socket ClamD; use private Backblaze B2
EU Central (Amsterdam) for objects and encrypted recovery copies. This follows
the existing recommendation while avoiding several managed-service minimum fees.
It is self-managed and has one failure domain; Michael must accept ongoing
patching, monitoring and recovery responsibility. Eight GiB is a rehearsal starting
point, not proven capacity. Measure signature reload plus application load first.

| Option | Indicative monthly cost before tax/FX/overage | Decision |
| --- | --- | --- |
| PythonAnywhere Developer | $10, 5 GB disk, one always-on task | Useful short-term capacity bridge; does not establish local scanner privileges or enough separately supervised services. PostgreSQL/custom requirements need a quote. |
| Hetzner CX33, 8 GB/80 GB, EU | Indexed official June rate EUR8.49 + EUR0.50 IPv4 + EUR1.698 host backup = **EUR10.688**, plus B2 usage | Preferred price target **only if stock and a current quote are confirmed**. Public cost-optimized page currently says unavailable; not a purchasable offer today. |
| Hetzner regular-performance CPX32 | Indexed official June rate EUR35.49 + EUR0.50 IPv4 + EUR7.098 backup = **EUR43.088**, plus B2 | More costly fallback; exact regional stock/quote not established. Return quote for decision, do not silently substitute. |
| DigitalOcean basic 8 GiB/160 GiB | $48 + 30% daily host backup = **$62.40**, plus object storage | Clearer published fallback; region/account eligibility and stock still need checking. Weekly backup option is $57.60 total but does not replace daily application recovery. |

The Hetzner price-adjustment page remains indexed but direct retrieval returned
404. Treat its amounts as estimates; its dynamic plan page did not expose a firm
current price. Do not buy against this table. Host snapshots are an extra recovery
layer, never a substitute for consistent database/object backups and restore tests.

B2 currently starts at $6.95/TB-month, first 10 GB free, with included egress up to
three times average stored data; extra egress is $0.01/GB. For 20 GB held all month,
the conservative gross storage estimate is $0.139 (about $0.0695 after 10 GB free),
excluding request/egress/tax effects. Recheck the actual account tariff and rounding.
R2 Standard is an alternative: first 10 GB free, then $0.015/GB-month, with free
egress and request allowances; 20 GB is about $0.15 after its storage allowance.
Use an explicit EU jurisdiction for R2 if selected; a location hint alone is not
a binding region. B2's region is chosen at account creation and cannot be changed.
No currency conversion or combined EUR/USD invoice is assumed.

## Processing, resource and recovery requirements

Documents would move only to the approved German VM and private Amsterdam B2
account; signature downloads contact ClamAV distribution services, not an external
document scanning vendor. Review terms, processor roles, cross-border handling,
account eligibility and restricted credentials before personal data moves. Michael
enters credentials privately. Never make the bucket, ClamD, PostgreSQL or broker
public. Preserve authenticated proxy downloads, integrity and no-store behaviour.

ClamAV documents 3 GiB minimum/4 GiB preferred container RAM; signature reloads
temporarily duplicate engine memory. Start scan concurrency at one, cap input at
5 MiB, configure expansion/recursion/time limits and measure peak resource use.
Missing/old signatures, unsupported engines, limits and outages quarantine/fail
closed. Maximum signature and verdict age stays 24 hours. No legacy CV or restored
file acquires a clean verdict automatically; preserve immutable approvals and
reconcile a separately reviewed legacy scan policy before enabling enforcement.

One fully populated certificate owner can add 20 MiB; ten add 200 MiB, before
replacement overlap, backups and transfer/restore copies. Budget disk independently
for PostgreSQL/WAL, Redis persistence, quarantine, clean files, signatures and
at least two recovery operations. Redis persistence alone does not establish
durable external effects: the outbox and authoritative delivery receipts must
reconcile unknown handoffs and host-loss restoration before any retry.

## Staged migration, with one authoritative writer

1. Select an available quoted VM/region and storage account, spending ceiling,
   processing terms and named operational owner. No provisioning before that decision.
2. Rehearse synthetic data only: exact runtime pins, network isolation, engine
   and signature refresh/outage/limit tests, peak RAM/disk, worker restart and
   host-loss restoration. Retain the desktop Docker lesson and existing resources.
3. Complete historical SQLite-to-PostgreSQL bootstrap, sequences, relationships,
   migrations and search equivalence (three SQLite triggers need a reviewed
   PostgreSQL equivalent). Compare counts/values and exact private hashes.
4. Rehearse resumable private-object copying, missing/conflicting objects,
   interrupted cutover and independent off-server recovery. Keep quarantine
   inaccessible and preserve the independent erasure ledger when present.
5. Pause web and both ingestion workflows, drain/reconcile deliveries, take a
   consistent fresh private snapshot and verify an isolated restore. Copy once;
   compare all rows/relationships and object hashes before switching readers.
6. Apply reviewed additive migrations, activate the new host with all sending,
   publication, certificate and queue gates still off, verify HTTPS/exact assets,
   owner/private access and rollback, then restore writer workflows against only
   the chosen authority. Never fall back to a stale writable SQLite copy.
7. Activate scanner, uploads and a bounded worker separately only after real
   resource/recovery acceptance; normal sending and genuine vacancy acceptance
   remain separate gates. Retain old recovery copies; propose retention separately.

## Official sources checked 16 November 2026

- [PythonAnywhere plans](https://www.pythonanywhere.com/pricing/)
- [PythonAnywhere always-on tasks](https://help.pythonanywhere.com/pages/AlwaysOnTasks/)
- [Hetzner indexed June price adjustment](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/) (direct fetch unavailable)
- [Hetzner cost-optimized plans and availability](https://www.hetzner.com/cloud/cost-optimized/)
- [Hetzner IP pricing](https://docs.hetzner.com/general/infrastructure-and-availability/ipv4-pricing/)
- [Hetzner backup billing](https://docs.hetzner.com/cloud/billing/faq/)
- [DigitalOcean Droplet pricing](https://www.digitalocean.com/pricing/droplets)
- [DigitalOcean backup pricing](https://www.digitalocean.com/products/backups)
- [B2 pricing](https://www.backblaze.com/cloud-storage/pricing)
- [B2 data regions](https://www.backblaze.com/docs/cloud-storage-data-regions)
- [R2 pricing](https://developers.cloudflare.com/r2/pricing/)
- [R2 jurisdiction](https://developers.cloudflare.com/r2/reference/data-location/)
- [ClamAV resource guidance](https://docs.clamav.net/manual/Installing/Docker.html)
