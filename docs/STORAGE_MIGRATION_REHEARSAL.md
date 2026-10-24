# Storage migration rehearsal requirements (AJ-47)

24 October2026: no production or test-target migration has been performed.
The earlier Docker image inventory could not connect to dockerDesktopLinuxEngine.
A Docker Desktop executable exists, but no service/target was started in this run.
No PostgreSQL driver or object-store client is listed in current requirements.
These are prerequisites to verify, not proof that any migration is impossible.

A further concrete source blocker is jobs/migrations/0011_job_full_text_search.py:
create_index explicitly raises RuntimeError when vendor is not sqlite. Running
normal migration history on an empty PostgreSQL target therefore cannot currently
be claimed successful. Do not edit, delete, silently fake or bypass this history
on production. AGENTS.md section10 protects migration history and hosting changes.

## Proposed isolated route, for review before implementation

1. Keep production and its authoritative SQLite writer unchanged. Select a named,
   disposable local PostgreSQL target and private object-store test target, using
   synthetic data only. Verify cost/eligibility, versions and required client tools.
2. Prepare an explicit PostgreSQL bootstrap/state strategy that leaves historical
   SQLite migrations intact. Compare a new isolated bootstrap graph against a
   separately reviewed replacement/squash strategy. Any migration-state marking
   must be confined to the empty test target and justified by schema equivalence;
   it is never permission to mark real production migrations applied without work.
3. Define a PostgreSQL keyword-search adapter and parity measurements instead of
   pretending SQLite FTS virtual tables/triggers work there. Preserve ordering,
   ownership/freshness filters and query semantics; state any ranking differences.
4. Export/import synthetic canonical model data into the actual target with stable
   PK/FK/UUID identities and exact field/file checksums. Verify row counts, FK and
   uniqueness constraints, owner isolation, document bytes/private downloads and
   immutable approval/application/authorization links. A JSON table or mock store
   is not a successful Django/PostgreSQL/object-storage migration.
5. Rehearse interruption, partial copy, restore/replay including erasure evidence,
   a single writer and resumed-write recovery. No switchback to stale SQLite after
   newer target writes without an explicit resynchronization plan. Use current
   actual account quotas and private verified off-server backups before cutover.

No target purchase, credentials, new dependency, hosting change, database migration
or original migration edit is included in this requirements note. The decision
and target are still missing; AJ47 remains To Do. A local rehearsal would not by
itself establish production hosting eligibility or authorize a real cutover.
