# Dependabot check failures

19 October 2026. Test-only fix on `codex/draft-concurrency-test`, based on merged
main d0031e5. No application runtime, dependency, schema, auth, CI or production
configuration changes in this branch. Suggested estimate: 2 points.

## Confirmed failures

- PR21, run 39225067048, Python 3.13: checkout/setup/install/check/migration drift
  passed. `ConcurrentDraftTests.test_concurrent_drafts_keep_one_application_and_two_snapshot_files`
  raised BrokenBarrierError while generating a letter. Python 3.12/3.14 were
  cancelled after the matrix failure, not separately demonstrated failures.
- PR22, run 39225761903, Python 3.14: the same test raised CVUnavailable while
  reading the approved CV. Its workers shared one ORM approval and FieldFile,
  so file open/read/close state could interfere. Real requests fetch independent
  ORM instances. The earlier barrier could then strand the other worker.
- PR22 frontend: install/lint/tests/build passed; the committed-build consistency
  check failed because dependency updates changed generated asset hashes without
  refreshing frontend_build. Rebuilding must use PR22's exact lockfile. This is
  separate from the concurrency fixture problem.

## Test correction

Each worker now loads its own CVApproval/FieldFile. A barrier wraps the real
Application.save immediately before SQL inside the existing deferred transaction,
after document generation and writes. Both attempts still race for the real
user/job uniqueness constraint; no application behavior or lock handling changed.
The assertions still require one Application, at least one successful result and
exactly two retained snapshot files. The real generators still run; no skipped
test, looser assertion, automatic retry or increased timeout was introduced.

Ten actual repeated race cases passed in one isolated test run (13.651s). An
initial attempt to repeat identical test labels was deduplicated by Django and
ran only one case; the ten-case result uses distinct TestCase instances. The full
suite started before the per-worker FieldFile correction was interrupted and is
not counted as a passing gate. Final gates: backend check and migration drift
passed; all 210 tests passed in 155.706s (one existing Windows symlink skip).
Locked npm ci, lint, 66 frontend tests and build passed on Node 24.19.0.
No generated-build changes are needed for this test-only branch.

The earlier intermittent account-email budget race remains a separate open
concern; it is not fixed or suppressed by this package. No real mail was sent.

## Integration and rollback

Review/merge this test fix into main separately, then update both Dependabot PR
branches from that main and rerun their required checks. PR22 additionally needs
its regenerated committed assets, prepared in an isolated checkout of its branch.
Do not weaken checks or merge a failing dependency PR. Source/test-only rollback
requires no data operation. Production deployment is not needed for this test fix.
