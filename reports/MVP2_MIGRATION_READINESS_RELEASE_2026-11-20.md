# Migration-readiness release candidate -20November2026

Status: NOT DEPLOYED. Last verified production remains e3e8f74 on SQLite/private
local media. No production writer pause, migration, activation, sending or deletion
has occurred in this development session. Actual PythonAnywhere/API connectivity,
capacity and fresh independently verified private recovery are still required.

## Reviewed packages

- PR125 current DeliveryTask/registered-worker lab merged as3b919b5 after six checks.
- PR126 private-storage portability merged as73a3a97 after six checks and the updated
  synthetic11-test HTTP S3 emulator/three-object isolated restoration.
- PR128 Vite8.3.8/Axios1.21.1 security patch merged as01bc2d3 after six checks. Its
 47generated assets were committed last. No API interceptor/auth/hosting change.
- PR127 PostgreSQL bootstrap/search candidate corrected out-of-range rank weights,
  preserved SQLite and original migration history, and integrated those checked
  packages. All six passed on54f26d5; merged into MVP2 asb995d50.
  Earlier9ec204d's browser and one rerun both failed Lighthouse NO_NAVSTART. Those
  failures are retained; no performance budget/check/retry rule was weakened.

## Actual independent integration evidence

Combined source passed694 backend tests in333.176s (one existing platform skip),
check/migration drift,20script tests, Ruff/OpenAPI. The security graph/build
integration left every backend Python byte unchanged from that full-suite head;
Node24.19 locked installation/lint/build1.14s and177components in18.23s passed,
with all47frontend bytes equal to committed assets. Release-specific local gates passed:694tests in320.723s (one existing platform
skip), backend check/migration drift,20script tests, Ruff/OpenAPI, Node24.19
locked install/lint/build1.27s and all47exactassets. Separate release CI remains
required; no deployment acceptance is established by these local checks.

Docker29.9.3/Python3.12 labs used synthetic recipients/documents and captured
transports, with no host mounts, exposed ports or real credentials/documents.

- S3 emulator:11workflow tests in7.512s; bounded exact-version access, interrupted
  historical cleanup/resume, copied-object reuse and exact three-object restore.
- Actual registered outbox/Redis8.10.2: three target kinds, nine hard crashes,
  ten eligibility/disabled cases, lease contention, three-claim dead letter,
  uncertain publication and no repeated handoff/shared reservation.
- PostgreSQL17.12: alternate graph applied normally;40models/628canonical rows,
  five exact private files, receipt/consent/certificate/outbox identities, full
  timestamps, interrupted-import rollback/resumed copying, owner isolation,
  FK/sequences and subsequent additive migration.27search cases matched membership;
  seven ranking orders differed. This cold tiny corpus was slower on PostgreSQL;
  representative index-plan/load tuning remains required.
- Actual nine-file graph and target recorder were retained. A consistent synthetic
  pg_dump restored into a fresh independent container: exact rows across41tables
  and32sequence states. Twelve schema strings differed only in the explicitly
  checked literal-array cast distribution; raw definitions are retained. This is
  component recovery, not combined fresh database/object/worker/erasure acceptance.

See POSTGRES_BOOTSTRAP_CANDIDATE.md, CURRENT_OUTBOX_REHEARSAL.md and
PRIVATE_STORAGE_PORTABILITY.md for scope and reproduction. Private local logs,
synthetic graph/dump and receipts are retained; no real recovery archive is public.

## Deployment order and remaining gates

1. Require feature and separately checked release PRs; no bypass or direct-main commit.
2. Verify authenticated PythonAnywhere API reads using a privately saved Windows
   Credential Manager token. Open the existing Bash console once; afterwards API
   console input/file downloads/web reload avoid foreground mouse/browser control.
3. Remeasure real account allowance and recovery/transient reserve. Four failed lab
   containers/10863830bytes of verified regenerated local contexts were cleaned;
   this provides no production space or backup-pruning authority.
4. Observe/pause only previously enabled web and both writer workflows, drain them,
   take a consistent private snapshot, restore previous writer states promptly,
   independently copy/hash-check off-server and complete an isolated restoration.
5. Stage the exact checked release only after recovery succeeds. This source diff
   adds no production migration and does not change requirements-prod.txt; verify
   actual migrate --plan and installed runtime rather than infer either from pins.
6. Activate code with SQLite/local storage and every current operational gate still
   disabled. Verify existing rows/file bytes, HTTPS/HSTS, all47exactassets, owner
   private downloads/anonymous denial, health and restored ingestion/sweep states.
7. Roll back source only if needed, retaining live rows/files/journals. Older code
   cannot interpret format2 pathless erasure journals; suspend erasure operations
   under older code until forward support is restored. Never restore test data.

Current workstation requests to both PythonAnywhere/Ajiri time out while GitHub
returns200. Local DNS agrees with an independent public lookup; a global outage
is not established. No credential is currently saved for API preflight. No new
production backup/capacity/runtime acceptance is claimed. Genuine participants,
real hosted durability/scanning/delivery, analytics and commercial decisions remain
external gates; all16unfinished stories remain open where their evidence is absent.
