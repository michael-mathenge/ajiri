# Actual local queue rehearsal (AJ48)

24 October 2026. This supplements the earlier inline contract with a real Redis
broker and separate Celery worker process. It does not provision a production
worker, change hosting/CI, register a runtime task, or send email.

## Isolation and reproduction

From the repository root in PowerShell, with Docker Desktop running:

```powershell
python scripts/prepare_queue_rehearsal.py
# Use the unique context path printed above as <context>.
docker build -t ajiri-queue-rehearsal:synthetic-20261024 <context>
```

The context exporter includes tracked backend source only; explicit scripts and
Dockerfile are copied separately. No environment, local database, backup or private
document is mounted. The image uses existing requirements-prod.txt without adding
runtime dependencies and runs as UID10001. The script refuses ordinary host/default
execution before Django/database/broker setup.

Use an unused dedicated container name. The actual target used network none,
tmpfs /data, no published port or host mount, loopback-only Redis with protected mode
enabled and AOF enabled. The Python test container used that target's network
namespace, a read-only root and tmpfs /tmp. No credentials were created or copied.
This isolated loopback setup is not a production broker security configuration.

The official image tested was redis:8-alpine at digest
`sha256:0bf6577d7774e592b29d093e3ac9390eb91e13d72c21e506afce736de5e0eeb0`;
the actual server reported8.10.2. Python base digest is pinned in the Dockerfile;
Celery5.6.3 and Redis Python client8.1.0 come from locked production requirements.

```powershell
docker run --rm --network container:<dedicated-redis-name> --read-only `
  --tmpfs /tmp:rw,nosuid,size=192m ajiri-queue-rehearsal:synthetic-20261024
```

Never point this at a shared or production broker. Verify the exact created
container ID and rehearsal label before removing only that disposable target.

## Actual result and boundaries

The source database is normally migrated synthetic SQLite with owner-approved test
documents and synthetic exact authorization. Broker task arguments contain only
owner ID and the existing authorization UUID. The worker resolves current evidence
through the existing queue executor, dispatch policy and shared delivery ledger.
Brevo handoff is replaced inside the test process by a local counter and synthetic
accepted result. No real email or provider request occurs.

After a captured handoff and durable accepted receipt, the worker exits73 before
Celery acknowledgement. After the Redis lease expires, the harness explicitly
restores the expired lease and starts a new worker. Redelivery and a further duplicate
return the same accepted receipt. Exactly one attempt and one global reserved
application budget remain; the capture count stays one. A separately withdrawn
authorization is rejected without a new attempt or handoff. The first run exposed
an expected PackageConflict that the harness did not classify; the corrected run
handles the existing closed-authorization exception and asserts the denial.

This proves a process crash after durable settlement and explicit lease recovery,
not provider delivery, broker/host crash durability, automatic periodic recovery,
dead-letter operations, distributed load or a crash inside uncertain provider IO.
AOF on tmpfs is intentionally disposable, not an off-server recovery guarantee.
Those cases and an eligible production worker/broker, retention/access/encryption
and operator reconciliation remain unfinished. AJ48 stays In Progress.

No production code imports this script. Rollback removes only the unused lab;
existing authorizations, delivery receipts, backups and current settings remain.

## Automatic worker recovery — 25 October 2026

The earlier explicit lease-restoration result above remains historical evidence.
The harness now waits for lease expiry and starts the replacement worker without
calling Redis/Kombu lease-restoration methods. The replacement worker recovered
the original task automatically. The real Redis/Celery run passed: hard exit73,
same accepted receipt on redelivery and duplicate, one captured handoff, zero
real email calls, one application reservation and withdrawal denial. The dedicated
network-none Redis had no published port or host mount and used disposable tmpfs;
its exact container identity/label was verified before removal. Existing Docker
resources were preserved. The image uses the existing pinned dependencies.

This closes the manual worker-recovery limitation in the earlier rehearsal. It
does not verify broker/host loss, production hosting, dead-letter operations or a
crash during uncertain provider IO. AJ48 remains In Progress. Required package
gates and CI/release results are recorded in JIRA_ROADMAP_PROGRESS.md.

## Broker-process crash with retained AOF — 25 October 2026

The optional `--broker-restart` harness mode now verifies that AOF is enabled with
`appendfsync always` before testing. After the worker exits73, the harness prints
`AJIRI_SYNTHETIC_BROKER_RESTART_REQUIRED` and waits for the operator's
`broker-restarted` input. Kill/restart only the exact disposable broker identity
created for this run; never a shared/production Redis. No Docker socket or host
credential is mounted into the runner. It checks the Redis server run ID changed
before continuing, so an unchanged broker cannot masquerade as a restart.

Actual run: Redis8.10.2/Celery5.6.3, pinned official Redis digest above; internal
network with no published ports, labelled synthetic-only Docker volume for AOF,
read-only runner and disposable tmpfs for database/documents. The broker accepts
only the internal test network; this is not production access configuration.
The broker received SIGKILL and restarted using the same synthetic volume. The
replacement worker recovered its unacknowledged task automatically. Same accepted
receipt, one application reservation, one captured handoff, zero duplicate/real
email calls and withdrawal denial passed. Broker, network and volume labels/identity
were checked before removal; existing resources and private data were preserved.

Reproduction uses the existing preparation/build commands, with an internal
dedicated network/volume and Redis arguments `--appendonly yes --appendfsync always`.
Set `AJIRI_QUEUE_LAB_HOST=broker` on the runner, use `docker run -i` and append
`python /rehearsal.py --broker-restart`. At the marker, kill/start the exact verified
broker ID, then send the input token. Only loopback or the fixed `broker` test alias
is accepted; a regression rejects arbitrary broker hosts before connecting.

This establishes broker-process restart with retained local AOF, not host/power
loss, disk failure, off-server broker restoration, clustered failover or production
eligibility. Unknown provider-IO reconciliation and dead-letter operations remain
unverified. AJ48 stays In Progress; no production worker or mail was activated.

## Hard exit inside uncertain handoff — 25 October 2026

`python /rehearsal.py --uncertain-handoff` uses a separate disposable broker and
fsyncs the synthetic handoff counter, then exits74 inside the captured transport
before receipt settlement/acknowledgement. Automatic redelivery and an explicit
duplicate both returned the same original reserved receipt with no provider ID or
resolved timestamp. One reservation/one captured side effect remained, with zero
new handoffs and withdrawal denial. The actual Redis/Celery run passed; the exact
labelled broker was removed afterwards. This covers a real worker-process crash
around simulated IO, not an actual uncertain Brevo request or permission to retry.
The reserved receipt remains unresolved; no operator reconciliation or dead-letter
policy is inferred or activated. Existing production ledger behavior was unchanged.
