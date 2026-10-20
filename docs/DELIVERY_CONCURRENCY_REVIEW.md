# Delivery receipt concurrency repair

19 October 2026. Local branch `codex/delivery-concurrency`, based on deployed
`894d1eb17665b7743bded6996bec9bd7c02230c5` (PR25). Michael confirmed the backup
and reviewed CV/cover-letter downloads successfully. No push or deployment is
included in this repair. Certificates, alert defaults and broader sending remain
separate unapproved designs.

## Cause and change

The provider call runs outside the reservation transaction, correctly. However,
another SQLite writer can acquire the database between reservation commit and
receipt recording. The old code immediately converted any receipt update/read
failure into a reconciliation error. A test holding a real SQLite write lock
reproduced that exact error before the fix; this identifies a concrete race
consistent with the historical intermittent DeliveryError, rather than proving
the cause of every historical failure whose traceback was not retained.

Receipt update/read now makes at most three attempts on OperationalError, with
20 and 40 ms pauses. The provider call stays outside this loop and all database
transactions. Only a reserved row is updated. If the write committed but rereading
failed, the retry preserves the recorded outcome. Other errors fail immediately;
exhaustion still returns the sanitized reconciliation error and retains the
durable reservation/result and spent capacity. No network retry, refund, new
delivery eligibility, schema, settings or dependency change is introduced.

These are attempt bounds, not a hard wall-clock deadline: database operations
remain subject to the configured SQLite timeout. Persistent contention can still
require reconciliation. No reconciliation operation is added here.

## Regression evidence and commands

Existing Python 3.12 virtualenv:
`C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend\.venv\Scripts\python.exe`.
Backend commands run from this worktree's `ajiri-backend` with
`PYTHON_DOTENV_DISABLED=1`, `DEBUG=True`, `REAL_EMAIL_ENABLED=False`:

```powershell
& $python manage.py check
& $python manage.py makemigrations --check --dry-run
& $python manage.py test jobs.test_delivery_service --noinput
& $python manage.py test --noinput --failfast
```

- Before fix: the new real-lock regression failed with the reconciliation error.
- After fix: all 23 delivery tests passed (1.395 seconds).
- Added tests cover a real overlapping SQLite writer, a committed receipt whose
  reread briefly fails, bounded persistent receipt failures, single provider call,
  idempotent repeated request and unchanged global/per-user reservation counts.
- Stress: 40 cases passed (2.943 seconds), 20 each of the original same-request
  race and the new forced-lock regression. A repeated label list was initially
  deduplicated by Django and ran only two tests; that was not counted as stress.

The stress command used Django's test runner with this override (normal test DB
setup/teardown, no development database writes):

```python
class RepeatRunner(get_runner(settings)):
    def build_suite(self, *args, **kwargs):
        original = super().build_suite(*args, **kwargs)
        return unittest.TestSuite(
            type(test)(test._testMethodName)
            for _ in range(20) for test in original
        )
```

Labels were `jobs.test_delivery_service.DeliveryServiceTests.` plus
`test_concurrent_same_request_produces_one_provider_call` and
`test_receipt_recovers_from_overlapping_sqlite_writer_without_resending`.

Frontend used explicit Node v24.19.0 and the existing npm CLI, running
`npm ci`, `npm run lint`, `npm run test -- --run`, `npm run build`:
locked install/lint/build passed; 71 tests in 12 files passed. The verification
build matches all 21 committed frontend_build files (index newline normalized).
No frontend source/build changes are needed for this backend-only package.

The first restricted-sandbox npm install failed with npm's "Exit handler never
called" error; rerun outside that sandbox passed. An initial restricted backend
full run emitted widespread errors and was interrupted without a complete failure
report; it is not counted as a passing gate or attributed to this repair. The
focused delivery suite and stress run passed in that sandbox; final full-suite
results are recorded below after rerun outside it.

Final backend gate: **218 tests run, OK, one existing Windows symlink skip,
105.506 seconds**, outside the restricted sandbox. System check passed and
`makemigrations --check --dry-run` reported no changes. `git diff --check` passed.
Synthetic error-path events and the duplicate ZIP fixture warning are expected;
they do not represent live provider calls. No remote CI or production test is
claimed. The local commit's author/committer identity is checked against configured
noreply identity at handback.

## Review and rollback

Review the three-attempt receipt-only loop and deterministic tests; do not enable
real sending to test this package. Deployment requires separate approval and the
normal backup/stage/check/activation procedure. Code-only rollback retains all
ledger rows, newer database writes and private files; never resend a reserved or
unknown outcome to compensate for a rollback. No migration is required.

Suggested size: 2 points. Jira-ready: **Recover from transient delivery receipt
contention | AC: forced SQLite contention recovers without a second provider call;
bounded exhaustion retains durable duplicate protection and spent quotas; all gates
pass; sending eligibility remains unchanged.**
