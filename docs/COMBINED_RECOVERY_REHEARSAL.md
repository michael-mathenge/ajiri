# Combined synthetic recovery

This operator joins the current outbox, alternate PostgreSQL bootstrap, pathless
private-storage boundary and signed erasure ledger in one recovery procedure.
It creates independent PostgreSQL 17.12, Redis, HTTP S3 emulator and application
containers for the source and target. The source containers are verified stopped
before the target stack is created, and checked again before target worker startup.
No production migration history, settings, worker, producer or schedule is changed.

## Reproduction

Docker Desktop's Linux engine must already be running. From the repository root,
use Python and the approved private-free context exporter:

```powershell
python scripts/prepare_combined_recovery.py
```

Use the exact new directory printed by that command; never build using the whole
checkout or an environment/data folder:

```powershell
docker build -t ajiri-combined-recovery:20261120 <printed-context-directory>
python scripts/run_combined_recovery.py --synthetic-only
```

Expected: source checkpoint, three interruption boundaries (`database`, `copy`,
`ready`), then `AJIRI_COMBINED_RECOVERY_RESULT` and an artifact directory. Every
phase is a new process. Exit 72/73/74 is expected only at its matching boundary;
the operator rejects other exit codes. The final operator must exit zero before
claiming success. Guard/unit tests run with:

```powershell
python -m unittest discover -s scripts/tests
```

The driver uses no host bind mounts, published ports or Docker socket inside a
container. PostgreSQL owns a network-none namespace; its own broker, emulator and
application share only that private namespace. Every container has a one-CPU,
512 MiB limit and bounded tmpfs areas. The app/worker runs as uid/gid 10001. Only
new invocation-labelled resources may be stopped. Existing resources, Git work,
private files and backups are preserved. Stopped lab containers and synthetic
artifacts remain for review; there is no general Docker prune operation.

## Evidence contract

The source generates alternate migrations in a new independent package and applies
them normally on an empty PostgreSQL database. It retains the actual graph and
recorder. Three independently authorised synthetic targets (application, alert,
saved-search window) complete through the registered worker and captured transport.
A hard crash during a fourth handoff leaves its receipt unresolved; lease recovery
must require reconciliation. A fifth message reaches Redis before publication
confirmation is lost; a second publish must remain unchanged.

Source workers stop before consistent pg_dump/RDB/object snapshots. The retained
synthetic archive includes five private objects, approved package hashes, exact
model/recorder/sequence fingerprints, captured handoff markers and a completed
format-2 signed erasure journal. A different synthetic owner's rows and all captured
object versions were erased before that checkpoint. No real erasure request or
legal attestation is inferred from these fixture-only command options.

Fresh target restoration first imports the database while gates remain off.
Premature worker startup is refused. A second process copies exactly one object
and stops; a third resumes using that verified object, verifies all five hashes,
restores the signed ledger and checks private owner downloads and cross-owner
denials. An older prepared journal must fail readiness. Original source object
versions must fail reads against the fresh store; no stale clean verdict is inferred.

Filesystem restoration creates new inode/timestamp identities. The lab explicitly
compares the retained key/size/hash inventory before obtaining new bounded read
identities. New target object identities are recorded separately. This is not an
authorisation to rewrite pending erasure journals or reuse old provider identities:
unresolved journals require a reviewed identity mapping before any real cutover.

Only after all prerequisites and source-stopped verification does a new target
worker consume restored messages. The original four receipts remain byte-for-byte
equivalent as canonical rows. Accepted targets produce no new handoff, the unknown
handoff stays reconciliable, and the already-published fifth target is consumed
once without republishing. One new sentinel proves queue progress. Final totals
must be six captured handoffs and six shared reservations, with zero duplicates
and zero real provider calls. Broker queued/unacked records must drain.

## Verified run - 20 November 2026

The complete eight-container source/target run passed in 90.572 seconds, excluding
image build and final container shutdown. All three interruption boundaries passed;
four original receipts remained unchanged; six captured handoffs matched six global
reservations; the unknown handoff still required reconciliation; queued/unacked
broker records drained. There were zero duplicate handoffs, blind republications
or real provider calls. All source resources were stopped before target creation.

Artifacts retained in the ignored local verification area:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| PostgreSQL dump | 165601 | `6faddce7034856ac66ab301a673ef35daf59542ce2c41f4239ee9eaeb9ded413` |
| Broker RDB | 2768 | `cb2bc0d6e2f231b976c198515b0d119a960fd9be5f54dca3c5545d2b42195c26` |
| Graph/private bytes/ledger state ZIP | 120232 | `9c6025bde7fa71c1bc568ef12965b8c163de8213110eb1965cc18b144a8287e5` |

Source point samples were PostgreSQL71.6MiB, Redis7.02MiB, emulator72.59MiB and
idle application11.23MiB. Target samples were71.05/5.309/72.88/11.8MiB respectively.
Worker processes had stopped at those sample points; these are not worker peaks,
scanner measurements, load tests or host sizing evidence. The receipt retains
actual image IDs and distinct container IDs. No historical source migration or
production migration record was rewritten.

Local gates: check/migration drift passed; full694tests passed in310.327s (one
existing platform skip);25script tests, Ruff/OpenAPI, Node24.19 locked ci/lint/build,
all47exactassets,177components, ESLint and five frontend helpers passed. An earlier
694-test run failed one concurrent-draft path check; five focused reruns and the
full rerun passed without changing protections/assertions. An initial restricted
component run failed four account-cache tests; focused and full normal-access runs
passed without changing tests/timeouts. Local pre_commit is unavailable; required
CI remains responsible for that check. Failed combined runs also remain retained:
negative import cache, synthetic mail configuration, restored inode identities,
an incorrect legacy fixture route, and HttpResponse/streaming response handling
were corrected in lab tooling. No production behaviour was changed to pass them.

## Operational next steps

Inspect the generated receipt, source/target resource samples, archive hashes and
phase logs. Samples are point observations, not peak memory/CPU or load capacity.
Retain failures as evidence; a failed phase never authorises production activation.
This is a fresh-container rehearsal on one Docker engine, not physical host loss,
regional recovery, actual provider acceptance or a production migration-history map.

Before a concrete cutover: select and approve the host/region/processing terms and
budget; measure scanner signature reload and full-stack load; verify private object
permissions/version recovery; decide unresolved/legacy-file treatment; and rehearse
the selected provider's interrupted restore. Keep one authoritative writer, current
receipts and the independent erasure ledger throughout. A rollback must preserve
new live rows/objects and format-2 journals; source rollback alone cannot reverse a
new storage identity or reconcile an uncertain provider outcome.

Production remains SQLite/local private media at the separately recorded verified
release. All normal sending, publication, certificate/scanner and worker gates stay
disabled. See MIGRATION_READINESS_2026-11-20.md for the dated service proposal and
../reports/MVP2_DEPLOYMENT_2026-11-20.md for real production recovery evidence.
