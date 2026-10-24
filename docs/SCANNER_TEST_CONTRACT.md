# Upload scanning: offline requirements and test contract (AJ-52)

This is a synthetic memory-quarantine integration, not a malware engine, physical
private storage or production protection. No existing upload/download endpoint has
changed. Existing uploads remain content-validated, not malware-scanned. No new
file is labelled safe in the application. No dependency, service, account, endpoint,
background worker, schema migration or private-file transfer is introduced.

The fixture first uses the existing bounded CV content validator: supported PDF,
DOC and DOCX, 5MiB/file and existing ZIP-member/expansion checks. Passing those checks
is not a malware verdict. Files receive opaque fixture IDs and start pending;
owner-only reads are blocked until an explicit fake clean result matches the exact
revision/hash. Infected, unavailable, malformed and timeout results stay blocked.
Only the fixture scanner is accepted; its fixture-only engine label is not an
actual signature database version. No real malware or antivirus test signature is
created, and no private production document is used.

Replacement creates a new pending revision; logical removal prevents future reads.
An in-flight old scan cannot release replacement or removed bytes. A client cannot
assert clean. Each operation rechecks synthetic ownership and revision. Independent
owner authentication, durable concurrent transactions, real file permissions,
resource limits, scanner deadline enforcement and worker recovery remain required
for a production adapter. This memory fixture loses evidence on process exit and
is not a durable audit, backup or retention system. Already downloaded bytes cannot
be recalled. No actual retention deletion is implemented.

## Before activation

Select an eligible scanner/host and deployment model, review its engine and
signature-update guarantees, failure behaviour, bounded CPU/memory/archive limits,
timeouts and protected quarantine/clean-storage separation. The current free WSGI
host does not itself prove a scanner or durable worker is available. Do not install
or provision one without the specific approved target. If external scanning is
chosen, the processing destination, actual file-transfer authorization, retention,
geography/onward processing and legal/privacy terms are prerequisites; never
silently upload private CVs/certificates to a vendor.

Propose additive scan records with owner, opaque file identity, immutable hash,
revision/state, engine/signature version and scan/result times. Bind every download,
attachment and replacement to current trusted evidence at its final read boundary.
Quarantine must never be under public media mappings. Initial unavailable/unknown
outcomes fail closed, with bounded explicit retry/reconciliation, not automatic
clean fallback. Atomic handoff must recheck owner/hash/revision after scanner I/O.
A clean result is evidence from a particular engine/time, not a guarantee a document
cannot harm a viewer. Keep existing structural checks as a separate defence.

Before live enforcement, reconcile every existing servable upload and approved
snapshot: never silently label historical files clean or rewrite immutable bytes.
Require explicit policy for legacy unscanned files, unavailable scanning, owner
removal, backups and restored scan evidence. Restoring a file cannot automatically
restore trust in an obsolete engine/version. Preserve erasure/recovery ledgers and
approved retention rules. Rollback closes new uploads/protected delivery while
preserving quarantine and later decisions; never restore an old DB over new writes
or silently bypass scanning by falling back to old routes. Live schema/activation
and actual scanning remain unimplemented until these prerequisites are resolved.

## Verification

Eight focused synthetic tests passed0.056s; Ruff passed. They cover owner isolation,
bounded format checks, pending/clean/infected/unavailable results, wrong hashes or
engine labels, timeout, replacement/removal races, no client clean assertion and no
resurrection of a removed fixture. Full467 Django tests passed329.007s (one known platform skip); system/migration-drift,
Ruff and strict schema checks passed. Node24.19 locked install audited364/zero
findings, lint/ESLint and build2.08s passed; source/runner and all36 committed build
files matched. Frontend source is unchanged; earlier141 components are historical
regression evidence, not a new package run. Required remote CI remains pending.
AJ52 stays In Progress for real scanner/storage integration and live acceptance.
