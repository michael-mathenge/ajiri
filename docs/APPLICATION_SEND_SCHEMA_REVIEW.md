# P4a authorization schema review

20 October 2026. Branch `codex/application-send-schema` starts from approved P4
design `b1bd394`, in `C:\dev\ajiri\.worktrees\application-package-schema`.
Michael reviewed the design and approved the additive schema/tests-only package.
Stop after this package. No P4b/P4c API/service/client, push, PR, deployment or
production inspection is included. Recorded production remains `894d1eb`.

## Changes

- Migration `jobs/0010_application_send_authorization_schema.py` creates only
  ApplicationSendAuthorization and ApplicationSendAttemptLink plus six constraints.
  No RunPython/RunSQL, data backfill, existing-table field/constraint change or User
  model change. Historical migration files are untouched. The swappable User FK is
  a reference, not an alteration of AUTH_USER_MODEL.
- Authorization has UUID identity, unique explicitly supplied request key, protected
  Application/User/document-approval provenance, explicit plan/hash/policy/times,
  authorized/withdrawn/superseded/expired/dispatch_started states, nullable closed_at
  and optional protected retry receipt. Defaults are state, UUID identity and None
  for optional columns; time/request/plan inputs are not silently manufactured.
- Constraints enforce valid states, closed_at presence according to state, expiry
  strictly after authorized_at, and one authorized row per application. Neither
  24-hour expiry policy nor one-way transitions are runtime behavior in this package.
- Attempt links protect their authorization and receipt, enforce both one-to-one
  mappings, optional unique non-null previous_attempt and rejection of self retry.
  Existing delivery_app_unresolved and other ledger constraints remain intact.
- No endpoint, serializer, admin registration, signal/task, sender, preference,
  file-generation/deletion, dependency, deployment configuration or frontend change.
  Existing email send still returns application_sending_disabled before any claim.

The only change to the older P1 migration test pins its upgrade target to jobs0009
instead of future leaf migrations; it still verifies only P1 and restores current
leaves in cleanup. P4a has its own populated jobs0009-to-jobs0010 upgrade test.

## Verification and limits

Focused command from ajiri-backend:
`manage.py test jobs.test_application_send_schema jobs.test_application_package_schema --noinput --failfast`
— **13 passed in 2.964 seconds**. New cases cover active/request uniqueness,
state/closed-time pairs, expiry/required inputs/no implicit defaults, link uniqueness,
retry fork/self rejection, PROTECT and disabled-sender/no-budget/no-file effects.

The populated MigrationExecutor test creates pre-P4a User/Profile/Job/Application,
CV approval, package/document proof, notification, three channel receipts and shared
budget, plus five synthetic private files. It checks exact operation types/counts,
unchanged existing model fields/options, unchanged row values and file bytes, empty
new tables and old-model readability after upgrade. No old preferences, historical
sent flags or receipts are reinterpreted. Only disposable test DBs are migrated.

SQL-only tests explicitly demonstrate that cross-owner/mismatched-channel links,
an empty JSON plan and lifecycle reopening remain possible through raw ORM writes.
This is not advertised as safe authorization behavior. No API exposes such writes;
P4b must close those gaps transactionally before using the tables. The hash field
has model validation, but save() does not automatically call full_clean(). The full
plan schema/64-KiB bound, exact hash correspondence, 24-hour policy, expiry handling,
retry count and dispatch cutoff are deliberately NOT implemented here.

## Full gate commands

PowerShell definitions and environment used:

```powershell
$python = 'C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend\.venv\Scripts\python.exe'
$node = 'C:\Users\micha\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$npm = 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js'
$env:PATH = (Split-Path $node) + ';' + $env:PATH
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:REAL_EMAIL_ENABLED = 'False'
# From this worktree's ajiri-backend:
& $python manage.py check
& $python manage.py makemigrations --check --dry-run
& $python manage.py test --noinput --failfast
# From this worktree's ajiri-frontend:
& $node --version
& $node $npm ci
& $node $npm run lint
& $node $npm run test -- --run
& $node $npm run build
```

Final outcomes and unchanged generated-build comparison follow after completion.
Python 3.12 Windows only; do not infer Python 3.13/3.14/Linux results. Existing Node
runtime/dependencies are reused. No live provider, inbox, browser, migration or
production acceptance claim is made. The current Docker lesson stays untouched.

## Future rollout/rollback — not performed

Any later separately approved release: pause relevant writers, verify a fresh
consistent private backup, stage code/migration, review the full delta from the
actual production SHA, apply only expected migrations, then activate paired code.
P1 jobs0009 may also be pending on production; do not assume only0010 is needed.
Stop on unexpected operations. No dependency upgrade is required by P4a.

Routine rollback reverts code to a reviewed email-disabled version while retaining
populated tables, plans, proofs, links, files, receipts and newer writes. Generated
reverse0010 drops both new tables and loses evidence; it is destructive, not routine
rollback. Never restore an older DB over newer writes or enable the legacy sender.
PROTECT can block future account/application/proof/receipt deletion once records
exist; resolve retention/erasure in AJ-25 rather than silently adding deletion hooks.

Suggested size: **3 points**, implementation slice of AJ-17; re-estimate remaining
P4b/P4c after this review. Jira-ready:
**Add dormant application send-authorization schema | AC: two additive tables,
reviewed constraints, no backfill, populated upgrade preserves existing rows/files,
no sender activation, complete gates pass and rollback retains evidence.**

Next after review: P4b authorization/withdrawal and mocked shared-service integration,
with explicit checks for all service-only invariants and real application sending
still disabled. Stop for P4b review before client/P5 work. This handback grants no
email, pilot, push or deployment permission.

## Final outcomes — 20 October 2026

- Backend check: no issues. Migration drift: no changes. Full suite: **255 tests
  run in 146.486 seconds, OK with one existing Windows symlink skip**. Expected
  synthetic failure-path logs contain no provider email operation.
- Node **v24.19.0**; locked npm ci installed 180 packages / audited 181 with zero
  reported vulnerabilities. Lint passed; full Vitest **86 passed across 14 files
  in 21.55 seconds**; build passed in 9.71 seconds.
- All **21 generated frontend files match** the committed build after normalizing
  index.html line endings. No frontend source, dependency lockfile or generated
  asset changed; no new frontend-build commit is needed for this backend package.
- Only the new0010 migration was created; no historical migration was edited.
  Populated upgrade and P1 migration regression passed. No ordinary development or
  production database was migrated. There were no installs of new declared
  dependencies, services, connector writes, real messages, pushes or deployments.
- git diff --check passed. The branch is checked before the local commit, then the
  non-empty `git log --format="%h %ae | %ce" b1bd394..HEAD` author/committer range
  is verified against the configured noreply identity. Original checkout changes,
  Docker lesson, existing coverage, stash and Git configuration remain intact.
