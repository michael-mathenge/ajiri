# CV builder schema package review

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

17 October 2026. Design approved by Michael in chat before implementation.
Branch: `codex/cv-builder-schema`, based on reviewed UI batch tip `4e3b1f3`.
Suggested estimate: 3 points. This is schema preparation, not a working CV builder.

## Changes

- New owner-linked CVWorkspace and CVApproval models match
  `docs/CV_BUILDER_DESIGN.md`. Positive revision checks, one workspace per profile
  and one approval per profile/revision are enforced by database constraints.
- `profiles/0005_cv_workspace_approval.py` contains exactly two CreateModel
  operations. No RunPython, backfill, modification of existing columns, User
  changes or edits to previous migrations. No migration applied to development
  or production databases; migration execution tests use the test database.
- Strict nested validation bounds complete CV content to 100 KiB before and after
  normalization. Limits apply to text, sections and achievements; dates, safe URL
  schemes, primitive types, unknown keys and duplicate entry IDs are checked.
  Optional sections stay empty; approval validation needs a name and substantive
  content. It never derives a name or invents qualifications.
- Private UUID document paths ignore client filenames. The 2 MiB output limit is
  defined for the later renderer; no renderer/file writes added in this package.
- Tests cover validation and schema constraints, snapshot separation, concurrent
  conditional revision writes and forward migration with unchanged legacy rows.

## Boundary and remaining implementation

No endpoint, current Profile serializer, frontend, CV generator, application
drafting, sending, auth, CORS, ingestion, dependencies or CI behavior changed.
Existing immediate CV generation still works as before; approval-gated generation
will be introduced with the service/client package, after this review.

Direct ORM writes do not automatically call the DRF validation helper. Approval
immutability, canonical hashing, ownership, optimistic concurrency, idempotent
approval, file consistency/size/hash checks and safe old-download behavior are
requirements for the next service package, not guarantees of this schema alone.
The concurrency test proves only the database compare-and-swap primitive; endpoint
race tests remain necessary once endpoints exist. Private file cleanup on account
deletion and report-only orphan reconciliation remain service/runbook work.

## Verification

Executed 17 October 2026 in the isolated checkout:

- `python manage.py check`: no issues.
- `python manage.py makemigrations --check --dry-run`: no changes detected after
  generating 0005 with `makemigrations profiles --name cv_workspace_approval`.
- Focused initial schema suite: 10 tests passed; the final full suite includes
  11 new schema/validation/concurrency/migration tests.
- `python manage.py test --noinput`: 189 tests, OK, one existing Windows symlink
  skip; 109.107 seconds. Dotenv disabled, DEBUG=True, REAL_EMAIL_ENABLED=False.
- Frontend on bundled Node 24.19.0: locked `npm ci`, lint, 51 component tests in
  eight files and production build all passed. No frontend source changed; the
  resulting build matches the already committed frontend_build after normalizing
  index.html line endings, so no generated-file commit is needed here.
- `git diff --check`: passed. No real messages, external calls or production tests.

To rerun the focused suite in PowerShell (uses a disposable test database):

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:REAL_EMAIL_ENABLED = 'False'
.\.venv\Scripts\python.exe manage.py test profiles.test_cv_schema --noinput
```

Expected: 11 tests pass. Do not run `migrate` against production for this review.

## Review and rollback

Review the two CreateModel operations and validation contract. No server actions
are needed now. The next package adds draft/review/approve/download behavior only
after schema-package approval.

Future release sequence: fresh verified backup, stage reviewed code, inspect exact
migration plan, apply this additive migration, then activate matching code/client.
Unexpected migrations stop the release. No push/deployment is authorized here.

Routine code rollback retains these tables and private files; no database restore
over newer writes. Reversing 0005 drops new CV tables and requires separate explicit
approval and preservation of any CV data. Tests reverse only their disposable test
schema. Old models can read existing Profile/User rows after forward migration.

Original checkout AGENTS/lockfile/coverage changes, Git configuration and stash are
preserved; the reviewed UI improvements remain in the local batch history.
