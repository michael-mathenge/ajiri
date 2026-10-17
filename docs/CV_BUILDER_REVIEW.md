# Personal CV builder review

17 October 2026. Branch `codex/cv-builder-flow`, based on approved schema commit
`42eaa4d`. Suggested estimate: 8 points. The reviewed UI polish and schema commits
remain in this local batch. No push, deployment, real email or production actions.

## Delivered behavior

Profile links to `/cv-builder`. A user explicitly starts a draft copied from their
profile, then edits contact details, summary, skills, employment, education,
certifications and projects. Optional sections can be omitted. Changes do not
alter account identity, Profile or existing applications. Profile changes do not
silently rewrite a draft. No inference, external AI, CV parsing or new dependency.

Save and preview validates and saves the draft, showing the server's exact content
layout. The user explicitly approves the saved revision/hash before downloading
that version. HTML and DOCX share section order and plain text; pagination/fonts
can differ. Editing hides current download and requires new approval after saving.
Earlier approved snapshots remain explicitly labelled and downloadable (latest 20
listed). Duplicate approval returns the existing version, with no extra document.

The retained `/api/profiles/me/generate-cv/` URL serves only a matching approved
version, otherwise JSON 409 directing the user to review. Existing uploaded CVs,
job cover-letter generation and application snapshots remain unchanged. No real
application sending is added. Linking applications to the selected approved CV
is a future reviewed package; the personal builder explains that separation.

## Integrity, concurrency and privacy

- Expected revision is compared in an atomic SQL write; stale saves return 409.
  Approval's conditional write acquires the SQLite writer lock. Concurrent edit
  invalidates approval; concurrent approvals produce one row and one file.
- Approval stores canonical content hash, template version and exact DOCX hash.
  There are no approval update routes. Administrative/direct ORM changes must
  preserve immutability. Downloads verify size/hash and never regenerate corrupt
  or missing content. Ownership checks return 404 for another owner's version.
- Files use existing private storage, UUID names, neutral download filenames and
  the configured private file permissions. Content is capped at 100 KiB, DOCX at
  2 MiB. Unsupported XML control characters fail validation.
- All new endpoint responses, including errors, use private/no-store. CV content
  is held in component memory, not browser storage or logs. Preview text is escaped.
- Failed approval transactions remove only their own newly written file. Hard
  process crashes or filesystem cleanup failure can leave orphan files. Deleting
  an approval/account removes its file only after DB commit; rollback retains it.
  Orphan reconciliation is report-only; there is no automatic retention pruning.

## Actual verification

Executed 17 October 2026 in the isolated checkout, with dotenv disabled,
DEBUG=True and REAL_EMAIL_ENABLED=False:

- Backend `check`: no issues; `makemigrations --check --dry-run`: no changes.
- Full Django suite: 202 tests, OK, one existing Windows symlink skip, 124.567s.
- Final focused CV workflow/schema suite after small start-idempotency and XML
  validation refinements: 24 tests passed, 28.045s.
- Frontend using bundled Node 24.19.0: locked `npm ci` (zero reported
  vulnerabilities), lint, 59 component tests across nine files and Vite build passed.
- Tests exercise explicit start, full section round-trip, consent, revision/hash
  conflicts, unchanged historical bytes, duplicate/concurrent approval, private
  ownership, corrupt/missing/oversized files, DB/storage failure, account-deletion
  commit/rollback, no profile-to-draft rewrite, field errors and escaped preview.
- `git diff --check`: passed. No provider or production requests were made.
- Browser/mobile visual QA, screen-reader behavior and Word/LibreOffice pagination:
  **UNVERIFIED**, manual checklist below. Automated tests inspect DOCX text/bytes.

## Manual local review

Use a local test database/media folder, never production. If this isolated checkout
has not applied approved migration 0005, inspect the local plan first. In PowerShell:

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:REAL_EMAIL_ENABLED = 'False'
.\.venv\Scripts\python.exe manage.py test profiles.test_cv_builder profiles.test_cv_schema --noinput
```

The tests create their own disposable database and temporary private files; no
local/production migration is applied by this test command. For a running local
preview use your normal local backend setup and frontend dev command, with real
email off. Do not point a dev frontend at production.

1. Log into a local test account. Open Profile → Build and review my CV. No CV is
   created merely by visiting. Click Start my CV and confirm the profile snapshot.
2. Enter details, add/remove optional entries, and leave some sections empty.
   Save and preview; check every section and date. Try an end before a start date:
   errors display and entered values stay. A missing name prevents approval.
3. Approval button is disabled until the explicit review checkbox is checked.
   Approve, download DOCX and open it in Word/LibreOffice. Compare all text with
   the preview; confirm empty sections and fabricated qualifications are absent.
4. Edit a field: current download disappears. Save and approve the revised CV.
   Earlier version download remains labelled and unchanged. Updating Profile
   independently must not silently modify either saved CV version.
5. Open two tabs. Save an edit in one; a stale save/approval in the other returns
   409 and retains entered edits for copying before reload. No automatic retry.
6. Check mobile/narrow layout, keyboard traversal, light/dark themes, long text,
   screen-reader labels, and actual DOCX pagination. Browser visual and Word
   verification remain manual; no real user information is needed for testing.

Unsaved changes warn on reload/closing and link clicks. Browser Back/Forward and
programmatic route changes are not fully blocked by the current BrowserRouter;
save before using them. No browser storage copy is made. A lost network response
can mean a save/approval committed: reload safely to reconcile rather than assume
failure or auto-retry. Before reloading, preserve any unsaved text privately.

## Backup and orphan review (future release operator)

Existing SQLite backup plus paused-writer private-media backup includes CV tables
and files. Verify both together in an isolated restore. New file storage paths
must stay unmapped publicly. For report-only reconciliation on the existing local
filesystem storage, with writers paused, compare CVApproval.document references
under `approved-cvs/` with regular files in that private subdirectory. Report counts
of missing/unreferenced files first; inspect details privately, never paste CV paths
or contents into logs/chat. Do not delete candidates automatically. Approval and
backup retention remain subject to the privacy review.

## Release and rollback boundary

No additional migration beyond reviewed profiles/0005. Future deployment must
follow verified backup → stage code → inspect/apply 0005 → activate matching
server/frontend. Stop on any unexpected migration. Old frontend tabs may need a
reload when the legacy immediate download begins returning 409.

Revert the matching code/client pair together while retaining new tables, files
and newer writes. Old code ignores these tables but resumes immediate generation;
therefore it loses the approval guarantee. Do not advertise the builder until a
forward fix is ready. Never reverse 0005 or restore an old DB routinely.

Stop for package review. Push/deployment, real application email, job-alert defaults
and application integration are not part of this handback. Original checkout
AGENTS/lockfile/coverage, Git configuration and stash remain untouched.
