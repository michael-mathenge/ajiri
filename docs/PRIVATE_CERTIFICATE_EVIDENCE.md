# Concurrent cleanup correction - 16 November 2026

Release PR122's Python3.14 run exposed a losing upload leaving its staged file
when a conservative post-error database read met a SQLite writer lock. The quota
remained five records; the sixth file was an unreferenced staged UUID. Cleanup
now distinguishes failure before any pointer can commit from an uncertain commit:
known rollback cleans only this request's file without another contested read;
after a commit attempt, verification or conservative retention still protects
potentially committed bytes. The strict concurrent record/file assertions remain.

## Private evidence package and operator procedure

# Private certificate backend and scanner integration

AJ-52/AJ-79 implementation package, 16 November 2026. Baseline: reviewed main
276f37ae05285c7fbe978994f6bf521add99d5fe. This focused port reuses archive
974dc6d without merging its older jobs models/migrations, payment/analytics code,
account export omissions or obsolete administration settings. Jobs0022 remains
intact; the only new migration is profiles0008 after profiles0007.

## Behaviour and limits

The backend supports optional owner-only PDF evidence on an already saved CV
certification. Default flags remain false: CERTIFICATE_EVIDENCE_ENABLED and
MALWARE_SCANNING_ENABLED. No UI, auto-upload, automatic scan job, scheduler,
external scanner or employer sharing is activated. Certificate text and immutable
approved CV/application bytes remain independent.

Additive owner routes (also under the existing /api/v1 alias):

- GET /api/profiles/me/certificates/: at most five safe metadata records.
- PUT /api/profiles/me/certificates/<certification_uuid>/: explicit multipart
  document and expected_revision; replacement also requires expected_id/hash.
- GET that detail route: attachment only after exact-byte integrity, a current
  clean verdict, supported engine and signatures within 24 hours.
- DELETE that detail route: JSON expected_revision/id/hash and confirm=true.

Anonymous access is denied; other owners receive no existence disclosure.
Responses are private/no-store; downloads use nosniff and neutral certificate.pdf.
No storage path/original name/public URL is returned. PDF validation is bounded
at 5 MiB, with five active files/20 MiB per owner including quarantine. A
conditional workspace write serializes quota/membership checks on SQLite. Uploads
never alter the workspace revision or immutable approval; draft entry removal
requires explicit evidence removal first.

Replacements stage a fresh UUID, swap metadata atomically and clean old bytes only
after commit. An uncertain commit or post-commit cleanup failure must preserve
potentially referenced new bytes. Reconcile metadata after an uncertain response;
never replay a mutation blindly. Orphan audit is report-only, including failed
cleanup. Verified export/erasure inventories and private relocation now include
evidence; full private-media backups already include quarantine bytes.

## Scanner and operator commands

The optional real adapter uses only Unix sockets or loopback ClamD, at most 5 MiB,
a ten-second overall deadline, reviewed bounds marker, confirmed UTC and an
explicit supported engine allowlist. It checks version/signature freshness before
transferring document bytes. Missing, malformed, stale, timed out, limit or encrypted
outcomes never become clean and never trigger automatic retries. Enabling scanning
also checks legacy uploaded CV bytes before download and new CV uploads before
storage. Existing generated approvals are not overwritten or retrospectively
labelled scanned. Review legacy/restored-file handling before enabling this gate.

Run with the deployed private environment and current settings:

```text
python manage.py private_upload_readiness
python manage.py private_upload_readiness --probe
python manage.py audit_certificate_evidence
python manage.py scan_certificate_evidence --evidence-id <UUID>
python manage.py scan_certificate_evidence --evidence-id <UUID> --recover-stalled
```

Readiness reports aggregate counts/setting states only. The optional probe sends a
version request to the configured local daemon; no document is transferred.
Configuration/probe success does not establish capacity, terms, signatures under
real load, independent recovery or live acceptance. The audit reads integrity and
orphan counts without changing anything. Scan requires an explicit UUID; stalled
claims older than one minute require explicit recovery. Settlement is bound to the
same UUID/path/hash and claim timestamp; a replaced/deleted row or newer claim
cannot be settled by an old worker. Disabled scanning changes nothing. All handler
arguments are validated for programmatic calls as well as CLI parsing.

## Deployment and rollback

1. Remeasure account capacity and reserve for snapshot, transfer, staging and
   recovery. No backup deletion authority is implied by cache cleanup.
2. Pause both writer workflows and web, verify a fresh consistent private snapshot,
   exact off-server archive/member hashes and an isolated database/media restore.
   Keep the independent erasure ledger when present.
3. With old code still active only outside the paused window, stage exactly
   profiles/certificate_paths.py and profiles/migrations/0008_certificate_evidence.py
   from the checked release. The migration helper deliberately imports no new
   runtime model. Apply reviewed migration before activating any new request code.
4. Compare every pre-existing table/row/relationship, three search triggers and
   private file hash. Only the empty evidence table plus migration/content-type/
   permission catalogue metadata may be added; no user/group grants.
5. Activate the checked source, keep both new gates and all existing sending,
   publication, saved-search and queue gates disabled, with freshness still on.
   Verify HTTPS/exact 47 assets, private owner/anonymous access, readiness and
   no evidence rows or new provider handoffs. Restore and verify web and writers.
6. Record actual source, migration, capacity, restore, CI and deployed evidence
   separately. If any gate fails, keep writers safe and use the reviewed rollback.

Rollback retains profiles0008, evidence/quarantine files, delivery receipts and
all newer data. Roll source back to the verified baseline with new gates off;
do not reverse a populated migration or restore stale data. Because old code
does not inventory certificates for erasure, disable verified erasure operations
under that older source until the reviewed forward code is restored. No erasure
is authorised as part of deployment.

Real host/signatures/resource tests, upload activation, manual device UI work and
live private recovery with genuine evidence remain AJ-52/AJ-79 acceptance gates.
See HOSTING_MIGRATION_PLAN_2026-11-16.md for the priced service decision. No employer,
reviewer or candidate participants are available yet, as Michael confirmed today.
