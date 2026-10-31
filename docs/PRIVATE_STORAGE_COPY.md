# Verified private copy/recovery — AJ-47 remains blocked for cutover

The new copy service performs real Django Storage reads/writes with bounded streamed
size/SHA-256 checks, exact names and a private checksummed journal. It does not select
a provider, discover credentials, change DATABASES/STORAGES, migrate production,
delete bytes or activate a runtime storage switch. Current SQLite/private media stay
authoritative.

It requires explicit paused-writer and private/exclusive-target attestations. These
flags do not prove a real target is private or quiescent; actual operator evidence
is still required. Local source/target trees must be independent/non-overlapping,
without links/junctions/hard links, and the journal stays outside both data trees.
Only reviewed relative private-document roots are accepted; no .env files, URLs or
traversal references. Limits are 10,000 files, 20 MiB/file and 512 MiB/snapshot;
unsupported/oversized entries abort for scoped review rather than being skipped.

The journal is exclusive across processes and fsynced before target writes. Its
checksum detects corruption, not malicious forgery by an administrator. It binds
the snapshot and source/target namespace fingerprints. A target write is claimed
before I/O. Complete matching bytes after an uncertain response can be verified on
resume without repeating the write; absent, partial, renamed or different targets
remain blocked. No automatic retry/overwrite/delete is permitted. Preserve partial
targets/journals; a new isolated namespace after review avoids blindly replaying an
uncertain write. Source mutation prevents completion. Physical power-loss durability
still requires actual storage-host evidence.

rehearse_private_storage takes --source-dir, --target-dir, --journal,
--writers-paused and --target-private, with optional --restore-dir for a third
isolated filesystem store. It inventories all actual FileField references, including
certificate quarantine, verifies the reference snapshot stayed stable, and reports
only counts/hashes. Keep journals private/off-server and out of Git. The file-copy
manifest does not establish database/schema correctness, semantic document approval,
off-server privacy or production restoration. Verify the database canonical rows,
FK/UUID identities, owner downloads and actual target separately.

The library can use a reviewed Django Storage implementation. A remote driver is
rejected unless it supplies an explicit private namespace identity and reviewed
single-attempt-write semantics. No S3/vendor SDK, credentials, legal agreement,
bucket privacy/encryption proof or real object-store integration was invented.
Filesystem copy/restore tests are not object-store acceptance.

The existing jobs.0011 migration explicitly rejects non-SQLite vendors. Preserve
that historical source; do not silently fake production migration state. Final
choice is required between a separately reviewed PostgreSQL bootstrap lineage and
a reviewed replacement/squash strategy, with genuine keyword-search parity and an
actual eligible target. Previous synthetic PostgreSQL schema-copy evidence does
not prove normal historical migrations work on PostgreSQL. AJ-47 stays blocked for
those concrete facts/decisions and actual object-store/host acceptance.

Rollback abandons the unused target and retains source, partial copies, journals and
backups. No pruning policy is implied. Once a future target accepts new writes,
never fall back to stale SQLite/filesystem bytes: halt writers and execute a verified
reverse reconciliation plan. No production cutover or migration was attempted here.
