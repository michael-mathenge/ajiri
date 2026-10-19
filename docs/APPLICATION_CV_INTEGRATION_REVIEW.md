# Approved CV → application drafting review

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

17 October 2026. Branch `codex/application-approved-cv`, base `5380fe1`.
Suggested estimate: 5 points. Implements the reviewed development direction and
`APPLICATION_CV_INTEGRATION_DESIGN.md`. Local batch only; no push or deployment.

## Delivered

- Job Detail fetches a small private owner-only version list, without CV content,
  contact information or storage paths. The selector suggests the current approved
  revision, labels earlier approvals and offers a selected-version download.
  An unapproved current draft never silently falls back to an earlier approval.
- New application preparation requires `cv_version`, validates ownership and
  file integrity, and copies exact bytes into Application.generated_cv. Current
  Profile edits never regenerate or change that approved CV snapshot.
- The job-specific letter and initial email remain based on the current Profile,
  as explained in the UI. Their review/send flow remains separate and unchanged.
- Existing applications return unchanged (200); selection does not replace their
  snapshots or resend them. My applications remains accessible without a new CV.
- Missing selection returns JSON 409 with code cv_approval_required. Malformed
  UUID returns field-keyed 400; unknown/other-owner approvals return 404; missing
  or corrupt selected files return generic 503 before creating an application.
- The existing user/job unique constraint arbitrates concurrent preparation.
  The losing request returns the winner or a safe retryable error on SQLite lock
  contention, and removes its own temporary snapshots. Partial file/DB failures
  clean the files already created by that request. No automatic POST retry.
- Snapshot filenames use neutral UUIDs, excluding untrusted employer/path text.
  Existing uploaded CVs, applications and approval versions remain unchanged.

No models/migrations, auth, CORS, ingestion, workflow, dependencies or sending
changes. The preceding ingestion reliability fix remains in the local batch.
New schema provenance is not claimed: the selected approval UUID is not stored on
Application; its verified document bytes are preserved as the independent snapshot.

## Actual verification

Executed 17 October 2026 in the isolated checkout, with dotenv disabled,
DEBUG=True and REAL_EMAIL_ENABLED=False:

- Backend system check: no issues. Migration drift check: no changes.
- Focused drafting/lifecycle/private-media/concurrent-send suite: 33 tests, OK,
  one Windows symlink skip, before the final metadata-list test was added.
- Initial full suite identified one legacy filename test still omitting CV
  selection. Its fixture now supplies an approved CV and retains its random-name
  assertion; focused rerun passed. Final full suite: 209 tests, OK, one existing
  Windows symlink skip, 120.447 seconds.
- Frontend locked `npm ci`, lint, 63 tests in ten files and production build passed
  on bundled Node 24.19.0. The last package commit refreshes frontend_build.
- The earlier ingestion helper's nine offline tests still pass.
- Tests verify exact bytes after Profile edits, unchanged existing drafts, missing
  selection, cross-owner/unknown IDs, corrupt/missing files, partial file/DB failure,
  concurrent uniqueness/cleanup, metadata privacy, explicit version selection and
  no automatic retry or message sending during preparation.
- `git diff --check`: passed. Browser/mobile visual checks and opening documents in
  Word/LibreOffice remain **UNVERIFIED**, with the manual checklist below.

## Manual local review

Use synthetic data with real email disabled and the approved CV migration applied
only in your usual local development environment. PowerShell focused test command:

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:REAL_EMAIL_ENABLED = 'False'
.\.venv\Scripts\python.exe manage.py test jobs.test_approved_cv_application --noinput
```

1. Without an approved CV, open a job. Preparation is disabled and the builder
   link is offered; browsing and My applications remain available.
2. Build and approve a CV. Return to the job: current approved revision is
   selected. Download it for reference. Prepare application; confirm the UI opens
   My applications without sending anything.
3. Download the application CV and compare its hash with the selected approved
   CV. They must match. Review the independently drafted letter/email too.
4. Change Profile or create a newer approved CV. Open the existing application:
   its original snapshot must remain unchanged. Selecting a newer CV and clicking
   Prepare on that job opens the existing application; it does not replace files.
5. Select an explicitly labelled earlier approved version for another job. Verify
   the new application uses those earlier bytes, not the current Profile/CV.
6. Check keyboard/narrow-phone/light/dark layout. On a network failure, follow the
   My applications guidance to reconcile before manually retrying; no auto retry.

For the hash comparison, save both local test downloads in a temporary private
folder, then run PowerShell with their actual paths:

```powershell
Get-FileHash 'C:\path\Selected_CV.docx', 'C:\path\Application_CV.docx' -Algorithm SHA256
```

Expected: identical Hash values. Never upload either CV or paste its contents.

## Limits, release and rollback

Browser visual QA and external Word/LibreOffice layout remain manual. Latest 20
approvals are listed; earlier versions require their explicit known owner URL.
Letter/email still reflect current Profile and can differ from selected CV contact
details: review them carefully. Application redrafting/replacement is not added.
Crash/storage cleanup failure can leave orphan files for private report-only
review; no automatic pruning. No new sending capability has been activated.

Future batch deployment still requires backup → stage code → inspect/apply approved
profiles/0005 → activate matching backend/frontend. No extra migration here. Old
tabs attempting new applications without cv_version must reload and select an
approved CV. Existing drafts/sent application downloads remain compatible.

Rollback matching source/client/build together, keeping schema, saved files and
newer writes. Old code resumes Profile-based CV generation and loses this
approval-selection guarantee; prefer a forward fix. Never restore an older DB
over newer application writes as a routine rollback.

Stop for review with the local batch intact. Original checkout AGENTS/lockfile,
coverage data, stash and Git configuration remain preserved.
