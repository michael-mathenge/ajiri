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
