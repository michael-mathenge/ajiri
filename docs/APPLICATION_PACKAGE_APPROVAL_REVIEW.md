# P3 saved-package review and document approval

20 October 2026. Branch `codex/application-package-approval` starts at reviewed P2
`ae8d05f`, in `C:\dev\ajiri\.worktrees\application-package-schema`.
Michael approved P2 and proceeding with P3. No push, PR, merge, deployment or
production inspection is performed. Recorded production remains `894d1eb`.

## Changes

- Owner-only GET package review returns plain paragraph text/order parsed from the
  actual saved DOCX bytes, saved job context, email draft and approval state. It
  neither renders current Profile data nor regenerates documents. The UI labels
  the preview as text/order, not Word's font/page layout, and offers both saved
  downloads before explicit approval. Original application downloads remain labelled.
- Owner-only GET/HEAD downloads return verified saved bytes with existing safe
  Content-Disposition naming. HEAD has no body and retains the document length.
  No storage paths or public media mappings are exposed. All responses/errors are
  private/no-store. Historical sent/dismissed packages are readable, not approvable.
- Every review/download checks both document sizes/hashes, canonical package
  fingerprint, approved-CV recorded hash/content provenance and matching owner.
  Existing bounded DOCX validation precedes parsing. Missing/changed bytes or bad
  document metadata fail closed. Review/approval also reject invalid proof metadata
  or unsupported preview tables with generic errors. Preview
  checks the letter paragraphs correspond to the saved letter text; no file is
  rewritten to repair a discrepancy. Source CV files may be absent if the exact
  independent application snapshot and its retained provenance remain intact.
- Approval requires explicit Boolean true, expected latest revision and exact
  fingerprint. It records owner, server time and `application-documents-v1` policy.
  An Application conditional write starts the transaction before reads, serializing
  approval with revision saves; state/latest/content/file checks repeat inside it.
  Identical approval of the unchanged latest package returns the existing proof.
  SQLite lock conflicts return a safe conflict, with no automatic mutation retry.
- New revisions have no approval; old proofs remain historical. Sent/dismissed,
  inactive/scam or reserved/unknown/accepted-delivery applications cannot acquire a
  fresh approval. Profile/job edits never rewrite saved files or approval evidence.
- The client starts unchecked, resets its preview/checkbox on working edits or
  revision changes, ignores delayed stale responses and reconciles uncertain
  approvals by GET. It never silently repeats an approval mutation. A later file
  replacement fails subsequent verification rather than being served or approved.

The canonical fingerprint was extracted without changing its P2 format. No model
field or migration changes, new dependencies, auth/CORS, ingestion, hosting or CI
changes. P1's existing proof table is now used; document templates remain unchanged.
No sending permission, provider or ledger write, attachment activation, automatic
submission or real email is added. The legacy email route remains disabled.

## Focused verification

Backend: `manage.py test jobs.test_package_review --noinput --failfast` — **13 passed
in 8.106 seconds**. Tests cover actual file bytes/text, private GET/HEAD, explicit
true/types, repeated approval, stale hash/revision, new revisions, profile/job
edits, ownership, corrupt/missing files, corrupt metadata/proof, generic parser
failure and concurrent approval/save. The first run's expectation for a tampered
stored fingerprint was corrected to 409 for the client's now-stale hash; validation
was not weakened. Imported fixtures were changed to a module reference to avoid
unittest accidentally rediscovering ten existing tests as duplicates.

Components: `npm run test -- --run src/test/package-review.test.jsx
src/test/application-packages.test.jsx` — **15 passed across two files, 4.16 seconds**.
Tests cover escaped stored text, explicit unchecked approval, editor-to-review
transition, working-edit reset, ignored late response, network/stale reconciliation,
historical proof labels and unavailable-file behavior. These are component tests,
not a single browser end-to-end run.

## Full gate commands and environment

PowerShell runtime definitions:

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

Actual full outcomes are appended below after completion. Python 3.12 on Windows;
Python 3.13/3.14 and Linux are not locally claimed. Tests use disposable databases,
temporary private storage and captured/mocked email. No ordinary development or
production DB migration occurs. Final frontend_build is generated in its own final
commit and verified against a subsequent build. No dependency/lockfile change.

## Manual verification and limits

In an isolated environment on this branch with P1 migrated, use synthetic data:

1. Prepare an application, select an owner-approved CV, edit the letter and save.
2. Review that exact saved revision. Compare visible text/order with both downloaded
   DOCX files; verify phone wrapping, keyboard operation and long optional sections.
3. Check the document-only wording; no checkbox is preselected and no email Send
   action exists. Approve, reload and confirm the same recorded proof.
4. Edit/select another CV: the current preview/checkbox clears. Save a new revision;
   it requires a new review/approval. Older proof remains explicitly historical.
5. In two tabs, approve/save concurrently. A stale approval must conflict or remain
   attached solely to its original revision; never to the new one.
6. Confirm external-site submission still records only the user's report, and
   sent/dismissed packages can be read without offering another approval.

Browser, phone and Word/Google Docs manual comparisons remain **UNVERIFIED** in
this package. The current root Docker lesson is an older checkout and does not
display these features. This preview is not a pixel renderer. Current generated
documents contain no tables; unexpected tables are rejected rather than omitted.
P2's browser-history navigation warning limit and 20-recent-CV chooser remain.
No historical approval/consent is inferred from legacy documents or test reports.

Filesystem edits cannot be transactionally locked by the SQL claim. Approvals bind
the verified hashes at that time; downloads and future delivery must recheck bytes.
No current delivery integration consumes this proof. Before P4, review exact send
authorization, recipient/Reply-To, consent, budgets, suppression, attachments and
unknown-outcome reconciliation. Real employer/alert delivery remains unapproved.

## Rollout/rollback boundary

No deployment is included. A future separately approved release must back up,
stage/review/apply P1's expected migration before activation, then deploy paired
reviewed server/client. Stop for any unexpected migration. Keep private media and
email-disabled boundary. Routine code rollback retains new tables, rows, newer
writes and files; never reverse populated P1 or restore old DB over newer writes.
Do not roll back to the old ungated email sender. No runtime approval-disable or
sending-enable switch was introduced.

Suggested size: **5 points**, AJ-17 application workflow. Jira-ready:
**Review exact saved application documents and record explicit document approval |
AC: owner-only no-store preview/download, verified saved hashes, latest-revision
explicit/idempotent approval, stale/concurrent protection, no delivery side effects,
historical evidence retained and complete gates pass.**

Stop for P3 review; no P4/P5 implementation or sending is authorized by this handback.

## Final outcomes — 20 October 2026

- Backend system check: no issues; migration drift: no changes. Full suite:
  **247 tests run in 154.934 seconds, OK with one existing Windows symlink skip**.
  Synthetic 5xx structured events are expected failure-path coverage, not production
  incidents or provider sends.
- Explicit stress suite: **20 passed in 59.746 seconds**, ten duplicate-approval
  races and ten approval-versus-new-revision races, with distinct unittest instances.
  No duplicate approval or approval of an unreviewed new revision was observed.
- Node **v24.19.0**; locked installation: 180 packages installed, 181 audited, zero
  reported vulnerabilities. Final lint: no warnings. Full Vitest: **86 passed across
  14 files in 9.56 seconds**. Final build: 1.19 seconds. An earlier successful run
  warned about state updates in an effect; a keyed review session now resets state
  without that effect, and the complete frontend gates passed again.
- Generated build: **21 files matched** a subsequent verification build (1.08 seconds),
  normalizing only index.html line endings. Final generated assets are committed
  separately after source/review notes. `git diff --check` passed.
- Manual browser, phone and document-viewer checks remain unverified as listed
  above. No ordinary development/production DB was migrated and no real sending
  was enabled. No Docker lesson file, unrelated root change, stash or Git identity
  configuration was changed.

Stress execution used a DiscoverRunner subclass whose build_suite constructs ten
fresh instances of each of these tests (normal Django label lists deduplicate):
`jobs.test_package_review.PackageApprovalConcurrencyTests.test_simultaneous_identical_approvals_create_only_one_proof`
and `jobs.test_package_review.PackageApprovalConcurrencyTests.test_new_revision_and_approval_race_never_approves_the_new_unreviewed_package`.
It ran through the same Python/environment definitions above, with interactive=False,
failfast=True and verbosity=1. Final author/committer verification uses the non-empty
`git log --format="%h %ae | %ce" ae8d05f..HEAD` range against the configured noreply identity.
