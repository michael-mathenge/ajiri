# P2 application-package editor review

20 October 2026. Branch `codex/application-package-editor` starts at approved P1
`e1e8f94`. Work remains in the isolated application-package-schema worktree.
Michael approved P1 and proceeding to P2. No push, PR, merge or deployment occurs.
Recorded production remains `894d1eb`; it has not been inspected during this package.
The root checkout, Docker lesson, lockfile, coverage, stash and Git config are preserved.

## Result and scope

- My applications loads an owner-only editor on explicit request. It shows bounded
  job context, original/legacy document labels, approved-CV selection with its existing
  private download, job-specific saved-letter revision selection, letter editing and
  email subject/body drafting. Choosing a CV never silently replaces the letter.
- Explicit save appends a package revision, exact approved CV bytes and rendered
  literal letter text. Existing Application fields/files and older packages remain
  unchanged. Reusing an older letter makes a new revision under current displayed
  context; it never overwrites the original. There is no AI/provider call.
- Neutral drafting uses approved CV facts rather than the legacy generator's mutable
  profile and match-score assertions. The new letter template is explicitly
  `application-letter-v1`; historical application documents are not regenerated.
- Owner/state/revision/job-context checks, transaction write-before-read and unique
  revisions prevent stale/concurrent replacement. Reserved/unknown/accepted delivery
  receipts block further edits. Missing/changed CV bytes fail closed. Failed writes
  clean only request-owned staged files; hard-crash orphans remain report-only.
- All new responses are private/no-store. Lists are paginated at 20 and return no
  storage paths. Job context is allowlisted/truncated with an explicit truncation
  indicator. Inputs reject unknown fields, invalid types, controls and excessive text.
- Client mutations are explicit and single-flight. Uncertain save/409 blocks further
  saves until a GET reload; no automatic mutation retry. Reload or older-selection
  asks before discarding dirty edits. Unload and same-window links warn when dirty.
- The legacy email sender is disabled before any claim/status change or backend
  call, with stable `application_sending_disabled` 409. No runtime enable switch was
  added. External-site confirmation retains its atomic claim. The old SMTP-send
  tests now assert the disabled boundary; concurrency tests cover external confirmation
  and the existing separate ledger concurrency repair remains in the suite.

No new approval endpoint/control, package-download endpoint, delivery authorization,
attachment activation, consent/schema migration, dependency, authentication/CORS,
ingestion, CI or hosting change. P1's approval table stays dormant. Original documents
remain downloadable with explicit labels; they are not the newly saved package.

## Verification

Focused backend command: `manage.py test jobs.test_application_packages
jobs.test_lifecycle jobs.test_send_concurrency --noinput --failfast`: 25 tests passed
in 3.021 seconds before adding the concurrent-package-save regression. The first
focused run found a test fixture re-computing its supposed stale job fingerprint;
the fixture now captures the old fingerprint before editing the job. No production
validation was relaxed.

Focused components: `npm run test -- --run src/test/application-packages.test.jsx
src/test/flows.test.jsx`: 16 passed across two files in 5.58 seconds.

Full gate commands (backend uses existing checkpoint-3b Python 3.12 virtualenv):

```powershell
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:REAL_EMAIL_ENABLED = 'False'
& $python manage.py check
& $python manage.py makemigrations --check --dry-run
& $python manage.py test --noinput --failfast
# Existing bundled Node v24.19.0 explicitly precedes other Node executables in PATH.
& $node $npm ci
& $node $npm run lint
& $node $npm run test -- --run
& $node $npm run build
```

Final counts/timing and committed-build verification are recorded below after the
gates finish. Tests use synthetic data, disposable SQLite databases and temporary
private files. No ordinary development/production database was migrated.

## Manual review and remaining limits

In an isolated test environment on this branch with P1 migrated, prepare a synthetic
application, then open My applications / Review application / Choose CV and edit
cover letter. Verify empty selection, select/download an approved CV, generate/edit
a letter, save revision 1, reload and reuse it to create revision 2. Confirm old
downloads remain labelled original and old contents are unchanged. Verify two tabs
conflict on the same expected revision, and a failed/uncertain save requires reload.
Check keyboard controls, narrow phone layout, large job/letter wrapping and warnings
before discarding edits. These live browser/manual checks remain UNVERIFIED here;
the currently running Docker lesson uses an older checkout and cannot demonstrate P2.

The component/API tests are not a single browser end-to-end test. Browser history
Back/Forward interception is not guaranteed by the current BrowserRouter setup;
unload and link warnings are implemented without changing router architecture.
The existing CV-version endpoint lists only 20 recent approvals; package provenance
outside that window remains selectable through a previously saved package.
After saving, the editor shows the new row; reload fetches the full paginated history.
Local edits are not autosaved. Retention/erasure and PROTECT constraints remain the
P1 design limits. Package approval/download integrity checks belong to P3.

## Rollout and rollback — proposal only

Any future release must include P1 tables first: verified backup, stage/review
expected migration, apply, then activate the paired client/server. No release is
performed here. A mixed older frontend/newer server will receive 409 for email
sending; it cannot bypass the boundary. Rollback must retain package rows/files and
keep email disabled; reverting to the old ungated sender is not an acceptable
rollback. Never reverse populated P1 or restore an older DB over newer writes.

Suggested size: **5 points**, AJ-17 application workflow. Jira-ready:
**Select approved CV and edit job-specific application revisions | AC: owner-only
append-only packages, exact CV bytes, stale/concurrent save protection, no delivery
side effects, legacy email disabled, external confirmation preserved, gates pass.**

Stop after P2 for review. P3 exact package preview/private downloads/document
approval is the next package; P4-P5 sending/pilot remain separately approved work.

## Final gates — 20 October 2026

- Backend check: no issues. Migration drift: no changes. Full suite: **234 tests
  run in 121.975 seconds, OK with one existing Windows symlink skip**.
- The first full backend run exposed SQLite shared-cache immediate lock rejection
  in the new concurrent-save test. The service now cleans its own staged files and
  returns a safe conflict for that lock condition, without retrying a mutation.
  Other operational failures retain the generic unavailable response. Focused
  lock/transaction-failure rerun: 2 passed in 2.784 seconds.
- Explicit repeated concurrency suite: **20 passed in 30.466 seconds** (ten package
  save races and ten external-confirmation races, distinct test instances).
  Repeating CLI labels alone was found to deduplicate to two tests; that preliminary
  run is not counted as 20. Existing delivery-budget concurrency tests also passed
  within the full suite.
- Node **v24.19.0**, locked npm ci: 180 packages installed, 181 audited, zero reported
  vulnerabilities. Lint passed. Full Vitest: **78 passed across 13 files**, 9.50 seconds.
  Build passed in 4.08 seconds. The first full frontend run had one old journey
  assertion expecting the removed Send button; it now asserts disabled sending,
  and the complete frontend gates passed on rerun.
- No source fixes required new dependencies, migrations, production actions or
  modifications to the Docker lesson. All mail/provider tests are captured/mocked.

Runtime paths used (PowerShell):

```powershell
$python = 'C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend\.venv\Scripts\python.exe'
$node = 'C:\Users\micha\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$npm = 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js'
$env:PATH = (Split-Path $node) + ';' + $env:PATH
```

Backend commands ran from this worktree's ajiri-backend; frontend commands from
ajiri-frontend. Gates ran outside the Windows sandbox to permit temporary private
file permissions and Node child processes. The final frontend-build commit contains
only regenerated artifacts; the generated build is compared with dist file-for-file,
normalizing index.html line endings. Author/committer identities are checked against
the configured noreply identity in the non-empty e1e8f94..HEAD range at handback.

Generated-build verification completed: **21 files matched** the subsequent clean
Vite build after normalizing index.html line endings (verification build 1.16s).
Final diff review also corrected a Windows text-encoding change in documentation;
historical text is preserved and only the new concept/banner remains in its diff.
