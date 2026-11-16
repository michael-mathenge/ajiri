# Current durable outbox rehearsal

AJ-48, 16 November 2026. This supplements the historical application-only queue
lab; it exercises the deployed `DeliveryTask` publisher/executor and registered
`jobs.run_delivery_task` with real Redis and separate Celery worker processes.
Production worker, producer, schedule and sending gates remain unchanged.

## Isolation and reproduction

Docker Desktop must already be available. From this checkout, with Python on PATH:

```powershell
python scripts/prepare_current_outbox_rehearsal.py
docker build -t ajiri-current-outbox:synthetic <printed-context>
docker run -d --name ajiri-current-outbox-broker --label ajiri.lab=current-outbox --network none --tmpfs /data:rw,nosuid,size=64m redis:8-alpine redis-server --bind 127.0.0.1 --protected-mode yes --appendonly yes --appendfsync always
docker run --name ajiri-current-outbox-run --label ajiri.lab=current-outbox --network container:ajiri-current-outbox-broker --read-only --tmpfs /tmp:rw,nosuid,size=192m ajiri-current-outbox:synthetic
```

Use unused dedicated names. The exporter accepts tracked backend source only and
explicitly copies the lab script; it excludes private databases/documents and
environment files. No Docker socket, host mount or published port enters the lab.
The runtime has only the isolated broker's network namespace. Provider handoffs
are captured inside the worker after current transport eligibility and immutable
document checks; recipients must end in `@example.invalid`. No provider request
or inbox delivery occurs. Only remove the exact resources created for this run,
after inspecting their IDs and matching labels; preserve all other Docker work.

## Behaviour under test

- Applications, match alerts and saved-search windows use their current adapters.
- Nine hard exits cover before/during/after handoff for all three target kinds.
- A during-handoff crash retains the reserved receipt and requires reconciliation.
- Accepted receipts survive duplicate delivery, lease contention and recovery with
  exactly one captured handoff and one shared global reservation per target.
- Lost broker confirmation follows an actual Redis publication. The publisher
  records uncertainty and refuses a second automatic publication.
- Two separate workers contend for the same task; the active lease is respected.
- Three failed execution claims dead-letter without a provider call.
- Revoked consent, changed mailbox, vacancy expiry, foreign owner, changed search
  revision, expired/withdrawn authorisation and disabled transports deny handoff.
  Application exceptions retain the existing needs-reconciliation classification.
- A SQLite backup and exact private media copy restore into a fresh private root.
  A fresh process/broker logical database replays the original targets and verifies
  receipt reuse before processing one new synthetic sentinel.

The bounded lab explicitly expires the application's three-minute lease after
observing each hard worker exit; this is operator-driven recovery, not proof of a
production periodic recovery schedule. Broker duplicate messages traverse real
Redis/Celery. Logical-database recovery is not a fresh host/container, an off-server
restore, power-loss durability or an actual hosted worker acceptance result.

The process prints only aggregate `AJIRI_CURRENT_OUTBOX_RESULT` JSON on success.
Any failed assertion is failed evidence. Preserve older lab checkpoints and report
this result separately from combined recovery and eventual provider acceptance.

## Rollback

This package adds source-only lab scripts and guidance. Removing those additions
does not change runtime tables, delivery receipts, settings or production data.
No database migration, runtime dependency or CI workflow change is required.
