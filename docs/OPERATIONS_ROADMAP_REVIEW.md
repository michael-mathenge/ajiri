# Operations and staging package

21 October 2026. Branch `codex/jira-operations`, based on deployed PR #27 merge
`cc731976de13a5b5d561739def8dd93a26f70bff`. Local until its PR/activation evidence
is recorded in JIRA_ROADMAP_PROGRESS.md. No migrations or dependency changes.

## Changes

- AJ-35: existing `.env.example` now has a valid local mail sink and approved local
  CSRF origins instead of blank values that break fresh setup. The read-only
  `scripts/release_preflight.py` validates exact clean source, reviewed migration
  delta and safe committed build references. It does not install, migrate or reload.
  Actual runtime migration planning and off-server recovery verification remain
  mandatory. The current deployment checklist replaces stale canonical instructions;
  the original Checkpoint2 version is preserved in `docs/archive/`.
- AJ-36: isolated non-root/read-only-root container, private named data volume and
  loopback port8001, real mail forcibly off, no ingestion credential. Docker copies
  only application/build source and excludes credentials/databases/private files.
  The original learning container on port8000 remains intact. This local staging
  arrangement is not a second hosted public environment.
- Backup automation support: `verify_private_backup` independently verifies
  completed manifests, all hashes, database integrity and bounded safe archives;
  optional restoration uses a new private folder and writes completion evidence
  only after success. Partial/corrupt/traversal/existing destinations are rejected.
  No live restore or retention deletion. Git-free packaged snapshots explicitly
  report unverified source provenance instead of failing to protect local data.
- Container-safe private path guards distinguish the checkout root from a packaged
  `/app`; `/` is not treated as the entire application tree. Production Git checkout
  protection remains. Header settings tests no longer write unrelated platform logs.
- The SQLite last-slot regression permits only the service's documented bounded
  busy/no-handoff result, then reconciles the same losing key after workers finish.
  It still requires exactly one accepted attempt/provider call/quota claim. A
  deterministic exhausted-lock test proves zero handoff/budget consumption.
  No delivery service retry policy or real sender changed.
- A render boundary addresses the observed stale-tab lazy-chunk blank screen with
  a safe explicit reload action, unsaved-edit warning and no exception detail,
  authentication clearing or automatic mutation retry.

## Actual checks

```text
Docker Compose configuration/build                     passed
Fresh isolated staging migrations                      passed
Localhost:8001 health and UID10001/data/mail isolation   passed
manage.py check and migration drift in staging          passed, no changes
Full final allowlisted-image Django suite               296 passed, no skips, 79.426s
Native focused backup/preflight tests                   20 passed
Concurrency regression, five separate invocations       all passed
Actual private off-server backup verifier/restore       12 files, 212184 bytes; passed
Node24.19 locked install, lint, component tests/build    passed;102 tests,16 files
```

Two useful failures were fixed rather than hidden: the original packaged path
guard rejected every backup under `/`, and a contending SQLite caller can truthfully
return busy after bounded pre-network retries. The earlier Windows-locked Tailwind
binary remains untouched; the Node gate used the documented fresh isolated runner.
The final generated build is committed last. The clean-checkout release planner
must be executed after that commit, and remote CI must pass before merge.

## Operation and rollback

Read STAGING.md, BACKUP_AUTOMATION.md and the current DEPLOYMENT_CHECKLIST.md. Keep
production code/client pairs aligned; no schema reversal is needed for this batch.
The staging volume is preserved on routine compose down. Never use --volumes or
copy developer data over production. Sending and account credentials are unchanged.

Suggested sizing: AJ-35 **3**, AJ-36 **3**, backup/portability/concurrency repairs
**3**, recovery UI **2**. Do not mark remaining application/alert/privacy-export or
provisional integrations complete based on this package. Requirements for AJ-42–52
are documented separately; fake/live integrations are still pending.
