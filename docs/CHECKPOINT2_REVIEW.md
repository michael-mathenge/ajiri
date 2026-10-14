# Checkpoint 2 review

15 October 2026, Africa/Nairobi. Local review candidate on
`integration/checkpoint-2`; main and origin/main remain at reviewed Checkpoint 1
merge `e5e0038`. Checkpoint 1 tip `b8c1881` was verified as an ancestor after fetch.
The first Checkpoint 2 commit, `a384ba4`, was documentation only. The design was
approved, then Prompt 2 authorized WP7-WP10. The bracketed examples in that prompt
were treated as template notes, not an instruction to choose option B: approved
recommendation A was implemented. No push or deployment has been performed.

## 1. Package summary

| WP | Status | Branch | Source commit range | Suggested points |
|---|---|---|---|---:|
| WP7 | done locally; host cutover pending | feature/private-media | a384ba4..b9037d0; safety follow-up 275d360..84461a3 | 8 |
| WP8 | done locally | feature/send-idempotency | 23dd56f..064f436 | 5 |
| WP9 | done locally; live Actions unverified | feature/ci-frontend-tests | fea344b..79676ef | 1 |
| WP10 | done locally | feature/deployment-checklist | 253ca45..feature/deployment-checklist | 3 |

Ranges exclude integration merges. WP10's final hash can be resolved with
`git rev-parse feature/deployment-checklist`. WP7's branch was fast-forwarded to
the integration tip before its safety follow-up; the two ranges identify its
actual changes without attributing intervening WP8/WP9 work to it. All packages
merge with --no-ff. Story points are relative suggestions for Michael's tracker,
not delivery-time estimates. No tracker changes were made.

## 2. What changed

### WP7 — Private storage and relocation

- MEDIA_ROOT now uses an absolute PRIVATE_MEDIA_ROOT, defaulting outside the repo
  to `C:\dev\ajiri-private-media` in this local layout. New Linux files/directories
  use 0600/0700. Database relative names and FileField definitions are unchanged.
- Django no longer serves media even under DEBUG=True. The SPA fallback continues
  to exclude media. Auth, CORS, owner download endpoints and their headers/statuses
  are unchanged. Default serializer legacy URL fields remain, but do not serve files.
- `relocate_private_media` defaults to dry-run and copies only on explicit --apply;
  --verify is read-only. It preserves bytes/names and never deletes source files,
  rewrites rows, or regenerates application snapshots. It includes orphan files.
- The command rejects unsafe names, links/junctions, overlapping/public roots,
  missing referenced files, conflicts and insufficient space. It verifies hashes,
  publishes copies without overwriting, resumes identical copies, and can write
  a protected apply manifest. Unreadable directories abort instead of disappearing
  silently from an inventory. Manifests are outside both roots and known assets.
- Updated time-bound AGENTS sections for Prompt 2, the example config, deployment
  guidance and concepts. Standing sections remain unchanged; checkpoint-specific
  exceptions and the new integration branch are recorded in the mission.
- No new migration. Real user database/media were not relocated or modified.

### WP8 — Concurrent send protection

- One autocommitted conditional update claims ready_for_review as sent before
  email delivery. Competing requests get 400 even when they read stale READY data.
- A delivery exception returns the existing safe 502 and conditionally releases
  only that claim, restoring ready_for_review and a null sent_at for retry.
- A stale dismissal cannot overwrite a concurrent send claim. No new status,
  schema, auth change, long-running DB transaction or dependency was added.
- Threaded in-flight/stale-read test proves one captured email. Separate tests
  cover failure/retry and stale dismissal; existing lifecycle tests still pass.

### WP9 — Frontend CI tests

- Only one workflow line was added: `npm run test -- --run`, between lint and
  build, exactly as CI_PROPOSAL specifies. Optional backend email configuration
  and interpreter-comment changes were not applied; the hosting account was not
  inspected. Python 3.12/3.13/3.14 and all existing checks are unchanged.
- Exact patch/indentation/order and matrix invariants were checked locally.
  No standalone YAML/Actions schema validator was available; no parser-validation
  claim is made. Actual Actions execution remains required before merging.

### WP10 — Deployment checklist

- `DEPLOYMENT_CHECKLIST.md` covers writer freeze, mapping removal, consistent
  SQLite/media backups, staging code and migrating before reload (including
  jobs/0007), dry-run/copy/verification, private-root configuration, permissions,
  post-deploy tests and privacy-preserving rollback.
- Every hosting instruction is for Michael to perform after review. No web app,
  mapping, environment, production database, mail service or scheduled caller was
  changed by Codex.

## 3. Verification evidence

Environment: Python 3.12.6, Node 22.15.0, npm 10.9.2. These are executed local
checks, not CI results, coverage measurements or a production security audit.

Backend command group, per package:

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test --noinput
```

Tests used their own database and temporary media. Agent test runs used an ignored
writable TEMP/TMP under `.npm-cache/test-tmp`. No live `migrate` or relocation ran.

Frontend command group:

```powershell
cd C:\dev\ajiri\ajiri-frontend
npm.cmd ci
npm.cmd run lint
npm.cmd run test -- --run
npm.cmd run build
```

WP7/WP8 used the equivalent direct `vitest.cmd run`; WP9 and final WP10 used the
exact npm CI invocation above, which resolved to `vitest --run`. Clean installs
used the ignored local npm cache and bounded fetch timeouts.

| Stage | Django check / migration drift | Backend results | Frontend results |
|---|---|---|---|
| WP7 initial | pass / none | 67 run: 66 passed, 1 skipped; final 11-test focused pass, 1 skipped | install, lint, 24 tests, build pass |
| WP8 | pass / none | 71 run: 70 passed, 1 skipped, 43.528s | install, lint, 24 tests, build pass |
| WP9 | pass / none | 71 run: 70 passed, 1 skipped, 58.050s | exact proposed commands pass; 24 tests |
| WP7 safety follow-up | pass / none | 72 run: 71 passed, 1 skipped, 38.877s | unchanged frontend; preceding WP9 gates apply |
| WP10/final | pass / none | 72 run: 71 passed, 1 skipped, 59.000s | install, lint, 24 tests (17.05s), build pass |

The skipped test requires creating a symlink, which Windows denied without
developer mode/privileges. Link rejection code is present; a Linux execution is
still needed. Initial relocation tests could not create hard links inside the
sandbox; the same isolated tests passed with the required execution permission.
An initial frontend clean install also hit Windows sandbox mkdir restrictions;
the permitted retry passed. These are resolved environment failures, not hidden
passing test claims. No unresolved failing test remains in the runs above.

Ajiri Vite was temporarily stopped to release the previously diagnosed Rolldown
binary lock and is restored after all install/test gates complete. The other project's process was left alone. npm clean installs
reported zero known vulnerabilities in their recorded output.

No frontend source changed and frontend_build was not regenerated. The 18 dist
files match committed build content after CRLF/LF normalization; two generated
assets differ bytewise in the Windows working checkout due to CRLF conversion.
Linux Actions' exact tree comparison has not been run locally. Main JS remains
384.92 KB raw / 125.57 KB gzip and CSS 19.31 KB / 5.22 KB gzip.

`git diff --check` and standing-section comparison passed. The final identity audit
uses `git log --format="%h %ae | %ce" origin/main..integration/checkpoint-2`.
Every line must show `11541427+michael-mathenge@users.noreply.github.com` for
both author and committer; this is checked again after WP10 is integrated.
Git configuration was never changed.

## 4. Michael's manual review script

### Media isolation, local synthetic environment first

1. Review `PRIVATE_MEDIA_DESIGN.md` and `DEPLOYMENT_CHECKLIST.md`. Existing files
   remain in the old root until you deliberately copy them; owner downloads can
   return 404 under the new root until relocation is completed. Do not fix this
   by restoring a public route/mapping.
2. Back up local DB/media and stop writers. For production use the full manual
   checklist; do not point local tests at production paths. In PowerShell:

   ```powershell
   cd C:\dev\ajiri\ajiri-backend
   $oldMedia = 'C:\dev\ajiri\ajiri-backend\media'
   $newMedia = 'C:\dev\ajiri-private-media'
   .\.venv\Scripts\python.exe manage.py relocate_private_media --source $oldMedia --destination $newMedia --dry-run
   ```

   Expected: no file/DB changes; totals and orphan count. Resolve missing references
   and conflicts before continuing. For apply/manifest/verify and server-root setup,
   follow the checklist with local absolute private paths. An existing different
   file at a destination name must fail instead of being overwritten or renamed.
3. Apply/verify the copy only after backup and write freeze. Compare relative DB
   names and file hashes before/after; source files remain. Repeat apply without
   reusing the manifest path: identical copies succeed and do not duplicate rows.
4. With DEBUG=True and then DEBUG=False, request known uploaded-CV and saved
   CV/letter `/media/` paths, using GET and HEAD. Expect 404, no bytes, redirect or
   SPA success. A guessed/encoded traversal path must also fail. At PythonAnywhere
   repeat against the actual web server after removing every alias/parent mapping.
5. Sign in as the owner: download uploaded CV and both saved application documents
   using Profile/Applications. Expect exact original content, correct attachment
   filenames and private/no-store headers. Edit the profile: snapshots must stay
   unchanged. Fresh generated documents should reflect profile edits.
6. Sign in as another user and request the first user's snapshot API IDs: 404.
   Without a token: 401. The second user's uploaded-CV endpoint only returns their
   own CV (404 if absent), never the first user's file.
7. Upload a synthetic CV and prepare a synthetic application. Verify new files
   exist only in the private root. Test captured email attachments, missing-file
   404 and normal login/refresh/logout. Do not submit to a real employer.

### Double-send and retry

Run the explicit regression group without needing a running server:

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py test jobs.test_send_concurrency --noinput
```

Expected: three tests pass. First request pauses at delivery; the overlapping
stale request receives 400; releasing the winner gives 200 and exactly one
captured email. Delivery failure gives 502, restores reviewable state, then retry
succeeds once. Stale dismiss is 400 and cannot undo sent state.

For UI verification, use console/captured mail in a local/staging environment and
a synthetic email listing. Prepare one application, open two tabs and approve both
drafts, then trigger both sends. Expect one success, one 400 and one captured
message. This is a smoke check; the deterministic automated test proves overlap.
No production mail settings should be changed just to exercise this script.

### CI and deployment review

Inspect the single-line workflow diff and run the frontend command group above.
After Michael pushes a review branch/PR, require actual GitHub Actions success
for all existing Python versions plus frontend tests/build consistency. Then
follow DEPLOYMENT_CHECKLIST manually; this report does not authorize deployment.

## 5. Decisions and why

- Private root plus no direct media route provides isolation in development and
  production; random names alone cannot protect a leaked URL. Platform mapping
  removal remains a manual requirement outside Django's control.
- Changing the root rather than FileFields preserves DB values and avoids schema
  changes. Copy/checksum/retain-original supports recovery without deleting data.
- A conditional SENT claim is a small portable change for SQLite, avoiding a new
  intermediate status, schema or open transaction around SMTP. Its visibility
  and crash ambiguity are explicit trade-offs, not exactly-once guarantees.
- Dismiss uses a conditional write too, so it cannot undo the send claim after a
  stale read. Existing owner permissions and normal 400/502 behaviours are kept.
- CI applies only the approved mandatory step; optional environment/comment
  changes were left out. Public/frontend assets are unchanged.

## 6. Open risks, assumptions and unverified work

- **Not deployed:** public PythonAnywhere media mappings can still expose files
  until Michael removes them and completes cutover. Application code cannot
  block a platform static mapping. No production access/mapping audit occurred.
- **Existing local files need relocation:** root selection changes immediately
  when updated backend code loads. Originals are intact; missing downloads need
  the planned copy/configuration, not regeneration or a public route.
- **SMTP is not exactly-once:** the claim prevents competing sends, but a crash
  can leave sent before delivery, and a provider can accept mail then raise.
  A resulting 502/retry may duplicate mail in that ambiguous provider case.
  Reconcile operational evidence before manual reset; no automatic timeout reset.
- **Host/Linux checks pending:** PythonAnywhere owner permissions, actual static
  mapping removal, Linux hard links/symlinks and Python 3.13/3.14 are unverified.
  No dedicated YAML/Actions validator or live Actions run occurred.
- Copies and backups consume space; quiescence is required. Replacing/reuploading
  files during copy can invalidate inventory. Unexpected DB/filesystem changes,
  missing snapshots, quota errors and conflicts must stop cutover.
- Backups/manifests may contain personal filenames and must remain private.
  Publicly downloaded/cached historical copies cannot be recalled. Retention and
  incident assessment require product/operational decisions, not automatic deletion.
- The first required clean install may briefly interrupt local Vite. Local test
  results do not establish browser/device or live SMTP behaviour.

## 7. Suggested story points

WP7: **8**, WP8: **5**, WP9: **1**, WP10: **3**. Total **17** suggested points;
Michael owns estimation and tracker updates. Preparation/design is separate.

## 8. Recommended next sprint

1. Review this candidate and run actual Linux/matrix CI on a PR.
2. Rehearse backup, relocation, restore and unmapped storage on staging; agree the
   maintenance window, recovery owner and private retention policy.
3. Perform the approved PythonAnywhere cutover manually and record real evidence.
4. Scope durable outbound-mail reconciliation/outbox/provider idempotency for crash
   and ambiguous-ack recovery, without silently resetting uncertain sends.
5. Continue broader accessibility/device/network checks and product scoping when
   this privacy checkpoint is accepted.

Checkpoint 2 stops for Michael's review. No deployment, push or further feature
implementation is authorized by this report itself.
