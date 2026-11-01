# Ajiri maintenance history and reference

Consolidated 1 November 2026. This is the single reference for superseded
checkpoint plans, reviews, decision forms and archive copies removed during cleanup.
The reviewed release is the canonical copy; checkouts receive it by updating Git.

## How to use this file

1. Read the maintenance map and completed-work summary first.
2. Use the four maintained technical guides for changes and operations.
3. Check the pending-work summary before starting something that already exists.
4. Expand a dated record only when you need its exact review, test or design details.

**Historical instructions are evidence, not commands to execute or new approval
requests.** Old source SHAs, test counts, expiry dates, proposal defaults and
"not implemented/not deployed" statements apply to their date. Current source,
Jira acceptance, owner instructions and actual runtime evidence take precedence.
This document does not authorize production actions, sending, purchases or deletion
of user data or backups. The initial consolidation made no production inspection;
the later explicitly authorized cleanup checks are recorded below.

## Maintenance map

| Need | Use |
| --- | --- |
| Deployment, private backup and safe rollback | [Deployment checklist](../docs/DEPLOYMENT_CHECKLIST.md) |
| UI tokens, components, mobile and accessibility conventions | [Design system](../docs/DESIGN_SYSTEM.md) |
| Request limits, proxy assumptions and 429 behavior | [Throttling reference](../docs/THROTTLING.md) |
| CV file structure/size validation and scanner limitations | [Upload validation](../docs/UPLOAD_VALIDATION.md) |
| Authentication/private-download implementation concepts | [Backend concepts](../ajiri-backend/docs/CONCEPTS.md) |
| Old checkpoint reviews, approvals, migrations and results | Expand the relevant record below; do not repeat it as an open task |

On the reviewed-source worktree, `docs/ROADMAP_NEXT_ACTIONS.md` holds the full
ordered pending-work list and `docs/JIRA_ROADMAP_PROGRESS.md` remains the active
execution ledger. Those current documents are not replaced by this history file.
The original checkout contains older source; documentation cleanup does not
upgrade its application code or change its branch.

## Completed work: what to retain rather than rebuild

| Area | Completed capability / lesson | Maintenance rule |
| --- | --- | --- |
| Checkpoint 1 / Phase 1 | Profile/API gaps, registration/application/notification UI, CV upload and download, mobile UI and component-test foundation | Preserve all field-keyed validation errors, 20-row pagination, accessible controls and immutable application documents. Prices were previews, not live entitlements. |
| Checkpoint 2 | Private owner-authenticated documents, relocation tooling, conditional application-state claims and CI component tests | No public media mappings. Relative FileField names are not public URLs. A second caller must not repeat a claimed external effect. |
| Security hardening | Password checks, request throttles, bounded structural uploads and deployment settings | Content validation is not malware scanning. Request throttles are approximate, not hard email quotas. Verify actual proxy topology instead of guessing it. |
| Cookie CSRF / account flows | Coordinated CSRF and JWT handling, later verification/reset and revocation work | Keep refresh tokens in httpOnly cookies; preserve rotation/blacklisting and public-endpoint interceptor exclusions. Old "design only" notes are historical. |
| Delivery and consent | Shared receipt/budget ledger, immutable application review/authorization, independent alert consent and unsubscribe | Provider acceptance is not inbox arrival. Never auto-retry an unknown handoff or infer consent from an old preference. |
| Owner pilots | Owner application inbox/content and alert/unsubscribe evidence recorded; owner inbox delivery reconfirmed 1 November | Do not repeat completed pilots as missing work; broader normal-path acceptance remains separate. |
| Privacy and recovery | Registration/privacy boundaries, verified-owner data operations, private backups and isolated restore tooling | No inferred historical consent. Actual erasure requires a verified owner request; backup retention remains report-only. |
| Showcase / runtime | Introduction and CV workflow deployed; later MVP1 source `3408565` (PR72) recorded deployed on 1 November without new migrations | Account-security mail configured; employer/search/public/application/alert exclusions off at that release; freshness on. These are recorded observations, not fresh checks. |
| Backup operation | 26 October scheduled backup and 17-file restore completed; MVP1 off-server recovery also verified | Check each later run's receipt; do not keep listing the first run as unverified. Preserve desktop availability limits. |
| Feed display | Default-off labelled browsing prepared on `codex/job-feed-display`; consult the release receipt for exact merged/deployed revisions | Preserve strict eligibility. Display-only jobs offer no application/send/document-generation actions; scams and known closed jobs stay hidden. |

Last recorded hosting expiry was **30 November 2026**, replacing older 14/19
November dates. Post-cleanup quota observed on the hosting dashboard was **228.7/512 MB (45%)**,
with approximately 283.3 MB headroom, superseding 482.4/512 MB. Recheck before a
release or storage-heavy activation; this observation is not a capacity guarantee.

## Maintenance workflow

### 1. Establish the actual source and scope

```powershell
Set-Location C:\dev\ajiri
git status --short
git branch --show-current
git log -1 --format="%h %s"
```

Expected: the actual dirty files, branch and local commit, not proof of deployment.
Preserve unrelated changes, stash and Git configuration. Work from the reviewed
release source in an isolated branch; reconcile existing implementation first.
The original checkout and the job-feed-display worktree intentionally differ.

### 2. Make and verify a bounded change

- Check the current Jira criteria and choose the smallest missing behavior.
- Use Python 3.12 / the project's pinned Django environment and Node 24.19 with
  locked installation. Run Django check, migration-drift check and full tests;
  frontend npm ci, lint, component tests and build where the package requires them.
- Record actual output and limitations. Old passing counts are historical evidence,
  not a replacement for checking changed code. Do not send real mail in tests.
- Preserve models/migration history and protected auth/CORS/ingestion behavior.
  Any newly needed migration for the feed-display task must stop for review.
- For frontend packages, regenerate the matching frontend_build and commit it last.
  Pass required CI before an authorized merge. No release action follows from
  this documentation cleanup alone.

### 3. Prepare an authorized release

Use the maintained deployment checklist: establish the exact source and previous
runtime, check capacity, pause relevant writers, verify a private backup/off-server
isolated restore, then apply only approved additive migrations before serving new
code. Verify health, HTTPS, owner-only documents, asset hashes and feature switches.
Record source versus deployed source separately. Rollback preserves newer writes,
receipts and private documents; it is not an old-database overwrite.

### 4. Diagnose without unsafe shortcuts

| Symptom | Check first | Do not do |
| --- | --- | --- |
| Empty job board | Eligible versus display-only counts, source evidence, deadlines, scam flags and intended switch | Invent deadlines, seed fake eligible vacancies or relax sending eligibility |
| Mail missing | Correct path, consent/verified mailbox, authorization, receipt and provider/inbox evidence | Treat console output as delivery or repeat an unknown handoff |
| Private download denied | Authenticated owner endpoint, storage root, saved relative name and file availability | Expose media publicly to make a link work |
| 403 on refresh | Legitimate origin/CSRF/cookie flow against the matching server/client revision | Disable CSRF, rewrite rotation or expose refresh tokens in JSON |
| 429 | Request scope, Retry-After, NAT/proxy identity and cache topology | Retry mutations automatically or call LocMemCache a distributed quota |
| Upload rejected | Format structure, size/archive limits and preservation of the previous CV | Bypass validation/quarantine or call content checks a clean malware scan |
| Low disk / backup failure | Account quota, required transient space, private receipt and restore evidence | Delete retained backups or untracked user files without a specific authorized policy |

## Pending work snapshot: 1 November 2026

The last read-only Jira reconciliation returned 14 open non-Epic issues: 13 In
Progress and AJ-80 To Do. This is an orientation snapshot; use current Jira and the
reviewed worktree's next-actions list before implementation.

| Order / issue | Next steps |
| --- | --- |
| Capacity and hosting | Recheck quota/expiry; verify the latest backup receipt and off-server restore; resolve headroom before activation. No backup pruning is authorized. |
| Feed display, no new issue key assigned | Review local diff; prepare source/build commits; obtain authorization lifting the current no-push/no-production limit; pass CI before release and private switch activation. |
| AJ-17 / AJ-26 / AJ-43 | Review existing PR73 stage2 implementation and recorded CI; finish missing bounded callers and normal-path consent/provider/inbox acceptance. It is not deployed merely because the owner pilot completed. |
| AJ-53 / AJ-42 | Verify genuine employer authority/source/deadline; independent review; then verify authorized posting/public metadata and expiry. Display-only feed rows remain excluded from public JobPosting output. |
| AJ-52 / AJ-79 | Review existing inactive scanner/certificate work; settle actual engine/host, quarantine, signatures, quotas, capacity and recovery before activation. |
| AJ-47 / AJ-48 | Review existing storage/queue rehearsals; verify actual target/worker durability, interrupted recovery, single-writer cutover and uncertain-handoff handling. |
| AJ-51 | Confirm purpose/wording/lawful basis, retention/cohort/access and processing facts; verify independent versioned consent and withdrawal before collection. |
| AJ-44 / AJ-45 / AJ-46, last | Confirm genuine merchant/commercial facts; review existing adapters; verify actual sandbox status/reversal evidence and entitlement enforcement before considering live charging. |
| AJ-80 | Review the existing 23-entry mapping; approve exact descriptive titles/non-destructive links; preserve original comments/authors/dates/history. Do not run jira_sync.py. |

## Current cleanup operation — 1 November 2026

- HTTPS Stage B reconfirmed at 15:14 EAT: live production health returned HTTP200,
  status ok and exactly Strict-Transport-Security: max-age=300. AJ-12 remains Done;
  its description now leads with completed acceptance and comment10172 records it.
- Main-checkout pending work was preserved in stash
  `1eafb40a0cdde66575ad01b6aad10dfb7b8a93d7`; only safety ignores remain modified.
  Its former uncommitted document consolidation is therefore in that stash; the
  active maintenance reference remains available in this reviewed worktree.
- Delivery-concurrency documents were preserved in stash
  `25ad1cfb0e6909b707b160228e907d79b4a8ee71`; that worktree is clean.
- Job-trust reports were preserved in stash
  `f9f50a725a1743d1523223f5ad583e19e09d011f`; that worktree is clean.
- The named venv backup and seven restore folders were already absent when
  inspected. No new deletion of those absent targets is claimed.
- Before pruning there were21 backup-* snapshots; newest four are24October10:22UTC,
  25October,26October and31October. All four server verifications passed and their
  manifest hashes matched off-server copies. Existing isolated restores passed
  SQLite integrity and per-file hashes for17files/372876bytes each. The newest
  local media artifact is a browser-decompressed tar with a matching recorded
  uncompressed hash; the generic gzip-only check alone does not validate that form.
- After Michael's explicit at-action confirmation, the exact17 older snapshots
  were permanently deleted at12:33:36UTC (15:33:36EAT), removing114760909 logical
  bytes (~109.4MiB). All17 targets are absent and exactly four backup-* snapshots
  remain. All four passed the read-only server verifier again after deletion;
  their manifest hashes remain unchanged. Restore/venv-backup counts are both0.
- Private receipt: /home/Mathenge/ajiri-private-backups/prune-receipt-20261101T123336Z.json
  (mode0600, state complete). Dashboard now shows228.7/512MB (45%used).
  Off-server copies and other historical backup types were untouched. This is
  one-time authorized pruning, not a standing scheduler retention/deletion policy.

To restore a stash, use apply rather than pop so the saved copy remains available:

```powershell
git -C C:\dev\ajiri stash list --format="%H %s"
# Run the matching command only when you want that work restored:
git -C C:\dev\ajiri stash apply --index 1eafb40a0cdde66575ad01b6aad10dfb7b8a93d7
git -C C:\dev\ajiri\.worktrees\delivery-concurrency stash apply --index 25ad1cfb0e6909b707b160228e907d79b4a8ee71
git -C C:\dev\ajiri\.worktrees\job-trust stash apply --index f9f50a725a1743d1523223f5ad583e19e09d011f
```

## Consolidation receipt — 1 November 2026

- Removed 13 obsolete files from the original checkout and 32 historical files,
  archive copies and superseded indexes from the reviewed worktree.
- Preserved the substantive history in 37 expandable detail sections, with earlier
  checkout differences shown as compact patches instead of duplicated full text.
- Retained the four maintained screenshot guides. The old Checkpoint 2 deployment
  content is historical; the original checkout now has an updated maintenance checklist.
- Verified both reference copies match, all 45 selected original files are absent,
  all historical detail sections remain, 96 local Markdown targets and 90 record
  links resolve, and git diff --check passes in both checkouts.
- Preserved unrelated changes, private data, backups, source code, stash and Git
  configuration. No production access, sending, push, merge or new runtime-test
  claim was made. Historical document instructions were not executed.

## Historical detail index

| Topic | Expand the dated record |
| --- | --- |
| Initial UI/profile/job work | [Phase 1](#record-phase1-review), [Checkpoint 1](#record-checkpoint1-review) |
| Private documents and first deployment | [Checkpoint 2](#record-checkpoint2-review), [private media](#record-private-media-design), [old cutover checklist](#record-deployment-checkpoint2) |
| Security and refresh cookies | [Checkpoint 3A](#record-checkpoint3a-review), [CSRF design](#record-refresh-cookie-csrf-design), [deployment checks](#record-deploy-security-verification) |
| Early roadmap and decisions | [Checkpoint 3 plan](#record-checkpoint3-plan), [audit](#record-modernisation-audit), [old questionnaire](#record-decisions-needed), [working prompts](#record-roadmap-working-prompts) |
| Delivery and accounts | [Original email design](#record-smtp-email-design), [delivery service](#record-checkpoint3b-delivery-review), [accounts](#record-checkpoint3b-accounts-review), [account email](#record-checkpoint3b-account-email-review), [owner pilot](#record-checkpoint3b-pilot-review) |
| Schema, privacy and operations | [Schema review](#record-checkpoint3b-schema-review), [Phase A review](#record-checkpoint3b-phase-a-review), [Phase A deployment](#record-phase-a-deployment), [Checkpoint 4](#record-checkpoint4-phase-c-review) |
| Sprint and CI evidence | [Sprint 3 review](#record-sprint3-review), [Sprint 3 release](#record-sprint3-release), [implemented CI proposal](#record-ci-proposal) |
| Superseded maintenance lists | [26 October actions](#record-roadmap-next-actions-2026-10-26), [31 October decisions](#record-decisions-pending-2026-10-31), [prior housekeeping](#record-housekeeping-review), [old backend onboarding](#record-backend-readme-pre-first-release) |

## Dated source records

The expandable records retain substantive historical content, including superseded
instructions, tests, caveats and decisions. Repeated navigation stubs and duplicate
archive copies are folded into the inventory. Source hashes identify the inputs;
newline-normalized duplicates appear once. Internal links to deleted documents
point to their corresponding record here; unavailable old targets are shown as
historical paths rather than broken maintenance links.


<a id="record-checkpoint1-review"></a>

### checkpoint1 review

<details>
<summary>Read dated details — source variant 1</summary>

Source: `docs/CHECKPOINT1_REVIEW.md`; input SHA-256 `f1a3c761de13d272ec6f536d8b259f7f576506dae4c07c9d5811697c4c49c45b`.

# Checkpoint 1 review


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

Review date: 14 October 2026 (Africa/Nairobi).

Checkpoint 1 is implemented and locally verified. All six packages have passed their quality gates and are integrated on `integration/checkpoint-1`. Michael's review and approval are still required before merging into main or deployment. No checkpoint branches were pushed, and main remains at `cbd9ce7`.

## 1. Package summary

Commit ranges use Git's `base..tip` notation and exclude the integration merge itself. WP6's branch tip is its final build commit; resolve its exact hash with `git rev-parse feature/checkpoint-polish`.

| WP | Status | Branch | Commit range | Suggested points |
| --- | --- | --- | --- | ---: |
| WP1 | done | feature/profile-api-gaps | cbd9ce7..de1038f | 5 |
| WP2 | done | feature/register-applications-notifications | cff7605..22c1442 | 8 |
| WP3 | done | feature/profile-cv | 823f578..ef66f01 | 8 |
| WP4 | done | feature/subscriptions-ui | 1d3b992..01b718a | 2 |
| WP5 | done | feature/tests-and-ci | c801f65..c9610ed | 8 |
| WP6 | done | feature/checkpoint-polish | 86bc24c..feature/checkpoint-polish | 5 |

These are relative story-point suggestions for Monday.com, not measured delivery times. No Monday.com changes were made.

Each package branched from the integration branch and merged back with --no-ff. Each frontend package regenerated frontend_build once, in its final commit. WP5 produced identical production assets; its final empty build-verification commit deliberately records that result. The user's earlier instruction to stop after each feature was superseded by the checkpoint instruction to proceed through all packages.

## 2. What changed

### WP1: Profile API and notification delivery

- ProfileSerializer exposes writable notify_email and notify_in_app.
- The user-approved additive migration `jobs/0007_notification_in_app.py` adds Notification.in_app, defaulting existing records to True.
- Matching treats email and in-app delivery independently. Email-only receipts prevent repeat emails but are excluded from list and mark-read APIs. Both preferences off means no receipt is created.
- `POST /api/jobs/applications/{id}/dismiss/` is authenticated and owner-scoped. Draft/reviewable applications become dismissed; repeating dismissal returns 200. Sent applications return 400. Other users receive 404.
- New tests cover preferences, channel combinations, repeat sweeps, receipt visibility and dismiss permissions/states.

### WP2: Registration, applications and notifications

- Register normalizes and displays every DRF field message, including detail and nested errors, with aria-invalid/aria-describedby connections. Failed requests retain entered values.
- Applications show status badges and a review disclosure. Email sending requires explicit review approval; successful sends remove the send control. API 400 and delivery errors remain visible without removing the application.
- ApplicationSerializer adds a read-only employer_url for external applications. The UI requires opening the employer listing and separately declaring that submission happened there. It then records confirmation through the existing send endpoint; it does not submit on the employer's behalf.
- Dismissal uses an accessible confirmation dialog and preserves history/documents.
- Notifications show Read/Unread text, a busy mark-read action, pagination and existing loading/error/empty patterns.
- Vitest, Testing Library and the explicitly approved jsdom were installed as devDependencies early in WP2 to satisfy per-package tests. WP5 expands those tests.

### WP3: Profile and CV tools

- New protected Profile page edits full name, phone, headline, location, experience, bio, skills and notification preferences. Email remains read-only; no account-auth changes were made.
- Skills save through skill_names; an empty array clears them. Contact field limits now match the existing User model.
- CV uploads use a separate multipart request, with client and server validation for PDF/DOC/DOCX, a 5 MiB boundary (labelled 5 MB), and empty-file rejection. Invalid uploads preserve the previously stored CV.
- New owner-scoped download endpoints stream uploaded CVs and saved application document snapshots. Downloads send Cache-Control: private, no-store.
- DownloadButton requests blobs through the unchanged API client, retains silent refresh, uses server filenames and releases temporary object URLs.
- Profile offers generated CV download. JobDetail offers generated CV/cover letter; Applications downloads its saved snapshots.
- Tests cover contact/skill edits, clearing, validation boundaries, uploads, authentication, ownership and saved-snapshot behaviour.

Additional endpoints:

| Method | Path | Result |
| --- | --- | --- |
| GET | /api/profiles/me/cv/ | Uploaded CV attachment, or 404 if missing |
| GET | /api/jobs/applications/{id}/documents/cv/ | Saved application CV attachment |
| GET | /api/jobs/applications/{id}/documents/cover-letter/ | Saved application cover-letter attachment |

The existing GET /api/profiles/me/generate-cv/ and GET /api/jobs/{id}/generate-cover-letter/ remain authenticated DOCX generators.

### WP4: Subscription preview

- Public /plans page and shell link show Free / Starter / Pro at KES 0 / 499 / 999.
- Every card states preview-only and not yet purchasable. There are no checkout controls, payment calls, account-plan changes or invented entitlements.
- Billing periods, usage limits and detailed inclusions remain unconfirmed.

### WP5: Regression coverage and CI proposal

- Auth tests cover registration, password hashing/profile creation, invalid credentials, inactive users, access-only JSON, cookie attributes, repeated refresh rotation/blacklisting, missing/invalid/expired tokens and logout.
- Matching tests cover zero required skills, no overlap, rounding, the 70% boundary, inactive/scam jobs and enabling alerts after both channels were off.
- Lifecycle tests cover idempotent preparation, saved attachments, email sending, sequential re-send guards, external confirmation, draft/dismissed guards, ownership, inactive/scam listings and delivery failures.
- A regression test exposed an unhandled missing-attachment exception. Attachment loading now happens inside the delivery error handler; failure returns a safe 502, leaves ready_for_review/sent_at unchanged and avoids exposing file paths.
- Frontend tests now cover Login as well as Register, Applications, Notifications and Profile. Plans also have preview/no-checkout tests.
- `docs/CI_PROPOSAL.md` proposes adding the frontend test step. The actual CI workflow was not changed.

### WP6: Accessibility, mobile and documentation

- Successful sends/dismissals focus the relevant application heading; mark-read focuses the notification row after its button disappears. Regression assertions verify focus.
- Login announces successful registration. Existing auth logic is unchanged.
- Desktop navigation expands at 1100px to fit the added links; intermediate widths retain the menu disclosure. Application preparation appears before optional document-generation tools.
- Browser checks at 375px, 1024px and 1280px confirm checked screens have no horizontal overflow.
- Root and frontend READMEs now explain setup, tests, migrations and build packaging. DESIGN_SYSTEM.md and the canonical `ajiri-backend/docs/CONCEPTS.md` describe the new components and concepts.
- Review screenshots are committed under docs/screenshots; they show only synthetic local QA data.

## 3. Verification evidence

Environment: Node 22.15.0, npm 10.9.2, Python 3.12.6. Commands were actually executed; counts below are test methods/cases, not a coverage percentage.

For every package, backend commands were:

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

TEMP/TMP pointed to an ignored writable workspace directory, because sandbox-default temporary directories previously denied writes. Tests used their own database and temporary media; the application's db.sqlite3, media and .env were not replaced or migrated.

Frontend commands were:

```powershell
cd C:\dev\ajiri\ajiri-frontend
npm ci
npm run lint
npm run build
npm run test -- --run
```

The test command applies from WP2 onward, when its tooling was installed. Clean installs used the local npm cache and bounded fetch timeouts. The production shell had VITE_API_BASE_URL cleared. Final frontend packaging used the existing `ajiri-backend/scripts/build_frontend.ps1`.

| Package | Django check / migration drift | Django tests | npm ci / lint / build | Frontend tests |
| --- | --- | ---: | --- | ---: |
| WP1 | pass / no changes detected | 27 passed | pass after releasing Vite lock | not installed yet |
| WP2 | pass / no changes detected | 28 passed | pass | 8 passed |
| WP3 | pass / no changes detected | 37 passed | pass | 16 passed |
| WP4 | pass / no changes detected | 37 passed | pass | 18 passed |
| WP5 | pass / no changes detected | 57 passed | pass | 23 passed |
| WP6 | pass / no changes detected | 57 passed | pass | 24 passed |

Final Django run: 57 tests, 40.021 seconds, OK. Final frontend run: 24 tests across 4 files, 10.89 seconds, all passed. Lint reported no warnings/errors. Npm reported zero known vulnerabilities during the recorded installs.

Failures encountered and resolved:

- WP1 npm ci initially failed with Windows EPERM on the Rolldown native binding. The identified Ajiri Vite process was stopped; clean install, lint and build then passed. The original untracked frontend_build/package-lock.json was backed up to `.npm-cache/checkpoint/original-build-package-lock.json` before build regeneration removed it.
- WP5's first focused backend run had one error among 20 tests: missing attachment escaped the handler. One focused fix was made; all 20 then passed, followed by the full 57-test suite.
- No unresolved failed gate or blocked package remains. Live CI and production checks below are explicitly unverified.

### Bundle and contrast

Final Vite build output: main JavaScript 384.92 KB raw / 125.57 KB gzip; CSS 19.31 KB raw / 5.22 KB gzip. Page modules are lazy-loaded; the main bundle plus CSS are about 131 KB gzip before route modules, HTML and transfer overhead. These are build estimates, not a measured mobile network budget. No new font/image download or production Node service was added. The generated deployment tree is checked against dist after final packaging.

Palette calculations passed normal-text 4.5:1 and control-boundary 3:1 thresholds. Examples:

| Pair | Light | Dark |
| --- | ---: | ---: |
| Foreground / surface | 14.38:1 | 13.49:1 |
| Muted / surface | 6.04:1 | 8.43:1 |
| Primary / soft | 6.37:1 | 7.38:1 |
| Primary-button text / primary | 7.26:1 | 9.62:1 |
| Input border / surface | 3.35:1 | 4.90:1 |

This is a targeted accessibility pass, not a full WCAG certification or screen-reader audit.

### Real-API browser checks

An isolated WSGI server used an in-memory SQLite database, synthetic users/jobs, temporary media, captured email, and a local synthetic employer page. No production requests, real employer submissions or real emails were made.

Observed in the browser:

- Registration succeeded and returned to Login. A duplicate email plus overlong phone produced both field errors at 375px.
- Login, protected access and logout worked. Logs show expired-token 401 -> refresh 200 -> retried request success, including document downloads.
- Job pagination moved to page 2; a new title search returned one opportunity and reset page to 1.
- Application preparation produced a reviewable email draft; approval/send changed it to sent and removed send controls. Email was captured locally.
- External confirmation required opening the local employer link and checking the submission declaration; status changed to sent and focus returned to its heading.
- Dismissal confirmed successfully. Escape closed the dialog and restored trigger focus; successful dismissal focused the application heading.
- Notification mark-read changed Unread to Read and focused the affected row.
- Profile saved headline, skills and independent alert preferences. A synthetic DOCX uploaded; authenticated uploaded-CV and generated-CV downloads succeeded. The generated DOCX ZIP was inspected and contained the edited headline and skill.
- Saved application cover-letter download succeeded through the owner-scoped endpoint.
- Plans/Profile/JobDetail/Applications/Register were checked at 375px without horizontal overflow; Plans/navigation also at 1024px and 1280px. Both themes were inspected, and theme persistence was checked after reload.

Screenshots:

- [Desktop plans](../docs/screenshots/checkpoint1-plans-desktop.jpg)
- [Profile at 375px](../docs/screenshots/checkpoint1-profile-375.jpg)
- [Multiple registration errors at 375px](../docs/screenshots/checkpoint1-registration-errors-375.jpg)

## 4. Michael's manual review script

Use PowerShell for these commands, not Command Prompt. Review locally with test listings and captured email; do not send test applications to real employers.

### Prepare the local checkout

1. Stop existing Vite and Django development servers with Ctrl+C.
2. Run `git status` and preserve any personal uncommitted work before switching branches.
3. Switch to integration/checkpoint-1.
4. Back up your existing local SQLite file before applying the additive migration. This command makes a new timestamped copy; it does not replace your database:

```powershell
cd C:\dev\ajiri
git switch integration/checkpoint-1
cd ajiri-backend
if (Test-Path -LiteralPath .\db.sqlite3) {
    $reviewBackup = Join-Path $env:TEMP ('ajiri-before-checkpoint1-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.sqlite3')
    Copy-Item -LiteralPath .\db.sqlite3 -Destination $reviewBackup
    Write-Output $reviewBackup
}
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
.\.venv\Scripts\python.exe manage.py showmigrations jobs
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Expected: jobs migration 0007_notification_in_app applies if not already applied. Existing alerts remain visible. Email output stays in the local console, not recipients' inboxes. Do not run this against production without a separate deployment review.

In another PowerShell terminal:

```powershell
cd C:\dev\ajiri\ajiri-frontend
npm ci
$env:VITE_API_BASE_URL = 'http://localhost:8000/api'
npm run dev
```

Open the Vite URL shown by the terminal, normally http://localhost:5173. Use localhost on both origins. The agent's temporary QA server is not a permanent service.

### Review the flows

1. **Register:** create a synthetic local account; expect a success message on Login. Try an already-used email plus an overlong phone; expect all returned field messages and preserved inputs.
2. **Login:** try a wrong password, then the correct one. Expect a readable error followed by the Jobs screen. Visit a protected URL while logged out and verify login returns there.
3. **Browse/filter:** search a title, location and job type; inspect score and salary labels. Change pages when enough jobs exist. New filters reset pagination. A nonsense title shows the empty state and clear-filters action.
4. **Profile:** update name, phone, headline, location, experience, bio and skills, then save/reload. Clear skills and verify they stay empty. Toggle the two alert preferences independently. Account email remains read-only.
5. **Upload CV:** select PDF, DOC and DOCX samples under 5 MB. Expect a success message and uploaded-CV download. Try a TXT, empty file and a file above 5 MiB: expect clear rejection and the prior CV preserved.
6. **Generate/download:** generate a CV from Profile, then a cover letter from a test JobDetail. Open the DOCX files and inspect profile/job values. Uploaded CV text should not appear automatically: extraction is deferred.
7. **Prepare application:** use a local email-method test listing, prepare it, and expect ready_for_review. Open Review application, download both saved documents, inspect the recipient/subject/body, approve and send. Expect sent/time and no re-send button. The console should show the email; no real message is delivered with the console backend.
8. **Saved snapshot:** edit the profile after preparing another application. Its saved application document downloads should remain unchanged; freshly generated profile documents reflect the edits.
9. **External submission:** use an external-method test listing pointing to a test page you control. Confirmation is disabled until you open the employer link and check the declaration. Submit only on your test page, then confirm in Ajiri. Expect External submission recorded; Ajiri does not perform that submission itself.
10. **Dismiss:** prepare a different test job, dismiss it, and confirm. Expect dismissed/history retained and no send action. Escape in the dialog should return focus to Dismiss application. Successful dismissal should focus its heading.
11. **Notifications:** with a local test job listing skills that match at least 70%, run a local match sweep with captured email. New in-app alerts show Unread; mark one read and expect Read with focus retained. Empty inbox is valid when there are no qualifying jobs. Turning in-app off affects new alerts, not existing history.
12. **Plans:** expect Free/Starter/Pro at KES 0/499/999, explicit preview text and no purchase controls or payment requests.
13. **Theme/mobile/keyboard:** test both themes and reload. At 375px inspect menus, fields, errors, cards and action buttons without horizontal scrolling. Tab/Shift+Tab through forms, use Space for checkboxes, Enter for actions and Escape for dialogs. Focus must remain visible and return meaningfully after actions.

Local sweep, with the development server's console/captured-email setting also used in this terminal:

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
.\.venv\Scripts\python.exe manage.py shell -c "from jobs.matching import sweep_all_active_jobs_for_matches; print(sweep_all_active_jobs_for_matches())"
```

The 70% threshold triggers alerts; it never blocks browsing/applying. Jobs without required skills score 0.

### Optional Postman assertions

Use your local access token and test IDs, not real employer targets. Refresh uses the httpOnly cookie; no refresh token is returned in JSON.

- GET/PATCH /api/profiles/me/: both booleans are present and independently writable.
- POST /api/jobs/applications/{id}/dismiss/: draft/reviewable -> 200 dismissed; repeat -> 200; sent -> 400; another user's record -> 404; anonymous -> 401.
- POST /api/jobs/applications/{id}/send/: ready_for_review -> 200; sequential re-send or dismissed -> 400.
- GET each private document endpoint: owner -> attachment; another user -> 404; anonymous -> 401.
- Repeat a local match sweep: no duplicate delivery receipt/email for the same user/job.

## 5. Decisions and why

- Independent channels need a receipt even for email-only delivery. The explicitly approved in_app flag separates inbox visibility from delivery history without repurposing is_read.
- Old alerts keep their prior visibility; preference changes affect future receipts. Both channels off creates nothing, allowing a later opted-in sweep to find matches.
- Dismissal is idempotent and preserves audit/history; sent cannot be undone. There is no restore/redraft action in this checkpoint.
- Register and Profile share error normalization, so flat or nested DRF errors are fully shown. Forms keep entered values on failure.
- Native details/selects and source-owned JSX components retain accessible browser behaviour and avoid unnecessary production dependencies.
- Profile fields and file uploads save separately. JSON can explicitly clear skills; a failed upload cannot mask a successful profile save.
- Saved application downloads stream their existing files rather than regenerate them. All requests use the existing client; interceptors, JWT cookies/rotation and CORS are untouched.
- System fonts, route-level lazy imports and static deployment retain the lightweight PythonAnywhere model.
- Plans are explicitly a preview. No billing interval, entitlements or payment behaviour was invented.
- Tests use synthetic records, temporary media and captured email. Fast hashing is scoped to new auth/lifecycle test classes, not runtime settings.

## 6. Open risks, assumptions and unverified items

- **Local migration required:** the live application database was not changed. Back it up and apply jobs/0007 before reviewing the integration branch against it.
- **Deployment and live CI unverified:** no PythonAnywhere operation, GitHub Actions run, SMTP-delivery test, production ingestion request, push or main merge was performed. Only Python 3.12.6 was executed locally; 3.13/3.14 remain for the existing CI matrix.
- **Static media remains accessible through existing URLs:** authenticated UI downloads and owner endpoints are implemented, but this checkpoint does not change hosting/static-media access. Restricting all uploaded/generated media needs a separate approved deployment/privacy design.
- **Email semantics:** backend acceptance is not inbox delivery. Sequential re-send guards are tested; simultaneous competing send requests are not covered by an idempotency-key or concurrency test. Mail retry/reconciliation remains follow-up work.
- **Missing files:** a missing attachment now produces a safe 502 and preserves state, but restoring lost files still requires operational recovery; retrying cannot recreate a deleted snapshot.
- **Dismissal is final in V1:** preparing the same job returns its existing application, including dismissed history. Reopening/redrafting is not implemented.
- **Document limitations:** upload validation checks extension, emptiness and size, not document contents. Uploaded-CV extraction and AI-generated cover letters remain out of scope.
- **Accessibility testing limits:** targeted keyboard, focus, labels, contrast and responsive checks passed. A full screen-reader/device-matrix audit was not performed.
- **Build sizes are estimates:** throttled-network transfer and low-end-device performance were not measured. No coverage percentage was measured.
- **Payments are absent by design:** prices are previews; billing periods and feature limits need product scoping before checkout.

No WP is currently blocked or unverified under the required local gates. The deployment/CI/device limitations above are separate unverified checks, not passing claims.

## 7. Suggested next sprint

1. Michael's Checkpoint 1 browser/Postman review; resolve any product feedback before merging integration into main.
2. Approve the small CI proposal and verify the actual Linux/Python matrix on a pull request.
3. Review private-media serving, backups and a controlled PythonAnywhere deployment/migration checklist.
4. Scope email idempotency, delivery observability and recovery of missing documents.
5. Define subscription periods, entitlements and M-Pesa/Daraja requirements before implementing payments.
6. Plan a screen-reader/device and constrained-network performance pass.

Checkpoint work stops here for Michael's review. No further implementation is authorized by this report itself.

</details>
<details>
<summary>Read dated details — source variant 2</summary>

Source: `docs/CHECKPOINT1_REVIEW.md`; input SHA-256 `a021efa8cfac3f12adc1663f8a9272bf078cd2be7d495253cb7f163c99dd6210`.

Earlier checkout differences; unchanged text is retained in the full record above.

```diff
--- consolidated full record
+++ earlier checkout version
@@ unchanged lines omitted @@
 # Checkpoint 1 review
 
-
-> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.
-
 Review date: 14 October 2026 (Africa/Nairobi).
 
```

</details>

<a id="record-checkpoint2-review"></a>

### checkpoint2 review

<details>
<summary>Read dated details — source variant 1</summary>

Source: `docs/CHECKPOINT2_REVIEW.md`; input SHA-256 `fbc28378a2a89ef49ee4e5165a1dba9ef5e395e673220c84d613e2f7421cbfda`.

# Checkpoint 2 review


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

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

## Follow-up review rehearsal - 15 October 2026

The local SQLite backup passed integrity_check and is stored only in an ignored
private audit directory. Migration plan/apply found nothing pending; jobs/0007 is
already applied. The actual local database has zero CV references and zero
applications; the legacy media directory and configured private root are absent.
The required legacy-root dry-run failed safely because the source does not exist,
so no real user media copy was attempted. A disposable synthetic CV rehearsal
then ran dry-run before apply/verify, preserving names/bytes and proving direct
URL 404, owner 200, other user 404 and anonymous 401. This is API-level evidence,
not a logged-in browser rehearsal against a real uploaded CV.

The frontend review rerun passed clean install, lint, 24 tests (20.99s) and build.
The backend review rerun ran 72 tests: 71 passed, one Windows symlink test skipped,
in 45.649 seconds, including privacy and delivery failure/retry/concurrency tests.
No production rehearsal or deployment occurred. The checklist was aligned with
Michael's requested backup, migrate, relocate, mapping-change, reload, post-check
sequence and gained explicit recovery gates plus a post-deploy ingestion-run
check. All traffic/writers must remain paused through the sequence.

## PR #4 frontend CI correction

GitHub Actions confirmed all 72 backend tests pass without skips on Python 3.12,
3.13 and 3.14. The frontend tests/build passed, but the exact packaged-build check
failed: committed index.html had mixed CRLF/LF (including a lone CR), while Linux
Vite emitted LF. Earlier local newline-normalized comparisons could not establish
bytewise CI consistency and missed this failure.

The correction adds repository LF attributes for Vite HTML/public inputs and
packaged text, normalizes packaged index.html to UTF-8 without BOM/LF in the
existing build script, and regenerates frontend_build once at the end of this
frontend CI branch. No Git config or workflow comparison is changed. Local clean
install, lint, 24 tests and build pass. Exact Git-blob/build comparison and a fresh
Linux Actions run are required before merging PR #4.

</details>
<details>
<summary>Read dated details — source variant 2</summary>

Source: `docs/CHECKPOINT2_REVIEW.md`; input SHA-256 `5e84819a9f82642caeee9b1e8e51b4be271beed43c3e071ce5826070e16fdd42`.

Earlier checkout differences; unchanged text is retained in the full record above.

```diff
--- consolidated full record
+++ earlier checkout version
@@ unchanged lines omitted @@
 # Checkpoint 2 review
 
-
-> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.
-
 15 October 2026, Africa/Nairobi. Local review candidate on
 `integration/checkpoint-2`; main and origin/main remain at reviewed Checkpoint 1
```

</details>

<a id="record-checkpoint3-plan"></a>

### checkpoint3 plan

<details>
<summary>Read dated details — source variant 1</summary>

Source: `docs/CHECKPOINT3_PLAN.md`; input SHA-256 `9f071091d3853370d6999147ac99ee96bc6eaaa6177f98fc1d6063316e367d06`.

# Checkpoint 3 plan


Planning only, 15 October 2026. No package below is authorized for implementation yet.
Prepared from clean main at `2d5d175`, also confirmed as the remote main revision.
Production is https://mathenge.pythonanywhere.com: private storage is deployed;
console email delivers no real mail; ingestion/sweeps run through GitHub Actions.
The free web app requires periodic renewal (last recorded expiry: 14 November 2026).
No production or GitHub write action is part of this preparation.

## Candidate packages

### WP11 — Email delivery (8 points)

Branch: `feature/email-delivery`. See [SMTP design](HISTORY.md#record-smtp-email-design).

- Scope: real application and notification delivery, verified platform sender,
  applicant Reply-To, accurate provider-acceptance tracking, atomic shared quotas
  and bounded alert retries. Preserve application claim/idempotency and 502/retry.
- Likely files: `ajiri-backend/config/settings.py`, `jobs/views.py`, `jobs/matching.py`,
  `jobs/models.py`, a shared delivery service and email/concurrency tests. Paths
  beginning jobs/ are beneath ajiri-backend/. No auth or ingestion endpoint rewrite.
- Migration: additive delivery-attempt/budget records likely required for limits
  shared across workers and channels. No deletion, status-value change or rewriting
  historical sent_email values. Exact schema needs approval before implementation.
- Tests: in-memory backend for recipients, Reply-To, saved attachments and accepted
  counts; mocked failures/timeouts; 502 leaves ready_for_review; overlap sends once;
  atomic cap boundaries, timezone reset, channel reservation and alert preference
  independence. Provider transport tests mock HTTP/SMTP; CI never contacts a provider.
- Risks: provider approval, free-tier reachability, domain authentication, quota
  exhaustion, sensitive attachments entering a third-party processor, uncertain
  delivery after lost acknowledgement. Console success is not delivery evidence.
- Decisions: provider/transport, verified sender, limits and alert retry policy;
  approval of privacy/vendor processing and any additive migration.

### WP12 — Dismissed applications (3 points)

Branch: `feature/application-restore`.

| Option | Benefit | Trade-off |
|---|---|---|
| Restore saved snapshots to review (recommended) | Preserves documents the user saw; no schema change | Old details may need review; cannot reconstruct prior draft status |
| Re-draft within the existing record | Uses current profile/job details | Replaces snapshots; must avoid losing user edits and handle missing/inactive jobs |
| Keep dismissal permanent | Smallest scope | User cannot apply again because user/job is unique |

- Scope: an owner-only restore action, a dismissed/history filter and an explicit
  review step before send. Proposed `POST /api/jobs/applications/<id>/restore/`
  changes dismissed to ready_for_review only when saved documents exist; repeated
  restore of an already reviewable record is a no-op. Sent/draft states return 400,
  missing documents return a clear 400, non-owner 404, anonymous 401. No regeneration.
- Likely files: `ajiri-backend/jobs/views.py`, `jobs/urls.py`, lifecycle tests,
  `ajiri-frontend/src/pages/Applications.jsx` and component tests; verify actual UI
  component paths before implementation. Extend the existing auth client usage.
- Migration: none for recommended option; existing unique user/job rule stays.
- Tests: owner restoration, immutable snapshot bytes, missing files, invalid states,
  repeats, concurrent restore/send/dismiss and review UI; no automatic send.
- Risks/decision: stale documents and inactive job destinations need visible review;
  Michael chooses restoration versus re-draft before building.

### WP13 — Privacy and consent (8 points)

Branch: `feature/privacy-consent`.

**DRAFT — requires legal review. This is engineering planning, not legal advice;
Codex is not a lawyer.** Kenya's Data Protection Act 2019 likely applies to CVs and
contact details. Confirm lawful bases, controller obligations, registration duties
and cross-border safeguards with a qualified reviewer, rather than treating a
checkbox as compliance. See [ODPC consent guidance](https://www.odpc.go.ke/wp-content/uploads/2024/02/ODPC-Guidance-Notes-on-Consent.pdf)
and [data-subject rights](https://www.odpc.go.ke/rights-of-a-data-subject/).

- Scope: lightweight public privacy page linked from registration/profile, covering
  controller/contact, data collected, purposes/lawful bases, employer disclosure,
  PythonAnywhere/email processors and transfers, retention, security, rights and
  complaints. Separate required notice acknowledgement from optional email consent;
  do not bundle marketing with access to the service. Recommend optional email off
  for new users pending an explicit choice; existing users need a separate policy.
- Record on the server: notice version and acknowledgement time; optional consent
  purpose/version, grant/withdrawal and timestamp in a separate consent model linked
  to the existing user. Do not collect IP/user-agent without a specific justified need.
  Profile preferences enforce operational choices; consent history records evidence.
  Do not invent consent for historical accounts or change AUTH_USER_MODEL.
- Likely files: `ajiri-backend/accounts/serializers.py`, registration view/tests,
  separate consent model/migration; frontend Register/Profile/router and privacy page.
- API: proposed registration acknowledgement/version and separate optional choice;
  server owns version validation and timestamps. Existing-user handling must be
  approved before making new registration fields mandatory. No token/cookie changes.
- Migration: additive consent records only; legacy users have no acknowledgement
  until collected. No destructive backfill or automatic change of old preferences.
- Tests: required acknowledgement, invalid version, optional rejection allowed,
  withdrawal, server timestamps, historical accounts, field-keyed errors and mobile
  accessible links/checkboxes. No personal data in fixtures or snapshots.
- Risks/decisions: legal wording, lawful bases, controller contact, processor terms,
  retention, optional-alert defaults and existing-user transition require Michael/legal review.

### WP14 — Account data rights (8 points)

Branch: `feature/account-data-rights`. **DRAFT — legal review required.**

- Scope: compare (A) manual identity-verified export/deletion requests with
  (B) authenticated self-service export and confirmed deletion. Recommend A for the
  initial small pilot, with documented fulfilment and identity verification; B is
  a later capability unless Michael approves it now. Disabled users alone are not
  deletion. Never request account passwords by chat/email as verification.
- Export inventory: user/contact fields, profile/skills/preferences, consent,
  applications and private snapshots, notifications and uploaded CV. Exclude password
  hashes, tokens, other users' information and internal secrets. Authentication rows
  must be considered for revocation/deletion, not exported as live credentials.
  Any generated archive is private, owner-checked and short-lived.
- Deletion inventory: user-owned DB rows/relations, consent/audit retention only as
  legally justified, uploaded CV and generated documents, pending sends and refresh
  tokens. Keep shared jobs/skill taxonomy. FileField cascade deletion does not itself
  remove storage bytes; inventory before row removal and make failures recoverable.
  Stop sends/alerts for pending deletion. Already-sent employer/provider copies
  cannot be recalled; describe recipient requests and provider retention limits.
- Backups: Michael/legal reviewer sets an explicit expiry and access policy. Explain
  delayed removal from encrypted/private backups, prevent operational reuse, and
  maintain a minimal legally reviewed deletion ledger so restores reapply deletions
  before serving traffic. Never claim immediate backup erasure if it is not performed.
- Likely files: accounts/profile/jobs service and permission tests, private storage
  cleanup/export tooling, docs and (only for option B) Profile UI and owner endpoints.
- Migration: possibly additive request/progress records; exact choice is open.
  Actual row/file removal is destructive and requires separate explicit approval.
  Do not change AUTH_USER_MODEL or reverse migration history.
- Tests: owner isolation, complete export/no secrets, shared records retained,
  missing files, partial cleanup failure/retry, token revocation, concurrent sends,
  and backup-restore deletion rehearsal using disposable local data only.
- Risks/decisions: identity verification, self-service scope, irreversible deletion,
  retention exceptions, backup expiry and restore suppression need approval.

### WP15 — Basic monitoring (3 points)

Branch: `feature/basic-monitoring`.

- Scope: built-in Python/Django sanitized error events to the existing server log,
  minimal `GET/HEAD /api/health/`, manual ingestion-failure visibility and an operations
  routine. No paid services, dependency, CI workflow change or production automation.
- Health contract: unauthenticated generic 200 when a bounded DB probe succeeds,
  generic 503 otherwise; HEAD has no body; no-cache; no versions, paths, counts or
  exception text exposed. This tests app/DB reachability, not SMTP or ingestion freshness.
- Likely files: `ajiri-backend/config/views.py`, `config/urls.py`, logging settings,
  backend tests and a manual monitoring runbook. Do not replace auth/CORS logic.
- Log only event category, time, safe correlation identifier and outcome. Never log
  bodies, tokens, headers, email addresses, CV content or personal filenames; raw
  exceptions can contain these too. Console email itself prints messages/attachments:
  restrict log access and flag this existing privacy risk pending real delivery.
- Routine for Michael: each day inspect PythonAnywhere error logs/quota and latest
  ingestion/sweep Actions status; on failure inspect the failed step and sanitized
  server event, without pasting credentials/log bodies. Check expected job freshness
  separately. Check renewal weekly and renew before the dashboard expiry. Use GitHub's
  existing personal Actions notification settings; do not configure them for him.
- Migration: none. Tests: GET/HEAD, DB failure 503, no caching, no secret/error detail,
  representative redaction cases; protected endpoints unchanged.
- Risks/decision: manual checks can miss failures between reviews; approve health
  exposure and assign a human owner/frequency. Monitoring must not make live SMTP calls.

## Housekeeping backlog — list only

- Three harmless private production probe files.
- Inactive production test job and disabled synthetic users.
- Line-ending policy check for `.gitattributes`.

## Recommended order and dependencies

WP13 -> WP15 -> WP11 -> WP12 -> WP14. Privacy/legal and sender processing decisions
precede real mail; monitoring supports delivery diagnosis; WP14 depends on retention
and consent decisions. WP12 can proceed independently after its product choice.
Numbers are stable identifiers, not execution order. Suggested total: 30 points,
subject to splitting WP11/WP14 once provider and deletion options are selected.
Future implementation needs package branches, section 7 gates, tests and concepts
updates. Regenerate frontend_build only at the end of each future frontend package.
Deployment compatibility is backup -> migrate -> activate code, with additive schema
remaining compatible with the preceding code. No deployment is authorized here.

## Audit impact

See [read-only modernisation audit](HISTORY.md#record-modernisation-audit) and the consolidated
[decision form](HISTORY.md#record-decisions-needed). No findings authorize application changes.

- Add a proposed WP16 `feature/security-baseline` (8 SP, split after approval):
  configured password validation, content-aware uploads, abuse controls and explicit
  cookie-auth CSRF/inactive-account review. Auth/CORS changes require separate approval.
- Add proposed WP17 `feature/account-recovery-verification` (8 SP): anti-enumerating
  password reset, mailbox verification and unverified-account restrictions. Real
  employer mail depends on verified identity, not merely working SMTP.
- Put P0 security/legal/backup/advisory verification ahead of public onboarding.
  Revise sequence to WP16 and WP13 planning first; WP15 next; WP11 owner-inbox-only
  delivery enables WP17; only then permit general real sending. WP12 is independent;
  WP14 follows approved rights/retention policy. Resolve provider/send dependency with
  a controlled recipient pilot, not by sending to unverified employers/users.
- Expand WP11 acceptance to bounce/complaint suppression, attachment budget, receipt
  copies, metadata retention, accurate notification flags and an operator disable gate.
  WP15 must cover console log sensitivity, manual backup/restore verification and renewal.
- Propose later query-count/scaling and reproducible-packaging maintenance; no index,
  dependency, CI or ingestion change is authorized now. Python vulnerability scan and
  coverage remain UNVERIFIED/unmeasured; npm audit returned zero advisories today.
- The earlier 30-point total excludes WP16/WP17 and expanded SMTP requirements; revised
  minimum is 46 SP before splitting/re-estimation, not a commitment to fit one sprint.

## Decisions Michael must answer before building

1. Gmail SMTP for a pilot or Brevo HTTPS delivery? Recommend Brevo, subject to
   provider approval and acceptance of API transport; Gmail reachability remains unverified.
2. Approve platform From plus applicant Reply-To? Which verified sender/domain
   will you configure privately? Do not send credentials to Codex.
3. What platform daily/per-user caps and application-versus-alert allocation apply?
   Approve bounded alert retries only after definite failures, with no ambiguous retry?
4. Restore saved applications to review or regenerate? Recommend saved snapshots.
5. Who reviews the draft notice/lawful bases, and what controller contact is published?
6. Should new-user optional email alerts default off, and how do existing users confirm choices?
7. Manual verified rights requests or self-service? What active-data, export-archive,
   provider and backup retention periods and deletion exceptions are approved?
8. Approve the order, additive migrations in principle and dependency-free monitoring?
   Exact migration designs and destructive actions still need separate review.

</details>
<details>
<summary>Read dated details — source variant 2</summary>

Source: `docs/CHECKPOINT3_PLAN.md`; input SHA-256 `84e712f86c666b087ac147a988c437f92d7c6fee12d2f933dc99797eda1bb5b4`.

Earlier checkout differences; unchanged text is retained in the full record above.

```diff
--- consolidated full record
+++ earlier checkout version
@@ unchanged lines omitted @@
 # Checkpoint 3 plan
 
-
 Planning only, 15 October 2026. No package below is authorized for implementation yet.
 Prepared from clean main at `2d5d175`, also confirmed as the remote main revision.
```

</details>

<a id="record-checkpoint3a-review"></a>

### checkpoint3a review

<details>
<summary>Read dated details — source variant 1</summary>

Source: `docs/CHECKPOINT3A_REVIEW.md`; input SHA-256 `e7fb105035d7a7c2e842747184bb47e5c3c91d44b772a4451e5e66a886dc1e8e`.

# Checkpoint 3A review — security hardening only


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

15 October 2026, Africa/Nairobi. Base integration/checkpoint-3 at `0a02c74`.
Michael's build instructions supersede AGENTS' earlier documentation-only mission
and WP numbering. Earlier Checkpoint 3 email/privacy WP11-WP15 remain proposals,
not implemented by these identically numbered **Checkpoint 3A** packages.
No push, main merge, connector write or production operation performed.

## 1. Package summary

| WP | Local status | Branch | Source range | Suggested points |
|---|---|---|---|---:|
| WP11 | passed local gates | feature/password-validation | 0a02c74..b792a9f | 3 |
| WP12 | passed; cache/proxy limits below | feature/throttling | bc59a78..f4e819f | 5 |
| WP13 | passed; structural checks only | feature/upload-content-validation | 1b306ce..183b18b | 5 |
| WP14 | passed; production manual verification pending | feature/deploy-settings | 2ec3767..82d8931 | 3 |
| WP15 | design only; no CSRF implementation | feature/refresh-cookie-csrf-design | 3e49fa8..feature/refresh-cookie-csrf-design | 2 |

Source ranges exclude integration merges. Resolve final WP15 tip with
`git rev-parse feature/refresh-cookie-csrf-design`. Passing packages merge --no-ff.
Points are relative sizing for Michael's tracker, not time estimates (total 18).

## 2. What changed

### WP11 — Password validation

Registration runs configured validators with candidate email/name and returns every
message in password-field arrays, including when another field fails. Manager-based
creation validates non-None passwords. Custom-user admin creation/change forms retain
Django validation. No password reset endpoint was invented, no existing hash changed,
no forced reset and no JWT/cookie change. Tests cover short/common/numeric/similar
passwords, strong acceptance, manager/admin/set-password paths and legacy weak login.
Frontend already displayed arrays; its regression now asserts multiple password errors.

### WP12 — Endpoint throttling

Login/register/refresh use IP keys; apply/send use authenticated user keys. Defaults
are 10/min login, 5/hour register, 60/min refresh, 20/hour apply, 10/hour send, all env
overridable (THROTTLING.md). These request rates are NOT the proposed future daily
accepted-email quota. Added attributes only on RefreshView; token/cookie code unchanged.
Interactive login/register/apply/send show 429 wait guidance, reading Retry-After where
available; no automatic mutation retry. Test caches are cleared between cases.

Repository default LocMemCache is process-local; live cache/worker topology is not
inspected. Limits are approximate, not distributed hard guarantees. DRF_NUM_PROXIES=0
ignores client forwarded headers until Michael verifies trusted hops. Same-NAT/proxy
users may share public limits; this is a pre-deployment gate, not a claimed production
fix. Proposed private shared-filesystem cache is documented only; multi-host/atomic
requirements need another design. No ingestion/sweep endpoint changes or global default
throttle were added. Tests show valid-key calls remain successful beyond user limits.
The existing interceptor may route to login if silent refresh receives 429; tailored
silent-refresh recovery UX remains an auth-client follow-up requiring approval. Its
behaviour was deliberately not rewritten in this package.

### WP13 — Content-aware CV uploads

Keep 5 MB, PDF/DOC/DOCX; reject empty/oversize/spoofed files. PDF checks signature and
EOF, DOC bounded compound directory/WordDocument entry, DOCX expected package parts,
XML, paths, CRC and expansion limits. No extraction/network/renderer/scanner. New stored
basenames are random UUIDs; existing data untouched. Unusual valid packages may be
rejected conservatively (UPLOAD_VALIDATION.md). Invalid uploads preserve prior CV.
Synthetic fixtures now contain format-appropriate bytes rather than arbitrary text.

### WP14 — Deploy settings

DEBUG=False profile enables SSL redirect and HSTS 300 seconds; local DEBUG=True keeps
HTTP/HSTS off. Session/CSRF Secure flags, nosniff/referrer/frame policies and HSTS controls
are env-overridable. Broad HSTS/preload remain off. Existing TRUST_PROXY_SSL_HEADER
opt-in is retained; verify proxy sanitation before activating production redirects.
Tests cover isolated settings profiles, overrides, trusted HTTPS no-loop, HTTP redirect,
headers and untrusted forwarded proto. REFRESH_COOKIE_SECURE/JWT logic unchanged.
See DEPLOY_SECURITY_VERIFICATION.md for Michael-only checks and rollback.

### WP15 — CSRF design and handback

REFRESH_COOKIE_CSRF_DESIGN.md documents actual Lax/HttpOnly/Secure cookie, DRF exemption,
credentialled CORS and same-origin deployment; compares Strict, Origin+custom header and
explicit Django CSRF validation. Recommends the standard Django token/origin solution,
with tests and coordinated rollback. No option is implemented. Audit remediation status
separates historical findings, local fixes and remaining open work. Standing rules remain;
AGENTS time-bound sections record Checkpoint 3A scope.

## 3. Verification evidence

Executed locally with Python 3.12.6 / Node 22.15.0 (existing runtimes). Every package runs
backend check, makemigrations --check --dry-run, full Django suite; npm ci, lint, component
tests and build. Django mail is in-memory. No real SMTP/production credential used.

| Package | Django suite | Frontend suite | Other gates |
|---|---|---|---|
| WP11 | 76 run, 75 passed + 1 skipped | 24 passed | check/migration check/npm ci/lint/build passed |
| WP12 | 80 run, 79 passed + 1 skipped | 25 passed | all passed; 4 final targeted throttle tests also passed |
| WP13 | 84 run, 83 passed + 1 skipped | 25 passed | all passed |
| WP14 | 88 run, 87 passed + 1 skipped | 25 passed | all passed |
| WP15 | 88 run, 87 passed + 1 skipped | 25 passed | all required gates passed |

The skip is Windows symlink privilege coverage; Linux CI must run it before Michael
merges. No CI write/run performed. Initial sandbox attempts failed node_modules/temp
permissions; required commands passed with normal filesystem access. One registration
validation-order regression was corrected before merge; no protection was weakened.
ZIP duplicate-name warning is deliberate malformed fixture coverage.

Local production-like `check --deploy`: original W004/W008 gone; W005/W021 remain
intentionally because includeSubDomains/preload are false. No warnings silenced. This
is not a claim of zero warnings or live production hardening.

Frontend build packaged once at end of WP11 (no byte changes) and once in WP12's final
commit; exact dist/package bytes verified. WP13/WP14/WP15 builds are gates only and do
not regenerate the committed package. No dependency/lockfile or CI changes. Final AST comparisons confirm login/refresh/logout
post bodies and ingestion/sweep/key-check implementations are identical to the base;
protected model/auth-client bytes and migration/workflow/dependency diffs are unchanged.

## 4. Manual verification script — Michael

Run only after reviewing this branch; deployment is a separate decision. Local tests
use disposable test DB/media and captured mail, never real employers. In PowerShell:

```powershell
cd C:\dev\ajiri
git branch --show-current
git status --short
cd ajiri-backend
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test accounts.test_passwords accounts.test_throttles profiles.test_upload_content config.test_security --noinput
.\.venv\Scripts\python.exe manage.py test --noinput
cd ..\ajiri-frontend
npm ci
npm run lint
npm run test -- --run
npm run build
```

Expected targeted 16 tests pass; full 88 run with one possible Windows symlink skip;
25 frontend tests pass, migration check finds none. Stop if frontend tooling is locked;
stop your own dev server before npm ci, don't kill unrelated processes or use force fixes.

Local UI review (synthetic accounts only, credentials entered privately by you):
1. Register with short/common/numeric and email-similar values; every returned password
   message appears. A strong password registers; existing-user login still works.
2. In an isolated local environment, lower one THROTTLE_* rate before starting the server;
   repeat that action and expect 429/wait message. Wait the indicated interval and retry
   once. Apply/send status must not change on a throttled request. Use automated tests
   for cache/timer isolation; don't exhaust production/login limits deliberately.
3. Upload genuine small PDF/DOC/DOCX and download as owner; bytes unchanged, random
   stored filename. Rename HTML/executable bytes to .pdf or try an empty/oversize file:
   expect cv_file errors, previous CV retained. Never open executable test content.
4. Read CSRF design, choose an option separately. Do not expect a CSRF fix in this build.

Production verification is **manual-only and not performed**: follow
DEPLOY_SECURITY_VERIFICATION.md for proxy sanitation, exact curl.exe header/no-loop
checks, secure cookie attributes without values, 300s HSTS and rollback; THROTTLING.md
for hop/cache verification. Keep normal backup -> migrate -> activate order and private
media mapping rules. No 3A migration, real-email change or fixture deletion is required.

## 5. Decisions and boundaries

No migration/dependency needed. AUTH_USER_MODEL/model definition, migration history,
CORS, ingestion endpoint implementations, hosting config, CI and auth interceptor are
unchanged. Password manager/form validation is within WP11; refresh only gains throttle
attributes. No SMTP/privacy/restoration/rights/monitoring feature proposals were built.
Michael must verify live proxy/cache topology and approve a CSRF implementation later.

## 6. Risks and follow-ups

- Process-local non-atomic throttle counters, proxy/NAT shared limits; no hard quota.
- Silent-refresh 429 recovery remains existing auth-client behaviour, not tailored UX.
- Structural validation is not malware detection; historical uploads unscanned.
- HSTS/proxy/header/live cookie verification pending; 300s browser retention survives
  zeroing the setting until expiry. No preload/subdomain broadening authorized.
- CSRF, inactive-user refresh, reset/verification, console false-send/log privacy, real
  mail quotas, legal/consent/rights, advisory scan/patches, accessibility/coverage and
  query/scaling issues remain open as listed in MODERNISATION_AUDIT.md.
- An untracked ajiri-backend/.coverage file appeared during local command execution;
  it was not read, modified, deleted or staged. No coverage measurement is claimed.

## 7. Recommended next sprint

Review the CSRF design and proxy/cache findings first; choose a supported shared-counter
strategy before treating throttles as cross-worker protection. Then separately scope
account recovery/verification and real-email safeguards with the unresolved provider,
identity, quota and legal decisions. No deployment is implied by this handback.

</details>
<details>
<summary>Read dated details — source variant 2</summary>

Source: `docs/CHECKPOINT3A_REVIEW.md`; input SHA-256 `0b6276ca6aea0430f35e5cdf51602a8d209f8f88f5fbf87cc63af72b16d6f524`.

Earlier checkout differences; unchanged text is retained in the full record above.

```diff
--- consolidated full record
+++ earlier checkout version
@@ unchanged lines omitted @@
 # Checkpoint 3A review — security hardening only
 
-
-> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.
-
 15 October 2026, Africa/Nairobi. Base integration/checkpoint-3 at `0a02c74`.
 Michael's build instructions supersede AGENTS' earlier documentation-only mission
@@ unchanged lines omitted @@
 
 ```powershell
+cd C:\devjiri
-cd C:\dev\ajiri
 git branch --show-current
 git status --short
@@ unchanged lines omitted @@
 .\.venv\Scripts\python.exe manage.py test accounts.test_passwords accounts.test_throttles profiles.test_upload_content config.test_security --noinput
 .\.venv\Scripts\python.exe manage.py test --noinput
+cd ..jiri-frontend
-cd ..\ajiri-frontend
 npm ci
 npm run lint
```

</details>

<a id="record-ci-proposal"></a>

### ci proposal

<details>
<summary>Read dated details</summary>

Source: `docs/CI_PROPOSAL.md`; input SHA-256 `729a2111f4db755260baf35cea5067d2ffd26ded53a0382bbd14b58252f9404c`.

# CI proposal for Michael's approval

The existing `.github/workflows/ci.yml` is unchanged.

## Proposed change

Add the following frontend step after lint and before build:

```yaml
- run: npm run test -- --run
```

The test script is Vitest, using jsdom and React Testing Library. All packages are devDependencies in the existing lockfile; npm ci installs them. No browser installation or production service is needed.

Keep the backend Python 3.12 / 3.13 / 3.14 matrix, system check, migration check, full tests and committed frontend build comparison. Consider setting the backend job's EMAIL_BACKEND to django.core.mail.backends.locmem.EmailBackend for consistently captured synthetic emails. Correct the stale comment about PythonAnywhere's interpreter after verifying the hosting account; Michael specifies Python 3.12.

Do not add deployment or payments to this workflow. Run the actual GitHub Actions pipeline on a pull request before merging; local checks do not establish Linux or multi-version CI results.

## Local verification (PowerShell)

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
cd ..\ajiri-frontend
npm ci
npm run lint
npm run test -- --run
npm run build
```

Expected: zero system-check issues, no migration drift, all tests pass, lint exits 0 and build exits 0. Regenerate frontend_build at the end of a frontend package using the existing build script; its tree must match dist.

</details>

<a id="record-decisions-needed"></a>

### decisions needed

<details>
<summary>Read dated details</summary>

Source: `docs/DECISIONS_NEEDED.md`; input SHA-256 `5d29feaa061a230076fd94fdaeb9606eeb8bc0dd674b3f900c4b343d7eaaa55e`.

# Decisions needed — Checkpoint 3

Choose A/B/C (or D where offered) in the Answers block; add brief notes where requested.
No answers have been selected. Recommendations are advice, not your decisions.
**Defaults are planning assumptions only: silence never authorizes implementation,
protected auth/CORS changes, dependencies, migrations, deletion, production or GitHub writes.**
If a required identity/legal fact is missing, the affected rollout stays blocked.

Sources: [plan](HISTORY.md#record-checkpoint3-plan), [email design](HISTORY.md#record-smtp-email-design),
[read-only audit](HISTORY.md#record-modernisation-audit). Privacy items are DRAFT requiring legal
review; Codex is not a lawyer. Never put credentials in this form. Public sender/domain
and contact details are configuration facts, not requests for passwords or keys.
WP16/WP17 are new proposals from Audit impact, not approved work.

## SMTP

### D1 — Which transport/provider?
Why: free-tier outbound restrictions determine feasibility.
A: Brevo HTTPS (free quota, adapter/provider approval). B: Gmail SMTP pilot (built-in
backend, current PythonAnywhere exception unverified). C: defer real email (console
must not be presented as delivery).
**Recommend/default:** A for planning; no activation until verified. **Blocks:** WP11, WP17 rollout.

### D2 — Do you own/control a sending domain and its DNS?
Why: authenticated From identity needs SPF/DKIM/DMARC and verified sender rights.
A: yes, domain/DNS under my control (supply public domain, provider setup manual).
B: only a verified mailbox, no domain (limited pilot, provider From restrictions).
C: neither/unknown (block real sending until identity is established).
**Recommend:** A if true; otherwise B pilot. **Default:** C, never infer ownership. **Blocks:** WP11.

### D3 — Which sender model?
Why: delivery alignment and employer trust.
A: verified platform From + applicant Reply-To (clear platform identity).
B: per-user mailbox OAuth/delegation (new security/dependency scope).
C: manual user-side email only (less automation, no server delivery claim).
**Recommend/default:** A; never spoof arbitrary user From. **Blocks:** WP11; platform support
Reply-To/public sender address must be supplied before rollout.

### D4 — Initial sending budgets (all channels/copies count)?
Why: abuse and provider caps; atomic reservations need explicit ceilings.
A: pilot 5/user/day, 2/user/hour, 50/platform/day, 20 reserved for applications.
B: pilot 10/user/day, 3/user/hour, 100/platform/day, 40 reserved for applications.
C: custom limits (give four numbers after provider review).
**Recommend/default:** A, Nairobi daily window, below provider cap; caps must also fit
provider reset windows. **Blocks:** WP11 quota design.

### D5 — Behaviour when a cap is reached?
Why: silent loss versus queued load.
A: applications 429/reviewable with retry hint; alerts pending at most 24h, no burst catch-up.
B: applications 429; discard email alerts over cap, retain in-app alerts.
C: durable queue for both (new scope/scheduling and migration design).
**Recommend/default:** A. **Blocks:** WP11.

### D6 — Retry definite versus uncertain failures?
Why: accepted mail may lose its acknowledgement; exactly-once SMTP is not guaranteed.
A: applications manually retry definite 502 failures; alerts up to 3 attempts, minimum
1h apart within 24h; uncertain outcomes held for manual reconciliation.
B: no automatic alert retry; manual reconciliation only (simpler, more lost alerts).
C: durable provider-idempotent delivery redesign (separate status/schema proposal).
**Recommend/default:** A, preserve existing 400/502 claim behaviour and never auto-retry
uncertain acceptance. **Blocks:** WP11; ingestion service changes still need scope approval.

### D7 — Bounce and complaint handling?
Why: protect sender reputation and stop unwanted mail.
A: manual provider-dashboard review daily during pilot; immediate suppression of
confirmed hard-bounce/complaint destinations, soft failures follow D6; no new webhook.
B: signed provider webhook + suppression records (more automation/testing/security scope).
C: defer all real sending until B is built (slower, no manual gap).
**Recommend/default:** A for tightly controlled pilot; general release needs reliable
suppression and a named reviewer (Michael unless reassigned). **Blocks:** WP11 rollout.

### D8 — Send an application copy to the applicant?
Why: extra cost and another sensitive attachment copy.
A: no email copy, show confirmation/history in app. B: opt-in separate receipt without
attachments (uses quota). C: opt-in separate full copy (privacy, size and quota costs).
**Recommend/default:** A; never silently CC/BCC. **Blocks:** WP11 composition/quota.

### D9 — Attachment limits?
Why: upload size is not the same as generated-document/provider message size.
A: 5 MB combined raw generated attachments plus conservative encoded-message check
against selected provider limit (reject before claim/delivery).
B: 10 MB combined, conditional on verified provider/worker budget (higher mobile cost).
C: manual external application above a lower custom ceiling (supply size).
**Recommend/default:** A; no public attachment URLs, preserve saved documents on rejection.
**Blocks:** WP11; exact provider cap must be verified before implementation acceptance.

### D10 — Email attempt metadata and retention?
Why: troubleshooting versus personal-data minimization.
A: outcome/timestamps, opaque application/user reference and provider message ID for
30 days; no body, attachment, address or raw error; anonymized aggregate counts after.
B: same for 90 days (longer diagnosis, more retention). C: legal-review custom period
and fields (state minimum needed; no credential/content logging).
**Recommend/default:** A subject to legal approval; suppression data has its own D25 policy.
**Blocks:** WP11 schema, WP13/WP14 retention.

### D11 — Safe production rollout and outage control?
Why: console can falsely report success; accidental employer email cannot be recalled.
A: disabled by default -> allowlisted Michael-controlled inbox with synthetic docs ->
small verified-user pilot -> general release after review, operator disable retained.
B: owner-inbox pilot only this checkpoint (general release deferred).
C: defer live email entirely.
**Recommend/default:** B until security/legal/account gates pass; server operations
remain Michael-only under separate approval. **Blocks:** WP11 rollout, WP17 delivery.

### D12 — Provider adapter/dependency approach?
Why: dependency budget versus transport maintenance.
A: Django-compatible standard-library HTTPS adapter, mocked transport (no new dependency).
B: propose Anymail/official SDK with cost/security rationale before installing.
C: Gmail built-in SMTP only, conditional on D1/connectivity.
**Recommend/default:** A for Brevo; B needs separate dependency approval. Finite timeout
proposed 10s, subject to worker verification. **Blocks:** WP11 implementation design.

## Accounts

### D13 — Password reset capability?
Why: recovery without leaking whether an address exists.
A: built-in Django token primitives + generic response, single-use/expiring link,
rate limits, new-password validation and refresh-token revocation after reset.
B: manual identity-verified recovery initially (human workload; never ask for password).
C: defer recovery and keep public onboarding closed.
**Recommend/default:** A design, proposed 1h token expiry. **Blocks:** WP17, public readiness;
real reset email requires D1/D11 and tokens never enter logs/chat.

### D14 — What may unverified accounts do?
Why: prevent using another person's email as applicant identity/Reply-To.
A: browse/edit profile; block employer sending and email alerts until verified.
B: block all authenticated features until verified (stronger gate, worse onboarding).
C: invite-only pilot with manual ownership verification (temporary operational burden).
**Recommend/default:** A, expiring single-use verification links (proposed 24h), generic
resend response/rate limits. **Blocks:** WP17, WP11 general sending.

### D15 — How do existing accounts transition to verification?
Why: historical registration proves no mailbox ownership.
A: mark unknown, prompt verification; preserve data and block email until verified.
B: manually verify an explicitly reviewed pilot list (no blanket grandfathering).
C: defer rollout until migration/communication strategy is reviewed.
**Recommend/default:** A design; additive separate verification records, no change to
AUTH_USER_MODEL, no invented historical proof. **Blocks:** WP17 migration/rollout.

### D16 — Disabled/deletion-pending accounts and sessions?
Why: custom refresh lacks an activity lookup; matching iterates inactive profiles.
A: stop refresh, revoke refresh sessions, suppress alerts/sends; existing short access
tokens rejected by current active-user checks; add concurrency/regression coverage.
B: design immediate revocation of all access tokens too (new mechanism/scope).
C: hold account changes/public rollout until a separate auth design is reviewed.
**Recommend:** A design. **Default:** C until protected auth changes are expressly approved.
**Blocks:** WP16/WP17, WP14, public readiness.

## Privacy — DRAFT, legal review required

### D17 — Who owns wording, lawful bases and processor/transfer review?
Why: checkbox implementation cannot establish legal compliance.
A: Michael drafts with qualified legal reviewer approving before release.
B: qualified reviewer supplies text, Michael implements as controller contact.
C: reviewer not selected; draft only, public onboarding held.
**Recommend:** B where available. **Default:** C. **Blocks:** WP13, real-user rollout, vendor use.

### D18 — Controller and rights/support contact to publish?
Why: users need an accountable party and usable request channel.
A: Michael as controller with a monitored dedicated contact (provide public details).
B: named organisation/controller and monitored contact (provide public details).
C: undecided; do not publish invented details.
**Recommend:** accurate A/B as legally reviewed. **Default:** C. **Blocks:** WP13, WP14.

### D19 — Registration acknowledgement and optional processing?
Why: preserve free choice and distinguish acknowledgement from consent.
A: required versioned notice acknowledgement; separate unchecked optional email choice;
server records version/time/purpose and grant/withdrawal, no IP/user-agent by default.
B: acknowledgement only; disable optional email until consent UI is approved.
C: legal reviewer specifies an alternative lawful-basis/choice model before coding.
**Recommend:** A subject to legal review. **Default:** B for planning until wording approved.
**Blocks:** WP13, WP11 alerts; schema must stay additive and not fabricate old consent.

### D20 — Existing users' notification preferences and notice transition?
Why: current default-true preference is not proof of informed consent.
A: prompt acknowledgement and explicit email choice; pause optional email until confirmed.
B: invite-only re-confirmation manually before email rollout (human work).
C: hold rollout until legal transition policy supplied; never silently infer agreement.
**Recommend:** A. **Default:** C until reviewed; no automatic preference backfill.
**Blocks:** WP13 transition, WP11 general alerts.

### D21 — Rights fulfilment: manual or self-service?
Why: identity checking and destructive operations need reliable handling.
A: documented manual verified requests for pilot (Michael owns queue).
B: authenticated self-service export + manual deletion (partial automation).
C: self-service export/deletion with explicit confirmation and recovery workflow (larger scope).
**Recommend/default:** A design, not authorization to delete. **Blocks:** WP14, rights readiness.

### D22 — Deletion scope and failures?
Why: DB cascades leave files; employers/backups retain independent copies.
A: remove user-owned DB/private media, revoke sessions and stop pending sends;
retain shared jobs/taxonomy, minimal legally justified ledger, backups expire by D25.
B: temporary deactivation followed by A after a reviewed grace period (state duration).
C: legal reviewer specifies retention/hold exceptions before destructive design.
**Recommend:** A subject to legal review. **Default:** C; deletion requires separate explicit
approval, including partial-file failure/retry design. **Blocks:** WP14.

### D23 — Export format and availability?
Why: portability, document access and risk of lingering archives.
A: private ZIP containing JSON and original CV/application files; 24h maximum lifetime,
owner-only authenticated retrieval, no tokens/hashes/secrets or other users' data.
B: JSON/CSV data plus separate existing owner downloads (less archive/storage complexity).
C: manual private delivery in reviewer-approved format (more operator work).
**Recommend/default:** B for manual pilot; A for later self-service. **Blocks:** WP14.

### D24 — Active-account/inactive-data retention?
Why: saved CVs/applications currently persist without an expiry policy.
A: retain while active, notify after 12 months inactivity then allow 30 days to export
before approved deletion (needs legal review and operational tooling).
B: shorter custom lifecycle (state period, notice and enforcement owner).
C: legal policy not decided; no automatic purge and no public retention promise yet.
**Recommend:** legally reviewed A or B. **Default:** C; flag unresolved before public release.
**Blocks:** WP13 policy, WP14 deletion automation.

### D25 — Backup, suppression/provider retention and exceptions?
Why: deletion claims must match recoverability and processor policies.
A: rolling 30-day private backups; restore replays minimal deletion/suppression ledger
before reopening; provider retention minimized and documented, legal holds explicit.
B: 90-day backups with same controls (greater recovery window and privacy exposure).
C: reviewer defines periods/holds, suppression lifetime and provider deletion constraints.
**Recommend:** A if legally appropriate; suppression held only as long as necessary to
prevent prohibited resends, reviewed separately from D10 attempts. **Default:** C pending
review. Never promise immediate backup or employer-copy erasure. **Blocks:** WP13/WP14/WP11.

## Product

### D26 — Dismissed applications: undo, re-draft or final?
Why: unique user/job row prevents starting a second application.
A: restore saved snapshots to review, no auto-send (recommended existing plan).
B: regenerate within record after explicit warning (may replace user-approved content).
C: final dismissal (simple, no second application).
**Recommend/default:** A design; specify inactive/missing-document behaviour in D27.
**Blocks:** WP12.

### D27 — Restore stale/inactive applications or missing documents?
Why: restoring must not silently send outdated content or regenerate snapshots.
A: restore when files exist, warn on stale/inactive destination and require review;
block send where destination no longer usable, missing files return clear 400.
B: allow restore only for active jobs with intact files (stricter, fewer recovery paths).
C: route such records to explicit re-draft/manual external process (larger UI scope).
**Recommend/default:** B for initial scope; amend prior WP12 proposal if selected.
**Blocks:** WP12 acceptance.

### D28 — Public SEO/PWA/cache work now?
Why: audit found shared metadata/no offline shell/no shared fetch cache; private caching is risky.
A: defer public SEO/PWA; measure mobile transfer first, no persistent private cache.
B: add public-job discovery/metadata design only (auth/product scope changes).
C: offline public shell design only, never private CV/token caching (new scope).
**Recommend/default:** A. **Blocks:** optional P2 backlog only.

## Operations

### D29 — P0 password, CSRF and abuse-control package?
Why: configured validators are bypassed, refresh is CSRF-exempt and throttles are absent.
A: approve separate WP16 design covering validator enforcement, explicit login/refresh
CSRF/origin policy, per-endpoint limits and active-account tests; then approve exact changes.
B: prioritize validators/uploads while commissioning auth threat review; public rollout held.
C: defer all code and keep onboarding closed pending review.
**Recommend/default:** A design only. Auth/CORS/interceptor changes remain protected;
no framework default or SameSite alone is accepted as a complete CSRF policy.
**Blocks:** WP16, P0 real-user release.

### D30 — HTTPS/HSTS/header policy and access-token storage?
Why: deploy checks warn W004/W008; live proxy/headers unverified; localStorage is XSS-readable.
A: Michael manually verifies HTTPS/proxy/cookies, then short HSTS without preload or
subdomains; plan CSP report-only and token-storage threat review without rewriting auth.
B: review at hosting layer first, keep app policy changes deferred and release gated.
C: request dedicated security design before any hardening choices.
**Recommend/default:** A design; never enable redirect behind an unverified proxy.
**Blocks:** WP16 deployment readiness; any server work remains Michael-only.

### D31 — Content validation: keep legacy DOC?
Why: current extension/5 MB checks accept disguised content; signatures are not malware scanning.
A: PDF/DOC/DOCX with signature/container + safe ZIP limits; no malware-free claim.
B: PDF/DOCX only, reject legacy DOC (simpler but changes accepted user formats).
C: propose external scanning/dependency separately (privacy/cost/approval required).
**Recommend/default:** A to preserve current format support; implementation feasibility
must be checked, with approval before dependencies or format removal. **Blocks:** WP16 uploads/P0.

### D32 — Python advisory scan and patch maintenance?
Why: pip-audit absent; pip check is not a vulnerability scan; packages are outdated.
A: Michael provides/runs pip-audit separately, triage findings and plan focused patch PRs.
B: approve a separate tooling/dependency proposal first; no installs now.
C: defer scan and keep public-release gate unresolved.
**Recommend/default:** A as a verification request, never infer scan passed.
**Blocks:** P0 vulnerability verification; future maintenance scope.

### D33 — Monitoring ownership, health endpoint and logs?
Why: no health/error tracking; console mail exposes content in private logs.
A: Michael checks logs/quota/Actions daily, renewal weekly; generic public GET/HEAD
health checks DB only, sanitized events, no paid service/dependency; review log retention.
B: same manual routine, authenticated health only (less useful external probing).
C: propose free external monitoring separately (data sharing/permissions need approval).
**Recommend/default:** A design; log retention follows D10/D25 legal review, no raw mail
content in new application logs. **Blocks:** WP15; public readiness needs named owner.

### D34 — Backup ownership and recovery evidence?
Why: checklist exists, current schedule/off-host copy/restore evidence is UNVERIFIED.
A: Michael performs private daily backup while writes occur, before every deployment,
weekly off-host copy and monthly disposable restore rehearsal, retention per D25.
B: same manual minimum plus separately designed automated backup (hosting scope).
C: propose alternative recovery objectives/owner before public release (supply targets).
**Recommend/default:** A planning baseline, never authorization for server/file operations.
**Blocks:** P0 operational gate, WP14 retention, deployment readiness.

### D35 — Coverage/E2E/accessibility and performance follow-up?
Why: coverage tooling absent, no browser/a11y gate; static evidence suggests N+1/scaling gaps.
A: targeted security/query-count/concurrent-draft tests and manual keyboard/mobile
smoke first; measure latency/query counts; defer new test dependencies until proposal.
B: propose coverage + E2E/a11y tools now, with dependency/CI approval separately.
C: commission a larger test/load study before feature work (slower, stronger evidence).
**Recommend/default:** A; query/index/chunking designs follow measurement, no ingestion
rewrite approved. **Blocks:** WP16 acceptance and later performance backlog.

### D36 — Packaging/schema/housekeeping scope?
Why: packaging uses npm install; no API schema/versioning policy; production probes remain.
A: defer as listed backlog; retain /api compatibility, exact build guard and LF scope.
B: separate maintenance design for npm ci packaging, docs-first API/error contract and
measured indexes (new branch/estimate, no production cleanup).
C: prioritize B after P0, separately request manual fixture cleanup later.
**Recommend/default:** A this checkpoint; no CI changes/dependencies/cleanup authorized.
**Blocks:** optional P1/P2 backlog only.

### D37 — Approve revised order and migration boundary?
Why: audit expands original 30-point proposal to at least 46 before SMTP re-estimation.
A: WP16/WP13 design -> WP15 -> WP11 controlled inbox -> WP17 -> reviewed real-mail
release; WP12 independent, WP14 after rights/retention approval; split into smaller sprints.
B: only P0 security/privacy + monitoring first; defer email/restoration/rights automation.
C: return for a smaller revised plan before any building.
**Recommend:** B for manageable next sprint. **Default:** C until explicit approval.
Any additive consent/verification/budget/request migration needs exact schema review;
no AUTH_USER_MODEL change, destructive operation or historical backfill implied.
All changes must support backup -> migrate -> activate code; no new dependency, CI,
ingestion or hosting change without separate approval. **Blocks:** checkpoint execution.

## Answers

Copy this block and enter option letters plus necessary non-secret notes. Leaving a line
blank leaves it unanswered; recommendations have not been preselected.

```text
D1:
D2:
D3:
D4:
D5:
D6:
D7:
D8:
D9:
D10:
D11:
D12:
D13:
D14:
D15:
D16:
D17:
D18:
D19:
D20:
D21:
D22:
D23:
D24:
D25:
D26:
D27:
D28:
D29:
D30:
D31:
D32:
D33:
D34:
D35:
D36:
D37:
```

</details>

<a id="record-deploy-security-verification"></a>

### deploy security verification

<details>
<summary>Read dated details — source variant 1</summary>

Source: `docs/DEPLOY_SECURITY_VERIFICATION.md`; input SHA-256 `46502a889a3406b5dae234daac449b5473bb061819b2a654839c4f0f642ffa37`.

# Checkpoint 3A deployment security verification — Michael only


No deployment performed by Codex. Apply only a reviewed revision after your normal
backup -> migrate -> activate-code checklist. Checkpoint 3A introduces no migrations.
Do not change JWT/cookie rotation, CORS, ingestion configuration or static mappings.

## Configuration to review privately before activation

| Name | DEBUG=False default | Local DEBUG=True default |
|---|---|---|
| SECURE_SSL_REDIRECT | True | False |
| SECURE_HSTS_SECONDS | 300 | 0 |
| SECURE_HSTS_INCLUDE_SUBDOMAINS | False | False |
| SECURE_HSTS_PRELOAD | False | False |
| SESSION_COOKIE_SECURE / CSRF_COOKIE_SECURE | True | False |
| SECURE_CONTENT_TYPE_NOSNIFF | True | True |
| SECURE_REFERRER_POLICY | same-origin | same-origin |
| X_FRAME_OPTIONS | DENY | DENY |
| TRUST_PROXY_SSL_HEADER | False (opt-in) | False |

Every row reads environment overrides; do NOT enable includeSubDomains/preload in this
rollout. REFRESH_COOKIE_SECURE and JWT/refresh logic are unchanged. Never weaken cookie
security on production to make a broken redirect work.

1. Privately record previous revision, non-secret settings and known-good behaviour.
   Back up DB/private media/config and verify restore as in DEPLOYMENT_CHECKLIST.md.
   Pause writers/callers for the normal cutover; stage reviewed code without activation.
2. Check PythonAnywhere's current support/documentation confirms its front proxy
   overwrites X-Forwarded-Proto, and confirm the app cannot receive arbitrary direct
   external traffic around that proxy. Do not assume the client's header is trusted.
   Also determine the trusted IP hop count separately (THROTTLING.md).
3. Before reload, set TRUST_PROXY_SSL_HEADER=True privately ONLY if step 2 is established.
   Keep SECURE_SSL_REDIRECT=False and SECURE_HSTS_SECONDS=0 while resolving uncertainty;
   retain PythonAnywhere Force HTTPS. If the proxy contract cannot be verified, stop
   rollout and ask support. Do not activate redirect defaults blindly.
4. Run checks from your PythonAnywhere Bash console (no secret printing):

   ```bash
   cd /home/Mathenge/ajiri/ajiri-backend
   workon ajiri
   python manage.py check
   python manage.py migrate --plan
   python manage.py check --deploy
   ```

   Review only the approved migration plan; none new for 3A. Once trust is verified,
   configure redirect=True, HSTS=300, session/CSRF secure=True, nosniff=True,
   referrer=same-origin, frame=DENY, includeSubDomains=False and preload=False using
   the table's environment names, privately. Re-run check --deploy: W004/W008 absent;
   W005/W021 expected because broader HSTS/preload are deliberately off. Never silence
   warnings or enable preload just to obtain a clean warning count.
5. Activate/reload only after checks pass and use credential-free checks from your
   own PowerShell terminal. These inspect the actual public proxy response:

   ```powershell
   curl.exe --head --max-redirs 0 http://mathenge.pythonanywhere.com/login
   curl.exe --head --max-redirs 0 https://mathenge.pythonanywhere.com/login
   curl.exe --head --max-redirs 0 -H 'X-Forwarded-Proto: http' https://mathenge.pythonanywhere.com/login
   curl.exe --head --max-redirs 0 -H 'X-Forwarded-Proto: https' http://mathenge.pythonanywhere.com/login
   ```

   Expected HTTP redirects to HTTPS; HTTPS is 200 without a redirect to itself,
   including when a client spoofs forwarded proto. Headers on HTTPS: HSTS max-age=300
   only, X-Content-Type-Options nosniff, Referrer-Policy same-origin, X-Frame-Options DENY.
   Missing headers/static response behaviour or unexpected redirects block verification;
   do not keep following a loop. These probes supplement, not replace, proxy assurance.
6. Log in through your browser yourself; inspect cookie attributes without copying
   values. Refresh remains Secure/HttpOnly/SameSite=Lax; session/CSRF cookies, if present,
   are Secure. Confirm login/refresh/logout and owner download. Direct private media
   still fails. Check one normal ingestion Actions result after resuming callers;
   never paste keys, cookies, token values or raw mail logs into chat.

## Rollback

Keep HTTPS at the host. If Django loops, privately set SECURE_SSL_REDIRECT=False,
SECURE_HSTS_SECONDS=0, restore the prior verified proxy-trust selection/revision and
reload manually. Keep session/CSRF and refresh cookies secure. Django stops adding
HSTS when zero; browsers may retain the previous 300-second policy until it expires
from their last positive header. HTTPS must continue working throughout. No preload
list or subdomain policy was enabled. Do not restore an old DB over new writes or
reverse migrations. Record outcomes privately; production remains unverified until
Michael completes these steps.

</details>
<details>
<summary>Read dated details — source variant 2</summary>

Source: `docs/DEPLOY_SECURITY_VERIFICATION.md`; input SHA-256 `ec2b0dab5d0ca7d803f8676917b0a060623c533205e243f32730649ca5e95a97`.

Earlier checkout differences; unchanged text is retained in the full record above.

```diff
--- consolidated full record
+++ earlier checkout version
@@ unchanged lines omitted @@
 # Checkpoint 3A deployment security verification — Michael only
 
-
 No deployment performed by Codex. Apply only a reviewed revision after your normal
 backup -> migrate -> activate-code checklist. Checkpoint 3A introduces no migrations.
```

</details>

<a id="record-modernisation-audit"></a>

### modernisation audit

<details>
<summary>Read dated details — source variant 1</summary>

Source: `docs/MODERNISATION_AUDIT.md`; input SHA-256 `a759f0f0e0b67782a139832784583be79d219724d03ca69f148b9f9da1703efc`.

# Modernisation audit — read-only


15 October 2026; source revision `24a0ae2` on integration/checkpoint-3. No application,
configuration, dependency, CI or production changes made. Status is **OK**, **gap**,
or **unknown**; **UNVERIFIED** means a claim could not be established. Effort uses
rough story points (SP), not a delivery promise. Evidence is repository-relative.
This is an engineering audit, not legal advice; privacy proposals are DRAFT for legal review.

## Command evidence and limits

- Backend `.venv` Python: `manage.py check --deploy` with DEBUG=False, audit.invalid
  allowed/trusted host, in-memory mail and explicitly dummy audit keys; dotenv loading
  disabled. Result: **security.W004 (HSTS), security.W008 (SSL redirect)**, no other
  deploy warnings. This does not verify the hosting proxy or actual production headers.
- Read-only serializer probes: common/numeric dummy password passes RegisterSerializer;
  configured validate_password rejects it with two errors. Nine non-PDF bytes named
  audit.pdf pass validate_cv_file. No user/file created by these probes.
- `python -m pip check`: **No broken requirements found**. `pip show pip-audit coverage`:
  both absent. No tools installed. Python vulnerability result **UNVERIFIED**;
  backend/frontend coverage **unmeasured** (Vitest coverage providers also absent).
- Initial restricted-network npm query failed DNS; retry with network access succeeded.
  `npm audit --json --fetch-retries=0 --fetch-timeout=20000`: **0 vulnerabilities**, 247
  dependency entries reported. This is a registry advisory snapshot, not proof of safety.
- `npm outdated --json --fetch-retries=0 --fetch-timeout=20000` returned 8 outdated
  direct packages (exit 1 indicates outdated entries). `pip list --outdated --format=json`
  returned 16 outdated installed packages. Exact examples below; no upgrades performed.
- No full test suite, fresh build, coverage, E2E, accessibility scanner, load test,
  production probe, backup restore or live header inspection performed this round.

Read-only reproduction for deploy checks (PowerShell, disposable process environment;
all key material below is deliberately non-secret, not production configuration):

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'False'
$env:SECRET_KEY = ('audit-dummy-not-a-real-key-' * 4)
$env:INGEST_API_KEY = 'audit-dummy-not-real'
$env:ALLOWED_HOSTS = 'audit.invalid'
$env:CSRF_TRUSTED_ORIGINS = 'https://audit.invalid'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check --deploy
```

Historical findings below describe the original audit revision; the final Checkpoint 3A
remediation status section is authoritative for local fixes and remaining limits.

## 1. Security

| Status / evidence | Risk | Suggested fix / effort |
|---|---|---|
| **gap**: settings.py effective SECURE_HSTS_SECONDS=0, SECURE_SSL_REDIRECT=False; W004/W008 | Downgrade protection depends on hosting | Michael verifies proxy HTTPS recognition/redirect first; staged short HSTS, no preload/subdomains initially. Avoid redirect loops. 2 SP |
| **OK (local config)**: DEBUG=False default; missing key fails outside DEBUG; ALLOWED_HOSTS parsed from env; prod secure session/CSRF/refresh cookies true | Actual production env **UNVERIFIED**; empty hosts reject access; wildcard/insecure key not explicitly rejected | Validate prod configuration without exposing values; preserve local fallback. 1 SP |
| **OK / gap**: SecurityMiddleware + frame middleware; effective nosniff=True, DENY, same-origin referrer policy. No explicit CSP or Permissions-Policy in project | XSS can expose localStorage access token; inline theme script complicates CSP. Live headers **UNVERIFIED** | Test headers and CSP report-only plan; retain auth client pending approved design. 3 SP |
| **gap**: accounts/views.py refresh reads httpOnly Secure/Lax cookie; APIView.as_view is csrf_exempt=True; JWT-only authentication provides no CSRF check; no explicit Origin enforcement | SameSite reduces cross-site cookie sending but is not a complete policy for same-site origins; CORS is not CSRF. No exploit demonstrated | Explicit CSRF/origin design for login/refresh, local-dev compatibility and adversarial tests. Protected auth changes need approval. 3 SP |
| **gap**: REST_FRAMEWORK has no default throttles; no view throttle classes found | Login guessing, registration abuse, document-generation and email resource exhaustion | Per-endpoint abuse controls and durable email budgets; trust proxy/IP only with verified configuration. 3–5 SP |
| **gap**: RegisterSerializer only min_length=8; create_user bypasses configured validators (probe confirmed) | Common/numeric/similar passwords accepted | Call Django password validation with candidate user; field errors and regression tests. 2 SP |
| **gap**: profiles/serializers.py validates extension and 5 MB only, no content sniffing | Disguised/unsafe files; private storage protects access, not file safety | Signature/container checks for PDF/DOC/DOCX, ZIP expansion limits and reject malformed inputs; signatures are not malware scanning. 3 SP |
| **OK (source)**: config/urls.py excludes /media; private permissions 0600/0700; owner download tests exist | Hosting mappings can bypass Django; current mappings **UNVERIFIED this round** | Keep manual privacy checks and private mappings in deployment acceptance. 1 SP |

Source context: [Django password validation](https://docs.djangoproject.com/en/4.2/topics/auth/passwords/)
explains model-level create_user does not apply validators; installed-code probes above
establish this repo's behaviour. [DRF CSRF guidance](https://www.django-rest-framework.org/topics/ajax-csrf-cors/)
distinguishes cookie/session requests from other authentication.

## 2. Auth and accounts

**gap.** accounts/urls.py only register/login/refresh/logout; no reset, verification,
export/deletion or consent endpoints/model fields. Tests cover rotation, replay,
expiry, logout and inactive login. Reset/verification policy and anti-enumeration
need design (5–8 SP); rights workflow belongs WP14 (8 SP). Block real employer email
until mailbox control is verified or explicitly restrict it to an owner-only pilot.

**gap / unknown.** Custom RefreshView validates token but does not look up current user
activity before issuing/rotating. An inactive account may continue refreshing until
expiry; protected JWT authentication checks user activity separately. No disabled-user
refresh regression found. Stop-issue/revoke policy, password-reset revocation and
concurrent refresh handling need tests/design; no exploit test run (3 SP). Client stores
access token in localStorage and refreshes each failed request separately; concurrent
refresh races and XSS exposure warrant targeted tests before changing protected auth.

## 3. Dependencies

**OK / gap.** package-lock.json supports npm ci; requirements-prod.txt pins versions
and requirements.txt includes runtime plus stubs. Python requirements are not a
hash-locked resolver output. pip check passes; npm advisory scan is clean today.

Outdated snapshot: React/ReactDOM 19.2.8 -> 19.3.1; Vite 8.2.2 -> 8.3.4;
react-router-dom 7.18.3 -> 7.18.4; oxlint 1.80.0 -> 1.88.0; plugin-react 6.1.1 -> 6.1.2;
React type packages -> 19.3.0. Python: Django 6.1 -> 6.1.2, DRF 3.18.0 -> 3.18.3,
PyJWT 2.13.0 -> 2.15.1, lxml 6.1.2 -> 6.1.3; other outdated entries are largely
Celery tooling, stubs, timezone data and pip. Outdated does not mean vulnerable.
Risk: stale patches and transitive drift. Recommend reviewed patch maintenance,
separate upgrades and future Python lock/hash decision (2–3 SP).

**unknown — UNVERIFIED Python vulnerabilities.** pip-audit not installed; do not infer
security from pip check or outdated. Michael can run the following **after separately
approving/providing pip-audit**, not as an implicit install instruction:

```powershell
cd C:\dev\ajiri\ajiri-backend
.\.venv\Scripts\python.exe -m pip_audit -r requirements-prod.txt
.\.venv\Scripts\python.exe -m pip list --outdated --format=json
cd ..\ajiri-frontend
npm audit --json
npm outdated --json
```

No audit package was installed. Vulnerability triage is a P0 verification gate; any
actual fixes depend on findings, not a blanket major-version upgrade.

## 4. Testing

**OK / gap.** Backend accounts/tests.py, jobs/test_{lifecycle,preferences,private_media,
send_concurrency}.py and profiles/test_cv.py cover core permissions/lifecycle. Frontend
src/test contains login/flows/profile/subscriptions tests; CI runs Django tests on
3.12–3.14 and Vitest. Historical counts in checkpoint reports are not a new test result.

**unknown — UNVERIFIED** line/branch coverage: coverage and both Vitest coverage
providers absent; no new dependencies installed. No Playwright/Cypress/axe dependency
or E2E/a11y CI job found. Risks: no real-browser auth/CSRF/keyboard regression gate,
no coverage of missing security controls/reset/verification. Recommend targeted P0
regressions first, then local browser smoke/keyboard checks; approve tools separately
before coverage/E2E automation (3–5 SP). No coverage percentage claimed.

## 5. Frontend

| Status / evidence | Risk | Suggested fix / effort |
|---|---|---|
| **OK / gap**: hooks/useApiResource aborts obsolete fetches; axios shared client; no shared response cache | Refetch on remount, repeated requests on mobile | Measure first; bounded in-memory deduplication, avoid persistent private-data cache. 2 SP |
| **OK / gap**: Register native constraints + all field-keyed errors; Profile extension/size validation; server lacks password/content checks | UI validation can be bypassed | Enforce server checks first, mirror helpful errors. Included security effort |
| **OK (measurement)**: committed assets total 438,431 raw bytes; main JS 384,921 raw / 123,952 gzip; CSS 19,312 / 5,211 gzip; App.jsx lazy routes | Main bundle/mobile cost; synthetic gzip is not live transfer size | Keep split routes, measure production compression and choose budget before new dependencies. 1–2 SP |
| **OK / unknown**: labels, aria-invalid, skip link and route focus in AppShell; Radix controls | Contrast, touch targets, keyboard and screen-reader completion **UNVERIFIED** | Manual mobile/keyboard review, then approved automated checks. 2 SP |
| **gap**: no service worker/offline manifest found | No offline shell; offline CV storage could create privacy risk | Defer PWA; never cache private documents/tokens. 3 SP if later approved |
| **OK / gap**: index.html has title/description/lang/viewport; no route-specific SEO/schema | Shared SPA metadata, authenticated jobs not searchable | Product decides public discovery before SSR/public-job work. 2–5 SP |

## 6. API

**OK:** settings.py sets page-number pagination (20); jobs/filters.py supports title,
location, type and skill. Owner scoping is explicit for applications/notifications.
**gap:** no OpenAPI/schema route/config or versioning policy found. Errors mix DRF
field arrays, detail strings and non-JSON infrastructure failures; frontend lib/errors.js
normalizes form errors. Risk: integration drift and inconsistent clients. Recommend
an explicit documented contract first, schema tooling only with dependency approval;
keep /api compatible, no gratuitous /v2 migration (2–3 SP). Schema generation and
end-to-end error consistency **UNVERIFIED**.

## 7. Operations

**OK / gap:** docs/DEPLOYMENT_CHECKLIST.md covers private SQLite/media backups,
restore rehearsal, staged migration-before-reload and rollback. Actual current backup
schedule, off-host copy, restore result and retention **UNVERIFIED**. No automated
backup/restore deployment system observed. Define manual recovery ownership first (2 SP).

**gap:** no project LOGGING/error tracker/health route; Django/platform defaults remain.
Console backend can log CV-bearing mail and report a false successful send. WP15 needs
sanitized events, health and a manual Actions/quota/renewal routine (3 SP). Production
log access/rotation/retention **UNVERIFIED**. Don't add a paid service.

**OK / gap:** tracked ajiri-backend/.env.example lists development/production setup,
but future SMTP quota/disable settings do not yet exist; keep examples value-free for
secrets and review stale deployment descriptions. No secret files read for this audit.

**OK / gap:** .gitattributes scopes LF to build-sensitive files; committed frontend_build
and CI's exact diff guard exist. scripts/build_frontend.ps1 is under ajiri-backend/,
normalizes HTML, but uses npm install instead of npm ci and replaces target tree.
Fresh build consistency **UNVERIFIED this round**; don't regenerate in docs-only work.
Recommend later reproducible packaging review and line-ending policy check (1–2 SP).

## 8. Performance

**gap (static evidence):** jobs/views.py JobList queryset lacks prefetch; JobListSerializer
calls calculate_match_score per job, which issues values_list for profile/job skills.
Application/Notification lists dereference job fields without select_related. Recommend
query-count regression tests and bulk skill sets/select_related (3 SP). Actual query
counts and latency **UNVERIFIED**, no production/load probe.

**OK / gap:** unique source_url and unique user/job pairs provide indexes/duplicate guards;
FK indexes exist. No explicit composite indexes for active/scam/posted ordering or
user/status/date in jobs/models.py. Choose indexes from EXPLAIN and representative
fixtures, not assumptions (2 SP; additive migration later).

**gap:** matching.py sweep loops all active jobs x all profiles with repeated skill
queries and synchronous mail. ingestion.py does per-entry exists/create/scam/match work;
views.py parses the whole body. SQLite has one writer, 20s lock timeout; feed body cap
10 MB. No chunking, request time budget or cache; inactive profiles are not excluded
from the matching iteration. Large fan-out risks worker timeout/partial completion.
Concurrent draft creation also does check-then-save around file writes: uniqueness
blocks duplicate rows but may leave orphan files/500s (not reproduced).
Recommend bounded query counts, inactive-user exclusion, explicit budgets and chunked
work proposal before scaling; ingestion changes require separate approval (5–8 SP).
No claim that today's small deployment exceeds capacity.

## Priorities

### P0 — before opening to real users / real employer mail

- Enforce configured password validators and content-aware upload validation.
- Approve and test CSRF/origin protection and auth/resource abuse limits; disabled-user
  refresh/sweep behaviour must be reviewed and covered. No auth change authorized yet.
- Resolve false email success/log exposure: gate real sending until verified mailbox,
  provider/sender approval, quotas and controlled owner-inbox rollout are ready.
- Legal-review privacy/consent and functioning rights-request contact/process; decide
  retention and backup access. DRAFT only, not a legal compliance certification.
- Michael verifies HTTPS redirect/proxy/cookies/headers and rehearsed private backups;
  stage HSTS only after HTTPS is known safe. Confirm renewal owner.
- Complete Python advisory scan/triage; no known Python vulnerability asserted here.

### P1

Password reset + verification UX, export/deletion fulfilment, monitoring/health,
accurate alert retries, query-count fixes, draft-creation race tests, patch maintenance,
CSP design and targeted browser/accessibility regressions. Some account controls are
also prerequisites of real sending, even if broader UX follows later.

### P2

Caching after measurement, schema/versioning formalization, broader coverage/E2E tooling,
index/load tuning, deterministic packaging cleanup, optional SEO/PWA after product review.
Production fixture cleanup remains a separately authorized housekeeping task.

## Checkpoint 3A remediation status (local only)

- WP11 password bypass: fixed in registration field validation and manager creation;
  custom-user admin forms use Django policy. Existing passwords/login unchanged.
  Other historical findings remain open until listed here with executed checks.

- WP12 absent throttling: scoped request limits implemented for five endpoints;
  proxy parsing tested. Shared-worker counters remain OPEN (LocMemCache), as do
  durable email quotas. Live proxy/cache topology remains UNVERIFIED; see THROTTLING.md.

- WP13 extension-only uploads: fixed with bounded PDF/DOC/DOCX structural checks,
  5 MB ceiling and UUID stored names. Full parsing and malware scanning remain OPEN;
  signature checks cannot certify files safe. Existing stored files are unchanged.

- WP14 W004/W008: addressed by DEBUG=False defaults and env-configurable profile
  (HSTS 300s, SSL redirect), with proxy/no-loop tests. Session/CSRF secure flags and
  standard headers configurable. Actual production remains UNVERIFIED. HSTS broader
  scope/preload advisories W005/W021 are deliberately retained, not silenced.

- WP15 refresh CSRF: design completed in REFRESH_COOKIE_CSRF_DESIGN.md; implementation
  remains OPEN, as authorized. No SameSite/origin/token validation changes were made.

### Remaining open after Checkpoint 3A

CSRF implementation; inactive-user refresh/alerts; shared-cache/atomic abuse protection;
durable mail quotas, real SMTP and truthful alert receipt handling; password reset and
mailbox verification; privacy/legal/consent and account rights; malware scanning/full
render validation; live proxy/header/cache verification and backups/renewal; Python
advisory scan, coverage/E2E/a11y, dependency patches; CSP/Permissions-Policy; query-count,
scaling/index/caching work; API schema/versioning, SEO/PWA and packaging cleanup.
None is silently declared fixed by a deploy check or a passing local suite.

## Sprint 3 AJ-14 evidence — 15 October 2026

Supersedes the original audit's UNVERIFIED Python scan and unmeasured backend
coverage only. Tested source 5e15a11 in an isolated local checkout. Existing tools:
pip-audit 2.10.1, coverage 7.16.2, Python 3.12. No dependency changes or installs.

`python -m pip_audit -r requirements-prod.txt --progress-spinner off` completed
with exit 1: **15 known vulnerabilities in two packages**, Django 6.1 and PyJWT
2.13.0. Django: PYSEC-2026-3717 (reported fixes 5.2.17/6.0.8/6.1.1).
PyJWT: PYSEC-2026-4140 through PYSEC-2026-4152 inclusive, and PYSEC-2026-4183.
The scanner reports 2.14.0 or 2.15.0 fixes for most PyJWT findings, but lists no
fix version for PYSEC-2026-4146. Do not assume upgrading alone clears every finding.
These are advisory matches, not demonstrated exploits or a production inventory.
Triage and compatible patch upgrades require a separate reviewed dependency task;
**P0 release risk remains open**. No ignore flags, audit fixes or dependency edits.

Fresh full suite: 88 run, 87 passed, one Windows symlink privilege skip.
`manage.py check` passed; `makemigrations --check --dry-run` found no changes.
Statement coverage: **90% (1182 statements, 121 missed)** excluding tests,
migrations and upload fixtures. Unfiltered total was 94%, inflated by tests.
No branch, frontend, E2E or production coverage measured. Notable gaps: tasks.py,
fix_mojibake command and WSGI/ASGI entrypoints 0%; CV generator 76%; cover-letter
generator and jobs serializers 80%; upload validator 89%. Coverage is not correctness.

Reproduce from ajiri-backend using its existing virtualenv, with local DEBUG=True,
in-memory EMAIL_BACKEND and PYTHON_DOTENV_DISABLED=1. Keep COVERAGE_FILE outside
the repo so existing local .coverage remains untouched:

```powershell
$env:COVERAGE_FILE = Join-Path $env:TEMP 'ajiri-sprint3-verified.coverage'
.\.venv\Scripts\python.exe -m pip_audit -r requirements-prod.txt --progress-spinner off
.\.venv\Scripts\python.exe -m coverage run --source=accounts,profiles,jobs,config manage.py test --noinput
.\.venv\Scripts\python.exe -m coverage report --omit='*/test*.py,*/migrations/*,*/upload_fixtures.py'
```

See SPRINT3_REVIEW.md for issue acceptance gaps and manual-only operations.

### Sprint 3 confirmed follow-up

AJ-10 now supports an opt-in private file-cache alias via THROTTLE_CACHE_DIR.
Independent processes share sequential request budgets; this does not make DRF's
read/modify/write atomic. Local default and ingestion flow remain unchanged.
Live cache/proxy activation is still unverified. AJ-13 option C is approved as a
design only, with implementation deferred. Read-only production HEAD checks found
HTTP-to-HTTPS redirect and standard frame/referrer/nosniff headers, but **no HSTS**;
do not declare the deployment-hardening finding fully fixed on the live site.

## Checkpoint 3B WP16 — current requirement scans

16 October 2026: both production/dev requirement scans return no known vulnerabilities.
See DEPENDENCY_ADVISORIES.md for all 15 historical IDs, primary metadata discrepancies,
static applicability, exact captured commands/output and installed-environment distinction.
Current pins already contain the upgrades; no dependency files changed. No production fix claimed.

## Checkpoint 3B Phase A — local remediation, 16 October 2026

This dated status supersedes earlier open findings only for the reviewed local code:
cookie mutation CSRF protection is implemented with Django tokens and exact origins
(WP18); minimal database health and allowlisted private rotating error logs are
implemented (WP21); verified manual private backups and report-only retention are
implemented (WP22). See CHECKPOINT3B_PHASE_A_REVIEW.md for actual gates and limits.
Production configuration/rollout remains UNVERIFIED and Michael-owned. No deployment.

Still open: SMTP and truthful alert delivery; password reset/mailbox verification;
inactive-user policy; legal/privacy/consent and rights; exact delivery quotas and
uncertain outcomes; automatic free-tier scheduling availability; production proxy/
cache/header verification; platform console email exposure; malware scanning;
coverage improvements/E2E/a11y; API contract, CSP/Permissions-Policy, performance/
query scaling, SEO/PWA and packaging follow-ups. New backup tooling does not imply
an executed production backup or a complete application restore test. No migrations
or dependency changes were made in this phase.

</details>
<details>
<summary>Read dated details — source variant 2</summary>

Source: `docs/MODERNISATION_AUDIT.md`; input SHA-256 `d0cbad2a0316bc2d2b9b9c080e855cb63932a1b06235614fe53d0fa1cf70ed75`.

Earlier checkout differences; unchanged text is retained in the full record above.

```diff
--- consolidated full record
+++ earlier checkout version
@@ unchanged lines omitted @@
 # Modernisation audit — read-only
 
-
 15 October 2026; source revision `24a0ae2` on integration/checkpoint-3. No application,
 configuration, dependency, CI or production changes made. Status is **OK**, **gap**,
@@ unchanged lines omitted @@
 scaling/index/caching work; API schema/versioning, SEO/PWA and packaging cleanup.
 None is silently declared fixed by a deploy check or a passing local suite.
-
-## Sprint 3 AJ-14 evidence — 15 October 2026
-
-Supersedes the original audit's UNVERIFIED Python scan and unmeasured backend
-coverage only. Tested source 5e15a11 in an isolated local checkout. Existing tools:
-pip-audit 2.10.1, coverage 7.16.2, Python 3.12. No dependency changes or installs.
-
-`python -m pip_audit -r requirements-prod.txt --progress-spinner off` completed
-with exit 1: **15 known vulnerabilities in two packages**, Django 6.1 and PyJWT
-2.13.0. Django: PYSEC-2026-3717 (reported fixes 5.2.17/6.0.8/6.1.1).
-PyJWT: PYSEC-2026-4140 through PYSEC-2026-4152 inclusive, and PYSEC-2026-4183.
-The scanner reports 2.14.0 or 2.15.0 fixes for most PyJWT findings, but lists no
-fix version for PYSEC-2026-4146. Do not assume upgrading alone clears every finding.
-These are advisory matches, not demonstrated exploits or a production inventory.
-Triage and compatible patch upgrades require a separate reviewed dependency task;
-**P0 release risk remains open**. No ignore flags, audit fixes or dependency edits.
-
-Fresh full suite: 88 run, 87 passed, one Windows symlink privilege skip.
-`manage.py check` passed; `makemigrations --check --dry-run` found no changes.
-Statement coverage: **90% (1182 statements, 121 missed)** excluding tests,
-migrations and upload fixtures. Unfiltered total was 94%, inflated by tests.
-No branch, frontend, E2E or production coverage measured. Notable gaps: tasks.py,
-fix_mojibake command and WSGI/ASGI entrypoints 0%; CV generator 76%; cover-letter
-generator and jobs serializers 80%; upload validator 89%. Coverage is not correctness.
-
-Reproduce from ajiri-backend using its existing virtualenv, with local DEBUG=True,
-in-memory EMAIL_BACKEND and PYTHON_DOTENV_DISABLED=1. Keep COVERAGE_FILE outside
-the repo so existing local .coverage remains untouched:
-
-```powershell
-$env:COVERAGE_FILE = Join-Path $env:TEMP 'ajiri-sprint3-verified.coverage'
-.\.venv\Scripts\python.exe -m pip_audit -r requirements-prod.txt --progress-spinner off
-.\.venv\Scripts\python.exe -m coverage run --source=accounts,profiles,jobs,config manage.py test --noinput
-.\.venv\Scripts\python.exe -m coverage report --omit='*/test*.py,*/migrations/*,*/upload_fixtures.py'
-```
-
-See SPRINT3_REVIEW.md for issue acceptance gaps and manual-only operations.
-
-### Sprint 3 confirmed follow-up
-
-AJ-10 now supports an opt-in private file-cache alias via THROTTLE_CACHE_DIR.
-Independent processes share sequential request budgets; this does not make DRF's
-read/modify/write atomic. Local default and ingestion flow remain unchanged.
-Live cache/proxy activation is still unverified. AJ-13 option C is approved as a
-design only, with implementation deferred. Read-only production HEAD checks found
-HTTP-to-HTTPS redirect and standard frame/referrer/nosniff headers, but **no HSTS**;
-do not declare the deployment-hardening finding fully fixed on the live site.
-
-## Checkpoint 3B WP16 — current requirement scans
-
-16 October 2026: both production/dev requirement scans return no known vulnerabilities.
-See DEPENDENCY_ADVISORIES.md for all 15 historical IDs, primary metadata discrepancies,
-static applicability, exact captured commands/output and installed-environment distinction.
-Current pins already contain the upgrades; no dependency files changed. No production fix claimed.
-
-## Checkpoint 3B Phase A — local remediation, 16 October 2026
-
-This dated status supersedes earlier open findings only for the reviewed local code:
-cookie mutation CSRF protection is implemented with Django tokens and exact origins
-(WP18); minimal database health and allowlisted private rotating error logs are
-implemented (WP21); verified manual private backups and report-only retention are
-implemented (WP22). See CHECKPOINT3B_PHASE_A_REVIEW.md for actual gates and limits.
-Production configuration/rollout remains UNVERIFIED and Michael-owned. No deployment.
-
-Still open: SMTP and truthful alert delivery; password reset/mailbox verification;
-inactive-user policy; legal/privacy/consent and rights; exact delivery quotas and
-uncertain outcomes; automatic free-tier scheduling availability; production proxy/
-cache/header verification; platform console email exposure; malware scanning;
-coverage improvements/E2E/a11y; API contract, CSP/Permissions-Policy, performance/
-query scaling, SEO/PWA and packaging follow-ups. New backup tooling does not imply
-an executed production backup or a complete application restore test. No migrations
-or dependency changes were made in this phase.
```

</details>

<a id="record-phase1-review"></a>

### phase1 review

<details>
<summary>Read dated details — source variant 1</summary>

Source: `docs/PHASE1_REVIEW.md`; input SHA-256 `c91778f1f1034a8ad0d50dda661a80c43d2425d061ffa27ae5865229c4ce6381`.

# Phase 1 review


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

## 1. What changed

- `ajiri-frontend/src/index.css`, `index.html`, `package*.json`, `vite.config.js`: semantic light/dark tokens, Tailwind 4, system fonts, Radix primitives and lucide icons. JSX only.
- `src/components`, `src/hooks`, `src/lib`: reusable controls, dialogs, toasts, states, pagination, match/status badges; responsive app shell; protected routes; cancellable resource reads; formatting helpers.
- `src/pages/Login.jsx`, `JobList.jsx`, `JobDetail.jsx`: redesigned login, API-backed filters and pagination, match explanation, clear prepare/review application action.
- Applications and Notifications adopt shared states, badges and pagination. Register retains its existing flow and receives an accessible error alert. Their feature completion remains Phase 2.
- `docs/DESIGN_SYSTEM.md` and `ajiri-backend/docs/CONCEPTS.md`: usage rules, tokens, verification instructions and plain-language concepts.
- `ajiri-backend/frontend_build`: regenerated static deployment build, including lazy route chunks.
- `.gitignore`: ignores the workspace npm cache and isolated QA files inside it.

Backend Python code, migrations, auth client, CORS and CI configuration are unchanged.

## 2. How to run and verify

See DESIGN_SYSTEM.md for exact PowerShell commands. Verification performed on Node 22.15.0 and Python 3.12.6:

- Clean `npm ci`: pass, 0 reported vulnerabilities.
- `npm run lint`: pass without lint warnings.
- `npm run build`: pass; main JS about 90 KB gzip, shared runtime chunk about 36 KB gzip, CSS about 5 KB gzip. Route chunks load on demand. These are build sizes, not measured mobile transfer totals.
- Repository `build_frontend.ps1`: pass; generated build compared with dist.
- Django system check: pass.
- Existing Django suite: 19 tests pass. TEMP/TMP were directed to an ignored workspace directory because sandbox-default temp directories denied writes.
- Browser smoke checks against real Django with an isolated in-memory database: protected redirect and return after login; job detail; prepare application and generated document links; pagination; title search resetting page; filtered empty results; notification mark-read; light/dark persistence; mobile disclosure/navigation; dialog Escape and focus restoration.
- Expired access tokens: server logs confirm 401 -> refresh 200 -> original request succeeds, without visible logout.
- Responsive checks: desktop plus 360px and 390px, without horizontal overflow on checked views.
- Palette checks: normal text pairs meet 4.5:1; input borders meet 3:1. Light muted/surface is 6.04:1 and primary/soft 6.37:1; dark equivalents are 8.43:1 and 7.38:1. This is not a full WCAG audit.

No production requests, real emails or real user data were used in QA.

## 3. Decisions and why

- System fonts avoid external font downloads.
- Locally owned shadcn-style JSX components use Radix for focus-sensitive behaviour; native selects keep mobile controls simple. No TypeScript migration.
- Search is submitted explicitly, avoiding a request on every keystroke. Filters live in the URL for bookmarking and browser history.
- The API client remains unchanged to preserve cookie refresh and token handling.
- Route guards guide navigation; Django continues to enforce authorization.
- The shell stays visible while a lazy page downloads.
- Existing Celery worker/Beat and Redis configuration remains for optional local use. SQLite is the configured database. Production documentation uses GitHub Actions for ingestion/sweeps. No active Postgres configuration was found. Running production services were not inspected.

## 4. Risks and follow-ups

- Michael's browser/Postman review is still required before merge; no push or merge is part of Phase 1.
- Profile notification API gaps, application editing/dismissal and external-employer confirmation flow remain Phase 2, each on its own branch with tests.
- Registration field-by-field validation, CV management and subscriptions remain Phase 2.
- Frontend automated component tests remain Phase 3. Browser checks here are smoke checks, not an automated regression suite.
- Production email delivery and payment processing were not exercised.

Suggested Monday.com tasks (relative story points):

| Completed task | Points |
| --- | ---: |
| Tokens, themes, accessible UI primitives and design documentation | 5 |
| Responsive shell, protected routes and shared page states | 5 |
| Login redesign and return-to-page behaviour | 3 |
| Job listing redesign, API filters and pagination | 5 |
| Job detail redesign and application preparation feedback | 3 |
| Build packaging and Phase 1 verification | 3 |

Stop after Phase 1 for Michael's review before starting Phase 2.

</details>
<details>
<summary>Read dated details — source variant 2</summary>

Source: `docs/PHASE1_REVIEW.md`; input SHA-256 `5b596fdf9d002f3591dbd751c17cf51a6fed79008ce7d85d87db54f20f12ae23`.

Earlier checkout differences; unchanged text is retained in the full record above.

```diff
--- consolidated full record
+++ earlier checkout version
@@ unchanged lines omitted @@
 # Phase 1 review
 
-
-> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.
-
 ## 1. What changed
 
```

</details>

<a id="record-private-media-design"></a>

### private media design

<details>
<summary>Read dated details</summary>

Source: `docs/PRIVATE_MEDIA_DESIGN.md`; input SHA-256 `f2394020c87fea4b962b82b96f8c4c1d497cdbdc61d44c03a5f16db1c0c58284`.

# Private media design — Checkpoint 2 preparation

15 October 2026. **Proposal only; not implemented or deployed.** Base: fetched
`origin/main` at `e5e0038`, containing Checkpoint 1 tip `b8c1881` and WP1-WP6.
No hosting dashboard, production files, database or environment was accessed.
Approval of this document is required before implementation. Prompt 2 has not
been supplied, so no exceptions to standing rules are assumed.

## Current storage and exposure

Repository evidence:

| Data | Model field | Relative storage name / creation |
|---|---|---|
| Uploaded CV | `profiles.models.Profile.cv_file` | `cvs/<uploaded filename>`; default storage sanitizes names and resolves collisions |
| Saved application CV | `jobs.models.Application.generated_cv` | `applications/cvs/<uuid hex>_CV_<company>.docx` |
| Saved cover letter | `Application.generated_cover_letter` | `applications/cover_letters/<same uuid hex>_Cover_Letter_<company>.docx` |

All three use default FileSystemStorage. `config/settings.py` currently sets
`MEDIA_ROOT = BASE_DIR / 'media'` and `MEDIA_URL = '/media/'`. Locally that root
is `C:\dev\ajiri\ajiri-backend\media`. FileField database values are relative
names, not file contents or absolute paths. Existing default DRF FileField
representations expose media URLs in Profile/Application JSON. Preserving these
JSON fields initially avoids a separate API contract change; their legacy URLs
must cease serving bytes. UI blob downloads already use protected endpoints.

`jobs/views.py` prepares application snapshots once with `ContentFile` and
`FieldFile.save()`. Sending email reads the stored attachments; moving storage
must preserve those exact bytes, names and attachment behaviour. A newly generated
CV (`GenerateCVView`) or cover letter (`GenerateCoverLetterView`) is produced in
memory on demand and returned as DOCX, rather than stored by those actions.

`config/urls.py` adds Django's media serving route only when DEBUG is true.
Production already omits that route. The React fallback excludes `media/`.
`ajiri-backend/docs/DEPLOY_PYTHONANYWHERE.md` instructs a mapping from `/media/`
to `/home/YOURNAME/ajiri/ajiri-backend/media`, bypassing Django permissions.
This is documented configuration, not a verified snapshot of the live account.
The runbook's Python 3.13 example is historical; this proposal uses the user's
Python 3.12 environment and does not alter any environment or CI matrix.

Current protected downloads:

- `/api/profiles/me/cv/`: authenticated caller's uploaded CV.
- `/api/jobs/applications/<id>/documents/cv/` and `.../cover-letter/`:
  authenticated owner only; another user's application is 404.
- Fresh document generators remain authenticated DOCX responses.

Saved downloads use `FileResponse`, attachment filenames, and
`Cache-Control: private, no-store`; anonymous requests return 401. Missing files
return 404. The existing auth client, refresh cookies/interceptors, CORS, response
statuses, headers, document contents and endpoint paths must remain unchanged.

## Options and recommendation

| Option | Benefit | Limitation / cost |
|---|---|---|
| A. Dedicated unmapped storage root; remove all direct media serving | Defence against both local debug serving and public hosting mappings; same relative names and owner endpoints | Requires operational copy/verification, storage capacity and manual cutover |
| B. Keep current root; remove DEBUG media route and PythonAnywhere media mappings | Smallest change; no relocation | Future accidental mapping of the repository/media folder reopens exposure; weaker separation |
| C. Randomize every filename, including uploads | Reduces casual guessing | A leaked URL still grants access; requires renaming existing references; not an authorization solution |

Recommend **A**, with B's removal of direct serving. C may be defence in depth,
but is insufficient alone; generated documents already have random prefixes.
PythonAnywhere explicitly warns that files inside mapped directories can be
publicly reachable ([account security guidance](https://help.pythonanywhere.com/pages/SecuringYourAccount)).

Proposed configuration: make the default media storage root configurable using
an absolute `PRIVATE_MEDIA_ROOT` environment value, with an unmapped local default
outside the repo (for example `C:\dev\ajiri-private-media`). Set MEDIA_ROOT to
that private location while retaining existing FileField definitions and relative
names. Do not add a second storage backend or change `.url()` behaviour in this
iteration; keeping MEDIA_URL as a legacy URL prefix does not serve anything by
itself. Remove the DEBUG media route entirely, and keep `/media/` excluded from
the SPA fallback. No web server/static mapping, WhiteNoise directory, symlink or
parent mapping may expose the private root. Public static/frontend assets remain
separate. Future public uploads must use separate, explicit public storage.

FileSystemStorage roots and URL prefixes are separate configuration concepts
([Django storage API](https://docs.djangoproject.com/en/6.1/ref/files/storage/)).
Storage access remains through FieldFile.open/save, preserving owner endpoints
and email attachment access. Configure new files as owner read/write (0600) and
directories as owner accessible (0700) on Linux; verify the web worker can operate
as that account. Permissions alone cannot protect files deliberately mapped by a
web server, so removing mappings is essential.

## Migration and existing data

The recommended default-storage-root change needs **no model/schema migration**
and no database row rewrites: `cvs/...` and `applications/...` stay identical.
Confirm with `makemigrations --check --dry-run` during implementation. Choosing
field-specific custom storage instead could create migration state changes and
would need separate approval. AUTH_USER_MODEL and migration history are untouched.

There is a real **operational data relocation**, even with unchanged DB values.
Never silently move files at application startup or regenerate saved snapshots.
Back up the database and media together while writes are paused. Keep the source
copy for rollback in an unmapped location; removal is a later manual retention
decision. Uploaded replacements/deleted rows can leave orphaned files. Inventory
all regular source files, including orphans, so they do not remain publicly
exposed; report unreferenced files separately without deleting them.

### Proposed management command contract (not available yet)

`relocate_private_media` would support explicit absolute `--source`, `--destination`,
`--dry-run`, `--apply`, `--manifest`, and a read-only `--verify` mode. Dry-run is
the default; apply requires explicit selection. It must not depend on which root
is currently configured for the web app. Example future commands:

```bash
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --dry-run --manifest "$AUDIT/plan.json"
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --apply --manifest "$AUDIT/applied.json"
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --verify --manifest "$AUDIT/verified.json"
```

These are a proposed interface, not runnable instructions for current main.
Dry-run must not create directories, manifests, files or DB updates; with
`--manifest` it reports where the manifest would be written. Read-only verify
prints results; persist its output manually to a protected audit location if
needed. Apply writes a protected manifest containing relative names, sizes,
SHA-256 checksums and copied/already-identical/error status; no file contents,
tokens or user details. Relative filenames can contain personal information, so
manifests and logs must remain private and uncommitted.

Required safety behaviour:

- Resolve roots; reject identical/nested roots, filesystem roots, symlinks,
  traversal, absolute DB names and paths escaping either root. Do not follow
  symlinks found inside the tree. Refuse a destination known to be inside a
  local static/frontend root; actual host mappings require Michael's inspection.
- Inventory the three FileFields, deduplicate shared names and identify missing
  referenced files and orphaned disk files. Missing references or unsafe names
  prevent a successful cutover; do not fabricate empty replacements.
- Preflight disk headroom and permissions. Copy bytes to exclusive temporary files
  under the destination, checksum and atomically finalize without overwriting a
  different file. Existing identical destination files are safe resumptions;
  different content at the same name is a hard conflict, not a suffix rename.
- Preserve all relative names and content; never use normal storage save collision
  renaming to relocate. Do not update rows, delete source files, or change status.
- Rerun safely after interruption, returning nonzero for any unresolved error.
  Verify the full source inventory plus every DB reference after copy. Pause all
  writers throughout inventory/copy/switch/verification; no best-effort live copy.

## PythonAnywhere manual cutover — Michael only, after implementation approval

Nothing in this section has been performed. Verify the actual clone path, Python
3.12 virtualenv, account and all static mappings before proceeding. Replace
`YOURNAME`, the approved revision, and backup timestamp explicitly. The existing
deployment runbook's public media mapping must not be followed for this change.

1. Schedule a maintenance window. Pause all users/uploads/application preparation,
   ingestion and sweeps, including GitHub Actions/external callers, and stop any
   local workers writing this database/storage. If writes cannot be paused, abort
   relocation. Use your established maintenance procedure; none is introduced here.
2. In Web → Static files, record all existing mappings privately. Remove `/media/`
   **and any aliases/parent mappings** exposing the old media root or planned private
   root. Reload the app, then test a known old URL anonymously: it must not return
   document bytes. Removing a Django route alone cannot defeat this mapping.
   Keep legitimate `/static/` and frontend asset mappings unchanged.
3. In your PythonAnywhere **Bash** console, prepare account-owned private folders:

   ```bash
   cd /home/YOURNAME/ajiri/ajiri-backend
   workon ajiri
   python --version  # must be your approved Python 3.12 environment
   umask 077
   OLD=/home/YOURNAME/ajiri/ajiri-backend/media
   NEW=/home/YOURNAME/ajiri-private-media
   AUDIT=/home/YOURNAME/ajiri-private-backups/checkpoint2-YYYYMMDD-HHMMSS
   test -d "$OLD" || exit 1
   mkdir -m 700 -p "$NEW" "$AUDIT"
   chmod 700 "$NEW" "$AUDIT"
   ```

   Inspect resolved paths (`realpath`) and every Web mapping: neither private
   directory nor any ancestor may be mapped. Never use chmod 777. Verify the web
   worker's account can read/write the new directory; if not, stop for a platform-
   specific permissions review rather than making it world-readable.
4. With writers paused, make a consistent SQLite backup using your established
   SQLite backup procedure (including WAL handling); archive the complete old media
   tree, settings revision and private environment backup under AUDIT. Verify the
   backup can be read/restored. Do not put backups in Git or a mapped folder.

   For the current default `db.sqlite3` location, these Bash commands use SQLite's
   backup API rather than copying a potentially incomplete main file. If the
   configured database differs, stop and substitute its verified location first:

   ```bash
   test -f db.sqlite3 || exit 1
   export AUDIT
   python -c 'import os, sqlite3; from pathlib import Path; src=sqlite3.connect("file:db.sqlite3?mode=ro", uri=True); dst=sqlite3.connect(str(Path(os.environ["AUDIT"])/"db.sqlite3")); src.backup(dst); result=dst.execute("PRAGMA integrity_check").fetchone()[0]; dst.close(); src.close(); assert result == "ok", result'
   tar -czf "$AUDIT/media.tar.gz" -C "$OLD" .
   tar -tzf "$AUDIT/media.tar.gz" >/dev/null
   git rev-parse HEAD > "$AUDIT/revision.txt"
   if test -f .env; then cp -p .env "$AUDIT/environment.backup"; chmod 600 "$AUDIT/environment.backup"; fi
   ```

   Require successful exit status for every command; stop at the first failure.
   An archive listing and integrity check are initial checks, not a restore drill:
   verify recovery in a separate private test directory before cutover.
5. Deploy the separately approved implementation revision in the clone using the
   established deployment procedure. Do not alter auth, CORS, WSGI routing or CI.
   Before reloading, run the proposed command's dry-run; resolve all missing files,
   conflicts, unsafe paths and disk space issues. Then run apply and verify using
   the explicit OLD/NEW paths above. Inspect counts and hashes, not just exit status.
6. In the existing server environment-loading mechanism (the private `.env` beside
   manage.py if that is how your app is configured), set
   `PRIVATE_MEDIA_ROOT=/home/YOURNAME/ajiri-private-media`. Keep DEBUG=False. Existing
   process environment values override `.env`; check the effective value without
   printing other settings or secrets. Protect the environment file with chmod 600.
   Apply owner-only file/directory permissions to copies using the approved command;
   verify future uploads receive those permissions too.
7. Web → Reload. Test known old URLs with GET and HEAD, without credentials and
   while signed in: expect 404 (or host denial), never file bytes, a redirect to
   the file or an SPA 200. Check uploaded CV and both snapshot types. Then test owner
   downloads, another user's access, anonymous requests, new upload/preparation and
   captured-mail attachment generation. Confirm byte hashes and no-store headers.
   Never test delivery against a real employer. Inspect server error logs privately.
8. Reconfirm no mapping exposes OLD, NEW, backups or manifests. Retain unmapped OLD
   and backups for an agreed retention period. Resume writers only after all checks
   pass. Update deployment documentation in the later implementation package.

PythonAnywhere mapping changes require reload and tests through the actual web
server ([static-file instructions](https://help.pythonanywhere.com/pages/DjangoStaticFiles)).
A Django test client cannot validate that platform layer. No mapping changes,
folders, chmod operations, environment edits or command execution above are part
of this documentation-only preparation.

## Required tests before implementation acceptance

Use synthetic data, temporary directories and captured email only.

| Layer | Required assertion |
|---|---|
| Django routing, DEBUG true and false | Existing files requested via `/media/cvs/...`, both application subpaths, and encoded/traversal variants return 404; GET/HEAD never stream private bytes or return SPA HTML as success. Reload URL configuration per setting; override_settings alone can leave cached routes |
| Uploaded CV endpoint | Owner gets original bytes, filename and private/no-store; anonymous 401; profile ownership cannot be supplied by a caller; missing file 404 |
| Snapshot endpoints | Owner gets identical saved CV/letter bytes after profile edits; non-owner 404; anonymous 401; invalid kind/missing file 404; attachment and no-store headers retained |
| New writes and email | Upload and preparation write only under private root; email uses same snapshot bytes with captured backend; no public copy created |
| Relocation | Dry-run changes nothing; no DB mutation; hashes/names preserved; orphans counted/copied; shared references deduplicated; rerun identical files succeeds; conflicting/missing files, traversal, symlinks, nested roots, permission/disk errors fail; interrupted copies resume safely |
| Existing regression suite | Django check, migration drift check, full backend suite; existing frontend install/lint/tests/build gates without packaging or committing a new frontend_build for backend/docs-only work |
| Real PythonAnywhere after manual cutover | Actual known legacy URLs fail anonymously and authenticated, including every old mapping alias; owner endpoint succeeds. Test with cache bypass and inspect response bytes, not status alone |

## Rollback and risks

If verification fails before writers resume, keep maintenance in place. Restore
the previous application revision and root setting so owner endpoints read OLD;
**do not restore public media mappings**. Production's existing DEBUG=False route
behaviour allows this privacy-preserving rollback. Verify owner downloads again.
Do not automatically restore an old DB over newer user records.

If new writes have already occurred, pause them again and reconcile new private
files back to the old *unmapped* root using the manifest/hash safeguards, or keep
the private-root configuration while fixing forward. Avoid a blind reverse move
or deletion. Restoring a backup is a separate destructive operation requiring
approval. Local rollback to older code with DEBUG=True must not re-expose a root
containing personal files; retain the no-media-route protection or keep it offline.

Risks: copies double storage temporarily; filesystem and DB backups can diverge
without a write freeze; old aliases/symlinks or broad parent mappings can defeat
isolation; stale environment values can select the wrong root; permission errors
can break uploads and attachment reads; missing originals cannot be recreated
faithfully. Browser/proxy copies downloaded before cutover cannot be revoked, and
prior public exposure may require a separate incident assessment. This proposal
does not claim to erase previously downloaded copies. Backups and manifests need
their own retention and access controls. No deletion policy is introduced here.

## Preparation verification and approval boundary

This document is based on repository inspection and official platform/storage
documentation, not a production audit. Runtime implementation, relocation command,
new tests and deployment are deliberately pending approval. No auth, CORS, endpoint,
model, hosting, dependency or build changes are included. Approval should resolve
the recommended option, maintenance window, destination root and retention policy
before implementation starts.

Preparation checks run on 15 October 2026 (Africa/Nairobi): Django `check`
passed, `makemigrations --check --dry-run` reported no changes, and all 57 existing
Django tests passed in 51.762 seconds using temporary test storage and captured
email. `git diff --check` passed; a section-by-section comparison confirmed all
eight standing AGENTS sections unchanged. These checks validate the unchanged
baseline, not the proposed privacy implementation. `npm ci` failed with Windows
EPERM unlinking the locked Rolldown native binary. Frontend lint/tests/build were
not run after that failed install; the frontend gate is **unverified**. A failed
clean install may leave node_modules incomplete; stop Ajiri Vite and rerun `npm ci`
before the next frontend session. No dependency manifest or frontend_build changed.

Git identity was checked without changing configuration:
`11541427+michael-mathenge@users.noreply.github.com`. The documentation commit's
author and committer identity must be confirmed in the handback report.

</details>

<a id="record-refresh-cookie-csrf-design"></a>

### refresh cookie csrf design

<details>
<summary>Read dated details — source variant 1</summary>

Source: `docs/REFRESH_COOKIE_CSRF_DESIGN.md`; input SHA-256 `daa0d137dce3ccb35544f172e97f9d2af2fe59e3e6818a40ce444a3eff3a0ed4`.

# Refresh-cookie CSRF design — Checkpoint 3A WP15

Design only. Michael approved option C on 15 October 2026 in the Sprint 3 follow-up.
This records design acceptance (AJ-13), not authorization to implement or deploy it.
No mitigation below is implemented or approved for automatic deployment.
JWT/refresh-cookie logic remains unchanged. Changes to auth, CORS or the interceptor
need Michael's separate approval. Request throttling is not a CSRF mitigation.

## Actual request boundary

- accounts/views.py LoginView and RefreshView are DRF APIViews. Installed DRF marks
  APIViews csrf_exempt; JWT authentication does not enforce Django session CSRF checks.
  The presence of CsrfViewMiddleware alone therefore does not protect this custom flow.
- Refresh takes only refresh_token from a cookie, returns access in JSON and rotates/
  blacklists the token. Cookie: HttpOnly, Secure outside DEBUG, SameSite=Lax, path /,
  seven-day max age, no Domain attribute (host-only). Do not expose its value to JS.
- Production UI/API are same origin. config/settings.py has CORS_ALLOW_CREDENTIALS=True;
  default production CORS_ALLOWED_ORIGINS is empty, development permits localhost/127.0.0.1
  on port 5173. The frontend axios client uses withCredentials and a plain axios refresh
  request. Refresh requires no access-token Authorization header by design.
- Lax generally excludes cookies from cross-site POST, but same-site is broader than
  origin: another port or a related host may be same-site. HttpOnly prevents reading,
  not browser attachment. CORS limits reading responses/preflight, not all requests.
  A form POST can trigger a state-changing request without reading its response.
- Consequences may include token rotation/session disruption; login CSRF can confuse
  account identity. This audit has not demonstrated an end-to-end exploit or cross-site
  token exfiltration. XSS/token theft and inactive-user refresh are separate open risks.

## Options

| Option | Benefit | Trade-off / limits |
|---|---|---|
| A. SameSite=Strict only | Small cookie change, stronger cross-site attachment restriction | Still allows same-site cross-origin requests; can affect external-navigation/embedded flows; not a complete CSRF control |
| B. Exact Origin validation plus non-simple custom header on login/refresh | Small explicit browser boundary; cross-origin attacker cannot add header without preflight; no new secret required | Reject null/absent Origin by default; nonbrowser clients need explicit documented policy. Static header alone is not secret or sufficient; proxy origin handling must be correct |
| C. Explicit Django CSRF validation, bootstrapped CSRF cookie/token and exact origin checks | Standard token+origin defence, no new dependency; covers form/browser attacks | Adds bootstrap/client/header contract and rejection handling. DRF exemption must be explicitly addressed; login token rotation must be handled; refresh cookie stays HttpOnly |

Recommendation: **C** for the durable solution, with same-origin deployment retained.
B is a smaller interim option only if separately approved with strict missing/null-origin
policy and adversarial tests. A may add defence-in-depth later but should not replace
request validation. Keep the refresh cookie itself Lax until a separately reviewed change.

For C, use Django's normal CSRF secret/masking/origin validation rather than a naive
unsigned double-submit implementation. A readable CSRF cookie contains only the CSRF
secret, never JWT/refresh tokens. Obtain a token from an explicit same-origin bootstrap
response, attach X-CSRFToken to login/refresh (and other approved cookie-based mutations),
and validate before authentication side effects. Constrain trusted origins to the actual
reviewed UI origin(s), never wildcard/suffix string matching. Production requires HTTPS.
Local Vite needs an explicit reviewed origin/token bootstrap contract; don't silently
expand existing CORS settings. No third-party-site exception is proposed.

## Proposed interface and failure policy (requires approval)

- Proposed GET CSRF bootstrap with no-store response and no auth token in JSON; no
  DB change. Exact route is selected in the eventual auth implementation review.
- Login/refresh carry CSRF header and cookie. Invalid/missing CSRF/origin returns a
  stable 403 detail before token creation/blacklisting. Existing valid 200 and invalid
  refresh 401 behaviours remain. Never consume/rotate a refresh on rejected CSRF.
- Frontend must distinguish 403 from 401 and request a fresh CSRF token once only
  when appropriate; do not create mutation loops, silently clear unrelated sessions,
  or retry ambiguous sends. Review the existing silent-refresh catch/logout behaviour.
- Do not waive checks for missing Origin/User-Agent or a caller-provided proxy header.
  Any native/server client support needs a separately explicit auth contract.

## Test plan before implementation approval

Use disposable local test users/token material only; no production probes or raw token
logging. Unit/API tests must enforce real CSRF checks (ordinary DRF test clients bypass
some checks unless configured). Browser tests/manual smoke are also needed for SameSite.

1. Valid HTTPS same-origin bootstrap/login/refresh works; refresh rotates and old token
   replay is 401. Refresh token stays cookie-only and HttpOnly/Secure/Lax.
2. Missing/mismatched CSRF cookie/header, missing/null/untrusted Origin and malicious
   same-site different-port origin get 403 without rotating/blacklisting or minting tokens.
3. Exact trusted development origin succeeds only under approved development configuration;
   scheme, port, suffix-lookalike and unrelated domain mismatches fail.
4. Simulated malicious form/simple POST and custom-header preflight cannot change session
   state. CORS response policy remains unchanged unless a separate change is approved.
5. Expired/missing refresh remains 401 after CSRF request validation; valid CSRF is not
   authentication. Existing login/logout and public stale-Authorization exclusions work.
6. Check concurrent refresh requests, tab start-up and token-bootstrap expiry. Prevent
   repeated automatic refresh loops; throttled 429 is visible without retry storms.
7. Test external navigation/normal mobile usage before considering Strict cookies.
   XSS and nonbrowser forged headers are not solved by CSRF protection; don't claim they are.

## Manual rollout and rollback proposal — Michael only

Ship server/client contract together through reviewed build packaging; no migration.
Before any production activation, back up, verify proxy HTTPS/origin assumptions and
run local tests. No server changes are performed by this document. Stage rollout to a
controlled account and monitor only sanitized event categories/counts, no cookie values.

If legitimate refresh breaks, keep HTTPS and private media protections, preserve issued
refresh-cookie semantics, and revert to the prior reviewed server/client revision together.
Do not weaken CORS, disable Secure cookies, expose refresh in JSON or accept every Origin
as a hotfix. Reverting validation reopens the documented gap: record that risk and pause
new onboarding until an approved fix is ready. No schema reversal is needed. Never
invalidate/reset every account merely to roll back request validation.

References: [DRF CSRF/CORS](https://www.django-rest-framework.org/topics/ajax-csrf-cors/),
[Django CSRF protection](https://docs.djangoproject.com/en/6.1/ref/csrf/).

## WP18 local implementation — 16 October 2026

Option C is implemented locally for Phase A, not deployed. GET /api/accounts/csrf/
returns {csrfToken: masked Django token}, sets the CSRF cookie, and is no-store.
It ignores stale JWT headers and has THROTTLE_CSRF_RATE=60/min by default.
POST login/refresh/logout require exact Origin plus Django cookie/header checks;
rejection is 403 {detail: generic message, code: csrf_failed}. Validate before
credentials, blacklist or cookie side effects. Successful login rotates CSRF;
JWT access-only JSON, refresh cookie flags/lifetimes/rotation are unchanged.

DEBUG dev CSRF defaults list only the existing localhost/127.0.0.1:5173 UI origins;
explicit CSRF_TRUSTED_ORIGINS overrides them. CORS is unchanged. Production trusts
only its own origin plus exact explicitly configured CSRF origins, no wildcard match.
The ordinary Django test client's exemption remains; attack tests explicitly enforce
checks and cannot be taken as a reason to disable production CSRF.

Current sessions need no forced reset: upgraded frontend bootstraps before the next
cookie mutation. An old open tab may fail with CSRF 403 until reloaded; tell users
to reload, never clear every token/account. Failed post-login bootstrap does not
turn an issued login into failure; the next mutation fetches again. Parallel expired
requests share one refresh. Identified CSRF rejection gets one bootstrap/retry;
other mutations/403s never automatically retry. Refresh 401 alone retains existing
logout handling; 403/429/network failures preserve local access and surface errors.

No runtime bypass switch is added. Roll back the reviewed backend and packaged
frontend together via Michael's normal deployment flow. Rollback reopens the known
gap; do not weaken CORS/cookie security, erase DB data or rotate all sessions.
Manual review: new login; reload; expire access; confirm silent refresh; logout;
check missing/wrong token and hostile/null/missing Origin return 403 without rotating
refresh; existing sessions bootstrap successfully. Use synthetic local users only.

</details>
<details>
<summary>Read dated details — source variant 2</summary>

Source: `docs/REFRESH_COOKIE_CSRF_DESIGN.md`; input SHA-256 `94923297e326d6ed3c45a729e5fbc17946f21d20e8f403f6b637c7fa79a2121e`.

Earlier checkout differences; unchanged text is retained in the full record above.

```diff
--- consolidated full record
+++ earlier checkout version
@@ unchanged lines omitted @@
 # Refresh-cookie CSRF design — Checkpoint 3A WP15
 
+Design only. No mitigation below is implemented or approved for automatic deployment.
-Design only. Michael approved option C on 15 October 2026 in the Sprint 3 follow-up.
-This records design acceptance (AJ-13), not authorization to implement or deploy it.
-No mitigation below is implemented or approved for automatic deployment.
 JWT/refresh-cookie logic remains unchanged. Changes to auth, CORS or the interceptor
 need Michael's separate approval. Request throttling is not a CSRF mitigation.
@@ unchanged lines omitted @@
 References: [DRF CSRF/CORS](https://www.django-rest-framework.org/topics/ajax-csrf-cors/),
 [Django CSRF protection](https://docs.djangoproject.com/en/6.1/ref/csrf/).
-
-## WP18 local implementation — 16 October 2026
-
-Option C is implemented locally for Phase A, not deployed. GET /api/accounts/csrf/
-returns {csrfToken: masked Django token}, sets the CSRF cookie, and is no-store.
-It ignores stale JWT headers and has THROTTLE_CSRF_RATE=60/min by default.
-POST login/refresh/logout require exact Origin plus Django cookie/header checks;
-rejection is 403 {detail: generic message, code: csrf_failed}. Validate before
-credentials, blacklist or cookie side effects. Successful login rotates CSRF;
-JWT access-only JSON, refresh cookie flags/lifetimes/rotation are unchanged.
-
-DEBUG dev CSRF defaults list only the existing localhost/127.0.0.1:5173 UI origins;
-explicit CSRF_TRUSTED_ORIGINS overrides them. CORS is unchanged. Production trusts
-only its own origin plus exact explicitly configured CSRF origins, no wildcard match.
-The ordinary Django test client's exemption remains; attack tests explicitly enforce
-checks and cannot be taken as a reason to disable production CSRF.
-
-Current sessions need no forced reset: upgraded frontend bootstraps before the next
-cookie mutation. An old open tab may fail with CSRF 403 until reloaded; tell users
-to reload, never clear every token/account. Failed post-login bootstrap does not
-turn an issued login into failure; the next mutation fetches again. Parallel expired
-requests share one refresh. Identified CSRF rejection gets one bootstrap/retry;
-other mutations/403s never automatically retry. Refresh 401 alone retains existing
-logout handling; 403/429/network failures preserve local access and surface errors.
-
-No runtime bypass switch is added. Roll back the reviewed backend and packaged
-frontend together via Michael's normal deployment flow. Rollback reopens the known
-gap; do not weaken CORS/cookie security, erase DB data or rotate all sessions.
-Manual review: new login; reload; expire access; confirm silent refresh; logout;
-check missing/wrong token and hostile/null/missing Origin return 403 without rotating
-refresh; existing sessions bootstrap successfully. Use synthetic local users only.
```

</details>

<a id="record-roadmap-working-prompts"></a>

### roadmap working prompts

<details>
<summary>Read dated details</summary>

Source: `docs/ROADMAP_WORKING_PROMPTS.md`; input SHA-256 `702426f763a2cf8a4e34fccf648fc25b978f8bbedb74427583fc911c2a2817b1`.

# Ajiri roadmap: working prompts

15 October 2026. Michael's P0/P1/P2 tables are backlog input, not blanket approval
to install libraries, rewrite architecture or deploy. Use the prompts below only
when Michael invokes the relevant item. Keep acceptance focused and size each
package before building; do not force the whole roadmap into one checkpoint.

## Reconciled baseline

| Table item | Actual state / next action |
|---|---|
| Password validation, request throttling, content sniffing, deploy settings | Implemented locally in Checkpoint 3A, pending Michael's review and production verification; do not repeat them as missing |
| Refresh-cookie CSRF | Design complete, mitigation not implemented; protected auth approval needed |
| Throttling strength | Per-process approximate cache, live proxy hops unverified; request throttles do not require SMTP and are not daily mail quotas |
| Password reset / verification | Application features absent; already proposed in audit impact as WP17, not absent from planning |
| Real email | Console only; chosen direction is isolated dependency-free Brevo HTTPS, reachability pending; Gmail owner-only fallback |
| Privacy / rights / monitoring | Proposed, not implemented; legal wording DRAFT, manual verified rights at launch; backups automation not yet designed |
| Upload safety | Structural PDF/DOC/DOCX checks now exist locally; malware scanning remains a separate feasibility decision |
| API / tests / frontend tooling | Existing pagination/filtering, component tests, axios hook and oxlint; no schema, browser E2E or coverage/a11y gate established |
| Build / deployment | Committed frontend_build and exact CI comparison remain required; change only through an approved deployment design |
| Job deduplication | Unique source URL already prevents exact-source duplicates; cross-source/fuzzy deduplication is a separate product improvement |

Checkpoint 3A numbering superseded earlier proposal WP11-WP15. Use the prompt IDs
below until Michael assigns future work-package numbers; never mix the two sets.
See [3A review](HISTORY.md#record-checkpoint3a-review), [audit](HISTORY.md#record-modernisation-audit),
[decision form](HISTORY.md#record-decisions-needed) and [SMTP design](HISTORY.md#record-smtp-email-design).

## Common instruction block for every build prompt

Read AGENTS.md and the named design/review first. Confirm Michael's exact scope and
the reviewed base revision; do not assume local 3A is merged/deployed. Use one branch
per bounded package and stop conditions/quality gates from AGENTS. Preserve the
existing auth client, JSX and Python matrix. No secrets, production operations,
destructive data changes, migration-history changes, paid service, new dependency,
CI/hosting change, push or PR merge unless separately authorized for that action.
Design-required migrations need Michael's exact schema approval before implementation.
Report actual tests, limitations, manual review steps and suggested story points.
For a frontend package, package frontend_build once as its final commit unless its
replacement policy has been separately reviewed and approved.

## P0-A: finish the security release gate

**Working prompt:** Review Checkpoint 3A instead of rebuilding it. Reproduce its
password/upload/throttle regressions and deploy-profile checks locally. Separate
code that passed from production verification still pending. Design a practical
shared-counter strategy for the confirmed PythonAnywhere topology and a correct
trusted-proxy configuration; do not guess NUM_PROXIES or call LocMemCache a hard
distributed limit. Obtain separate authorization before implementing the chosen
refresh-CSRF option or changing silent-refresh 429 recovery. Preserve rotation,
blacklisting, cookie-only refresh tokens, CORS and ingestion behaviour. Show tests
for cross-origin rejection, legitimate browser flows and no redirect loops.

**Done when:** Michael has a reviewable security release checklist, tested fixes
within the approved scope and explicit open release gates. HSTS stays short with
subdomain/preload off; intentional W005/W021 advisories are documented, not hidden.
Production verification remains Michael-only. No repeated live load/brute-force tests.

## P0-B: delivery and account recovery

**Working prompt:** Implement real email only after provider reachability and
sender decisions are confirmed. Keep Brevo HTTPS in one isolated module using
existing/standard-library capabilities; Gmail is an owner-only pilot fallback.
Use verified platform From and applicant Reply-To. Enforce 10 accepted applications
per user/day and Michael's confirmed global budget below provider limits, prioritizing
applications over alerts. Define copy/attachment budgets, bounces, complaints,
suppression and minimal attempt metadata before schema approval. Retain 502 and
reviewable retry for definite failures; never auto-retry ambiguous acceptance, and
show a duplicate-delivery warning before a manual retry. Keep mail switchable off.

Then implement anti-enumerating password-reset and email-verification flows as a
separate package. Confirm what unverified/existing accounts may do, expiry/resend
rules and password-change session revocation before coding. Use Django validators
and token primitives; preserve auth boundaries unless explicitly approved. Mock
transport/use in-memory mail in tests and CI. No real provider calls from CI.

**Done when:** acceptance/failure/quota/concurrency tests pass; reset links expire
and cannot replay, invalid requests reveal no account existence, unverified identity
cannot be used for employer mail under the approved policy. Rollout starts with
synthetic documents to Michael's controlled inbox, performed manually by Michael.
Domain, global cap, provider reachability and remaining form choices stay unresolved
until supplied; placeholders are never configuration values.

## P0-C: privacy and usable rights at launch

**Working prompt:** Keep all legal text DRAFT pending the named reviewer's approval.
Propose a public privacy notice with controller contact, purposes/lawful bases,
processor/cross-border disclosures, retention and rights. Separate versioned notice
acknowledgement from optional email choice; alerts default off for new users and
existing users confirm in-app before any alert email. Record server timestamps and
consent versions without inventing historical consent or collecting unnecessary IPs.

Provide manual identity-verified export/deletion fulfilment for launch, with a
dry-run-first deletion command design and separate destructive-action approval.
Inventory owned DB rows, private media, auth sessions, pending sends, shared records
to retain, provider copies and backups. Define partial-failure/retry and a restore
procedure that does not resurrect deleted accounts. Self-service is deferred.

**Done when:** legal owner/contact and retention are confirmed, notice/choice UI and
owner-isolation tests pass, export excludes hashes/tokens, and deletion is rehearsed
only against explicitly disposable local data. Seven-day export expiry and 30-day
rolling backups are starting proposals, not final legal commitments.

## P0-D: operational visibility and recoverability

**Working prompt:** Design dependency-free sanitized error logging, a minimal
GET/HEAD health endpoint and visible ingestion/sweep failure ownership. Health must
not reveal versions, paths, secrets or private records, and does not prove mail or
feed freshness. Cover failure status and redaction tests; stop logging CV-bearing
content as if console delivery were safe production delivery.

Separately design automated private DB/media backups that fit the actual free-tier
CPU/disk/scheduler limits. Compare manual minimum plus verified restore against
approved automation; define consistent SQLite backups, encryption/access control,
off-host custody, retention, deletion replay and failure alerts. No server access,
credentials, GitHub secrets, scheduling workflow or production copy is authorized
by this prompt alone. Do not assume free-tier scheduled tasks are available.

**Done when:** a human can identify failed ingestion and stale data, perform the
documented recovery rehearsal, and renew the app before expiry. Automation is not
declared complete until its supported schedule, restore and failure path are proven.

## P0-E: repository controls (current authorized action)

For michael-mathenge/ajiri, require PRs, current-branch CI, frontend and backend
3.12/3.13/3.14 checks from GitHub Actions, resolved discussions, no force pushes or
branch deletion, and admin enforcement. Michael selected **zero approvals until
an independent reviewer is added**; don't impose an impossible self-review rule.

Protection, dependency graph, Dependabot alerts and security-update PRs were saved
and verified on 15 October 2026. Secret scanning/push protection were already enabled
and were preserved. [Dependabot version configuration PR #6](https://github.com/michael-mathenge/ajiri/pull/6)
contains only weekly npm/pip/Actions update proposals (Monday 09:00 Nairobi), limited
to three version PRs per ecosystem with minor/patch grouping. It has not been merged;
scheduled version updates activate after Michael merges the configuration to main.
No auto-merge is enabled. An already-installed YAML parser validated the configuration
and its Git blob hash matched the committed file. No dependency version was upgraded.

An owner-scoped connector has Michael's authority: these rules cannot distinguish
his manual merge from an API merge after checks pass. Human-only merge separation
needs a separately permissioned integration and/or independent reviewer, not a claim
that branch protection makes all agent merges technically impossible.

## P1-A: browser quality and supply-chain gates

**Working prompt:** Start from risk-based E2E scenarios: registration, sign-in/refresh,
profile upload, prepare/review/send/failure/dismiss and keyboard/mobile navigation.
Propose Playwright, axe, coverage and Lighthouse budgets with dependency/CI changes
itemized for approval first. Mock external mail; synthetic data must never reach an
employer. Establish baseline bundle/network/accessibility measurements before budgets.

Review existing oxlint, tests and Python stubs before proposing ruff, formatter,
eslint replacement, pre-commit and mypy/pyright. Keep JSX; no TypeScript migration.
Plan pip-audit/npm audit and focused patch review alongside Dependabot. Preserve
required check names or coordinate branch protection before renaming CI jobs. Free
secret scanning is already on; never print real findings containing credentials.

**Done when:** approved reproducible gates catch meaningful regressions without flaky
live services or silently skipped security tests. Coverage has measured evidence;
hooks remain convenience, CI is authoritative. No tool installation is implied here.

## P1-B: frontend data/forms and API contract

**Working prompt:** Measure duplicate fetches, stale state, retry needs and form
inconsistency before replacing the existing hook. Compare a small in-place fix with
TanStack Query; compare existing forms with React Hook Form/Zod. Obtain explicit
dependency approval, migrate one vertical slice at a time, preserve all field errors
and auth-client behaviour. Never retry send/apply automatically or persist private
documents/tokens in a cache. Account for mobile data cost and cache invalidation.

In a separate package, propose OpenAPI via drf-spectacular versus a docs-first contract,
with schema/security/error/pagination examples and compatibility tests. Decide whether
versioning solves an actual breaking change before introducing /api/v1; keep existing
/api consumers functional. Approval is needed before dependency or routing changes.

**Done when:** the approved slice demonstrates fewer duplicate requests, correct
loading/error/invalidation behaviour and accessible consistent form errors; contract
tests agree with server and client without gratuitous rewrites.

## P1-C: build, staging and repeatable deployment

**Working prompt:** Design a replacement for committed frontend_build before removing
it or its exact CI guard. Compare CI-produced immutable artifacts with deployment-time
builds under PythonAnywhere free-tier limits. Define revision/artifact linkage,
checksums, custody, download/authentication, release activation and rollback. Ensure
Dependabot frontend PRs can obtain a reviewed matching build until the policy changes.

Propose a staging environment and narrowly scripted deployment, with private media,
no real mail/production data, explicit server operations owned by Michael, and backup
-> migrate -> activate ordering. Audit existing .env.example before adding one;
templates list names/placeholders only. Devcontainer/setup additions need dependency
and platform support review rather than an assumed Docker requirement.

**Done when:** a disposable environment can build/recover the same revision and a
reviewed deployment design preserves data/security. No CI, hosting, generated-artifact
policy or production action is authorized until the replacement is approved.

## P2: discovery, scale and product experiments

Treat each row as its own discovery/design prompt, not a combined build request.

| Prompt | Required outcome before implementation |
|---|---|
| Public jobs / SEO | Decide public versus authenticated boundaries; verify source rights and job freshness; propose JobPosting structured data, canonical pages/sitemap and prerendering/SSR without exposing applicant data |
| Search quality | Measure current filters/results; assess SQLite FTS availability/tokenization/ranking and additive indexing/migration options before promising it; preserve existing queries and evaluate representative Kenyan jobs |
| Scale | Measure N+1/query counts, ingestion/matching budgets and SQLite contention first; compare Postgres, private S3/R2 and background work with real host/cost limits, migration/rollback and signed owner downloads |
| English / Swahili | Confirm audience/translation owner and terminology; design locale, fallback, dates/currency, mobile layout and tests; don't auto-publish legal translations |
| Payments / subscriptions | Validate Free/Starter/Pro demand; design M-Pesa entitlements, authenticated webhooks, idempotency, reconciliation/refunds and sandbox tests; no live payments or provider credentials |
| Application pipeline | Decide statuses and external-employer semantics; preserve saved-document/review history and explicit regeneration; design before any status migration |
| Saved searches / alerts | Define saved criteria, frequency, consent, quiet hours and sending budgets; keep application and alert quotas distinct |
| Moderation / deduplication | Define reviewer tools, flagged-job appeal/audit handling and cross-source duplicate criteria; preserve exact source-URL uniqueness and avoid destructive merge/delete automation |
| PWA / offline | Measure poor-network journeys first; propose installable public shell/retry UX with cache versioning/logout cleanup; never cache private CVs, tokens or authenticated API responses by default |
| Analytics | Define the questions/metrics first; compare no analytics, server aggregates, Plausible/Umami under actual hosting/cost constraints; consent wording, retention and third-party processing require legal review |

## Suggested sequence and handback

1. Review Checkpoint 3A and verify the repository controls; keep production gates open
   until Michael performs the proxy/cache/header checks. Do not infer deployment.
2. Launch readiness: CSRF follow-up, controlled mail, account recovery/verification,
   legal-reviewed privacy/rights and operational recovery; separate bounded packages.
3. Professional baseline: E2E/a11y/supply-chain gates, then measured frontend/API
   changes and an approved build/deploy replacement. No dependency shopping spree.
4. Product-led experiments: choose SEO, language, search, payments or analytics based
   on evidence; move infrastructure only when current limits or reliability justify it.

For each invoked prompt, hand back scope/branch, actual test results, risks/limits,
manual verification and story-point suggestion. Ask only decisions that block that
package. Existing open placeholders remain in DECISIONS_NEEDED.md; this roadmap does
not manufacture answers, legal approval, migration approval or access credentials.

</details>

<a id="record-smtp-email-design"></a>

### smtp email design

<details>
<summary>Read dated details — source variant 1</summary>

Source: `docs/SMTP_EMAIL_DESIGN.md`; input SHA-256 `a76775f6335e48339174f034c32797c6700a31b6f764f192c95e1cebd824c1a5`.

# SMTP and transactional email design — WP11

Historical 15 October proposal. Its "current behaviour", provider-selection and
approval paragraphs describe that date and are superseded by the reviewed Brevo
HTTPS/shared-ledger implementation. Owner inbox pilots are complete; broader
normal-path acceptance remains open. Use sending design (historical path: `APPLICATION_ALERT_SENDING_DESIGN.md`),
activation checklist (historical path: `BACKEND_ACTIVATION_CHECKLIST.md`) and next actions (historical path: `ROADMAP_NEXT_ACTIONS.md`).
Do not restore the legacy console/SMTP path described below.

Proposal only, 15 October 2026. No provider selected or account configured.
Michael performs every server/provider/DNS operation. Codex never touches production
or requests, receives or writes credentials. Names below are configuration names,
not secret values. Privacy/provider processing sections are DRAFT for legal review;
Codex is not a lawyer. See [Checkpoint 3 decisions](HISTORY.md#record-checkpoint3-plan).

## Current behaviour and acceptance boundary

`config/settings.py` reads EMAIL_BACKEND and existing SMTP fields from environment;
it defaults to Django console. Production therefore reports application sends as
successful without delivering real email. Console output can include message bodies
and attachment content; treat logs as sensitive and restrict access.

`jobs/views.py` atomically claims ready_for_review as sent before sending saved CV
and letter attachments. Definite delivery/attachment failure returns 502 and releases
that claim to ready_for_review with no sent_at, retaining documents for retry. Preserve
400 for already claimed/invalid state, owner checks and external-link confirmation.

`jobs/matching.py` currently uses fail_silently=True, then sets sent_email=True without
checking accepted count. Existing notification uniqueness also prevents a fresh retry
on the next sweep. Correct this prospectively: accepted means provider/backend accepted
one message, not inbox delivery. Never relabel old records as delivered or resend them
in bulk. Keep in-app alerts independent and ingestion successful on mail failure.

## Provider options and verification

Sources checked during planning on 15 October 2026, not through production probes.
Prices/limits and account policies must be rechecked by Michael before activation.

| Option | Free-tier evidence / feasibility | Trade-off |
|---|---|---|
| Gmail SMTP with app password | Google documents app passwords for eligible two-step-verification accounts. PythonAnywhere's official help search result describes a Gmail exception, but canonical SMTP help could not be fetched; current account connectivity is NOT fully verified | Uses Django built-in SMTP, no dependency; account-specific limits, abuse restrictions and shared consumer identity make it a small-pilot option |
| Brevo HTTPS transactional API (recommended) | api.brevo.com is on the current US PythonAnywhere allowlist; Brevo documents a free 300 sends/day plan and attachment/Reply-To support | Requires a provider transport adapter or approved dependency, account/sender approval and privacy review; allowlisting is not an end-to-end connectivity test |
| Brevo SMTP relay | SMTP exists, and relay hostname appears on the allowlist, but an HTTP(S) proxy allowlist does NOT prove outbound SMTP-port access | Do not choose this path on the free tier without explicit current platform confirmation |

References:
- [PythonAnywhere free accounts](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/)
- [Current US allowlist](https://www.pythonanywhere.com/whitelist/)
- [Canonical SMTP help — retrieval failed](https://help.pythonanywhere.com/pages/SMTPForFreeUsers/)
- [Official help development mirror — indexed historical guidance, not current proof](https://helpdev.pythonanywhere.com/pages/SMTPForFreeUsers)
- [Google app-password requirements](https://support.google.com/accounts/answer/185833)
- [Brevo free-plan limits](https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan)
- [Brevo transactional API](https://developers.brevo.com/reference/send-transac-email)

Recommendation: Brevo over HTTPS, conditional on Michael approving API delivery instead
of literal SMTP. Keep Django's EmailMessage interface and supply a small backend adapter
using Python's standard library (including environment proxy support), with all transport
calls mocked in tests. No dependency is approved by this proposal. If an SDK/Anymail would
be safer or materially simpler, explain its benefit and stop for dependency approval.
Send attachments as encoded bytes, never as public CV URLs. Provider limits, payload
sizes and processing terms must be checked against saved document sizes before selection.
Do not disable TLS verification or bypass PythonAnywhere network restrictions.

## Sender and user trust

Recommend a verified platform From address, branded as Ajiri, with request.user.email
as Reply-To on applications. Employer sees the platform sender and can reply to the
applicant. Clearly explain the relationship in the review UI; never suggest the
message originates from the user's mailbox. Alerts use the platform sender and a
platform-controlled reply/support address, not the recipient as Reply-To.

Alternatives: arbitrary applicant From risks SPF/DKIM/DMARC mismatch and spoofing;
per-user OAuth/mailbox delegation adds credentials, permissions and complexity outside
this checkpoint; mailto/manual external sending reduces automation and cannot confirm
delivery. Recommend neither arbitrary From nor per-user credentials for this release.
Michael verifies the sender/domain and provider-required DNS authentication, including
DKIM/SPF and DMARC alignment. Gmail may rewrite unauthorized From identities. Do not
claim domain control or promise deliverability before sender verification.

## Configuration contract (names only)

Existing: EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER,
EMAIL_HOST_PASSWORD, EMAIL_USE_TLS, DEFAULT_FROM_EMAIL.

Proposed: EMAIL_TIMEOUT, EMAIL_USE_SSL (only if required by selected SMTP transport),
BREVO_API_KEY, EMAIL_PLATFORM_REPLY_TO, EMAIL_PLATFORM_DAILY_LIMIT,
EMAIL_USER_DAILY_LIMIT, EMAIL_APPLICATION_DAILY_RESERVE,
EMAIL_USER_HOURLY_LIMIT, EMAIL_ALERT_MAX_ATTEMPTS, EMAIL_ALERT_RETRY_DELAY_SECONDS,
EMAIL_DELIVERY_ENABLED (operator control to stop email actions during outage/rollback).
Exact defaults/limits require Michael's decision; credentials have no committed defaults.
Only selected-provider variables are required. TLS and SSL modes are mutually exclusive.

Read configuration from environment; the existing private server loader may load the
private environment file that Michael maintains. No credentials in Django DB, frontend,
source, sample commands, screenshots, chat or commits. Codex lists names only. Missing
configuration for an explicitly selected real backend must produce a sanitized startup
check error. Do not silently downgrade production SMTP/API failures to console.
Local default remains console; tests override to Django in-memory backend and do not
inherit production delivery credentials. Timeout is finite and must fit the worker budget.

## Failure handling, retries and limits

- Require accepted count of one for application success; zero is failure too. Preserve
  502/reviewable retry for definite failure and unchanged external-link behaviour.
  No transaction is held over network delivery; preserve the conditional claim.
- A provider can accept then lose its acknowledgement. Do not automatically retry an
  ambiguous attempt. Record a sanitized uncertain outcome for manual reconciliation;
  no new application status value is proposed. If a stronger state machine is needed,
  stop for separate approval. Sent in the current UI is not proof of inbox delivery.
- Alerts record sent_email only on confirmed acceptance; definite failures retain
  independent in-app visibility. Add attempt/budget records so a bounded retry can
  happen through the existing matching service invocation, without rewriting ingestion
  endpoints, changing workflow schedules or creating a daemon/Celery dependency.
  Any ingestion-flow change beyond that boundary requires explicit approval.
- Recommend additive SQLite-backed delivery reservations shared by both channels and
  workers, not per-process caches or DRF's approximate throttle as a hard global cap.
  Atomically reserve platform/user budgets before delivery and release only definitely
  unaccepted attempts. Keep uncertain reservations consumed for safety; no automatic
  crash reset. Do not hold SQLite locks across network calls.
- Define daily windows in Africa/Nairobi and a user rolling-hour control; provider
  windows may differ, so use conservative application caps beneath provider quotas.
  Count accepted plus unresolved reservations. Reserve a configurable portion for
  applications so alert fan-out cannot consume everything. Exact caps are decision 3.
- Local quota rejection proposes 429 with a safe retry hint and no state change; it
  is separate from provider failure (502). Provider quota rejection must not be
  mistaken for successful delivery. Alerts over quota stay pending only until bounded
  attempts/expiry, never unlimited catch-up bursts. Exact expiry belongs in approval.

Migration proposal: new delivery-attempt and budget tables with constraints supporting
atomic reservations; no destructive data migration, AUTH_USER_MODEL change or historical
consent/delivery backfill. Present exact schema and mixed-version deployment behaviour
before coding. All writers must be paused for cutover because old code bypasses quotas.

## Test plan — no live email in tests or CI

Use Django's in-memory backend for end-to-end message composition and current concurrency
suite. Assert platform From, applicant Reply-To, recipients, saved attachment bytes,
preferences and no duplicate sends. Mock transport for rejected auth, zero accepted,
timeouts, provider quota response and ambiguous acknowledgement. Assert 502 resets only
the winning claim, 400 remains for invalid sends, and retry after definite failure works.

Exercise atomic caps with overlapping reservations, day rollover, hourly limits,
application reserve and alert fan-out. Check alert failure never creates false success
or breaks ingestion, bounded retry does not duplicate confirmed acceptance, and in-app
visibility stays independent. Assert errors/logs contain no credential, address, payload
or attachment content. Future implementation runs all AGENTS quality gates; this planning
round does not claim those tests have been run.

## Manual activation instructions — Michael only, after separate approval

These are instructions, not actions taken by Codex. Existing deployment checklist remains
required; no production operation is authorized by approving a design document alone.

1. Select the approved provider, review processing/retention and verify the platform
   sender/domain in its dashboard. For Gmail, enable two-step verification and confirm
   app-password eligibility; create credentials privately. Never paste them into chat.
   For Brevo, verify transactional sending approval and attachment limits. Confirm current
   PythonAnywhere restrictions with platform documentation/support if SMTP is chosen.
2. Choose a quiet window; record old revision and backend privately. Pause all writers,
   ingestion/sweep callers and sending. Back up SQLite with its backup API and verify
   integrity, plus private media and private server configuration, following
   [deployment checklist](../docs/DEPLOYMENT_CHECKLIST.md). Stop if restore rehearsal fails.
3. Stage the reviewed revision containing migration tools without activating new code.
   Review check/migrate plan in the Python 3.12 environment. Stop on unexpected/destructive
   operations; apply approved additive migrations before web reload:

   ```bash
   cd /home/Mathenge/ajiri/ajiri-backend
   workon ajiri
   python manage.py check
   python manage.py migrate --plan
   python manage.py migrate --noinput
   ```

   Expected: no system-check errors and only approved migrations applied. The exact
   approved revision and schema will be documented when implementation is reviewed.
4. In the private server configuration editor, enter only the selected backend's
   variables yourself. Keep environment file permissions owner-only. Do not put secret
   values in shell command history, public files or Git. Confirm required names are
   present through sanitized checks, never printing the environment. For HTTPS delivery,
   retain the platform proxy; for SMTP use the provider's documented TLS mode/port.
5. Activate/reload reviewed code only after migration and configuration checks pass.
   Leave private media mappings unchanged; no public download URLs are needed. Keep
   writers paused until health, login and owner download checks pass.
6. Send a synthetic application only to an inbox you control, then a synthetic alert.
   Confirm actual arrival, From/Reply-To, correct saved attachments and provider receipt.
   Never send a deployment test to a real employer. Exercise failure/double-send paths
   in local captured-mail tests, not by corrupting production credentials.
7. Inspect sanitized server/provider events privately, caps and acceptance counts.
   Resume callers only after checks pass; verify one ingestion/sweep run stays healthy.
   Recheck renewal/quota and provider rejection/bounce evidence in the manual routine.

## Rollback and risks

On failed validation, keep writers paused. Michael restores the prior backend selection
privately and reloads the reviewed compatible revision. If returning to console, **real
email stops**, and console output can contain sensitive content. Pause email application
sending and alert dispatch until the failure is resolved; do not tell users console
success means delivery. If no existing way safely disables these actions, keep traffic
paused rather than silently accepting sends. Designing an operator delivery-disable
control is a prerequisite of WP11 implementation, not a change made in this document.

Keep additive tables in place; do not reverse migrations or restore an older DB over
new writes. Preserve delivery-attempt evidence and reconcile accepted/uncertain sends
before any retry. Never bulk reset sent applications. A compromised credential is
revoked/rotated by Michael through the provider, never shared with Codex. Rollback
cannot recall mail already accepted or copies held by employers/providers.

</details>
<details>
<summary>Read dated details — source variant 2</summary>

Source: `docs/SMTP_EMAIL_DESIGN.md`; input SHA-256 `08f4c49a62797bf7f48ad333cb1a2f7538f0e1867b74fe62ffee9c16e941747c`.

Earlier checkout differences; unchanged text is retained in the full record above.

```diff
--- consolidated full record
+++ earlier checkout version
@@ unchanged lines omitted @@
 # SMTP and transactional email design — WP11
 
-Historical 15 October proposal. Its "current behaviour", provider-selection and
-approval paragraphs describe that date and are superseded by the reviewed Brevo
-HTTPS/shared-ledger implementation. Owner inbox pilots are complete; broader
-normal-path acceptance remains open. Use sending design (historical path: `APPLICATION_ALERT_SENDING_DESIGN.md`),
-activation checklist (historical path: `BACKEND_ACTIVATION_CHECKLIST.md`) and next actions (historical path: `ROADMAP_NEXT_ACTIONS.md`).
-Do not restore the legacy console/SMTP path described below.
-
 Proposal only, 15 October 2026. No provider selected or account configured.
 Michael performs every server/provider/DNS operation. Codex never touches production
```

</details>

<a id="record-checkpoint3b-schema-review"></a>

### checkpoint3b schema review

<details>
<summary>Read dated details</summary>

Source: `docs/CHECKPOINT3B_SCHEMA_REVIEW.md`; input SHA-256 `bc87f7249171da4ed620d38e39b23b11ec9e2e073ec25cb5c2aa7aa6d855b3ee`.

# Checkpoint 3B Phase B preparation — schema package review


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026. Branch feature/verification-delivery-schema, based on deployed,
merged Phase A e4eaefd21f839281d306d6f68cf4fc7c0218cd85. Michael explicitly approved
implementing this additive schema package with tests and stopping afterwards.
The previous AGENTS design-only migration rule is superseded only for this package.
No push, deployment, email delivery, provider/DNS write or further Phase B work.

## Package / scope / suggested points

| Package | Branch | Suggested points |
|---|---|---:|
| Verification and delivery accounting schema | feature/verification-delivery-schema | 5 |

Profile proof columns, new ledger/budget tables, schema constraints, migration and
API-isolation tests, concepts, and this review. No new WP number was invented.
The design decision commit was cherry-picked locally from integration/checkpoint-3b
onto the merged release; original dirty checkout, coverage, stash and config remain.

## Exact new migrations and existing-data impact

- profiles/0003_profile_email_verified_at_profile_verified_email adds nullable
  email_verified_at (None) and blank verified_email ('', max length 254). All
  existing profiles remain unverified. No proof, consent or preferences backfill.
- jobs/0008_deliverydailybudget_deliveryattempt depends on jobs/0007 and the
  existing swappable user dependency. It creates two initially empty tables;
  it does not change the User model, old migrations, application status choices,
  notification receipts, passwords or private files.

DeliveryAttempt contains UUID identity/idempotency, nullable SET_NULL owner/document/
notification links, four channels, four outcome states, keyed recipient digest,
provider reference, bounded category and timestamps. No email address, body,
attachment, token or credential is added. Digest remains personal data for privacy
purposes. There is no sender populating this table yet.

DeliveryDailyBudget stores an explicit day, scope global/user:<id>, and independent
nonnegative application, alert and account counters. Account counter combines
verification/reset. No rows or past sending counts are inferred from console mail.

## Enforced guarantees versus future service responsibilities

Database checks enforce known channel/state/failure categories, channel/link shape,
nonnegative counters, unique idempotency keys, unique (scope,day), and at most one
reserved/unknown attempt for each linked application or notification. Partial
uniqueness remains authoritative if callers bypass model validation.

Creation ownership, required source links, digest format and scope format are
model-validation rules: future services MUST call full_clean (or equivalent explicit
validation) before reserving. Django save()/bulk_create()/update() do not automatically
call full_clean. The database permits null links so SET_NULL erasure works. It cannot
distinguish an erased historical link from a deliberately missing link at insertion.
No false claim of cross-table ownership enforced by SQLite CHECK constraints.

Verification/reset channels forbid document links. Account-message throttles,
deduplication/replay policy and any future account-purpose partial unique constraint
remain service design work; this package does not arbitrarily serialize all account
messages or generate a token table. Receipt state transitions also remain service
work; accepted means provider acceptance, never inbox delivery.

The approved 10/user and 200/platform daily policy (150/30/20 categories) is NOT yet
enforced. Future services need atomic conditional reservations/attempt creation in
short transactions, Nairobi day calculation, no network I/O under SQLite locks,
quota UX, unknown reconciliation and bounded retries. The definite-failure capacity
accounting clarification still needs confirmation. No numeric cap is hardcoded into
schema, keeping approved runtime configuration possible without another migration.

## Verification

Actual local outcomes (Python 3.12.6 / Node 24.19): pip check, Django check,
migration-drift check all passed. Focused schema suite: 9 passed. Full backend:
120 run, 119 passed and one Windows symlink-privilege skip (85.674 seconds).
Locked npm ci, lint, 32 component tests and Vite build passed. No frontend_build
regeneration. The skip requires Linux CI after a future authorized push; no CI or
production tests were triggered by this package. Focused schema tests cover:

- Existing/new profiles start unverified; public Profile serializer cannot write proof.
- Account categories create without document links; no token/payload fields.
- Invalid ownership/missing links/digest validation; database enum/link checks.
- Unique idempotency and unresolved application/notification attempts.
- Separate retry record after definite failure; no actual sending invoked.
- User/document erasure retains null-linked receipt.
- Budget nonnegative checks, duplicate date/scope, separate days/user scope.
- Migration from representative old user/profile/job/application/notification rows,
  preserving hashes, snapshots/preferences/receipts, no ledger/budget backfill, and
  historical model reads against additive schema (normal code rollback strategy).

Tests use only disposable synthetic local databases. MigrationExecutor briefly moves
the TEST database to historical schema; this is not a production reversal. This is
not a quota-service concurrency or token-expiry test: those services do not exist.
No new dependency, frontend source or committed-build changes. Verification builds
only; the packaged frontend must still match dist byte-for-byte.

## Manual local review / reproduction (PowerShell)

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test jobs.test_delivery_schema --noinput
.\.venv\Scripts\python.exe manage.py test --noinput
```

Only these tests apply the migrations locally in this package; no existing local
development database migration was performed. Do not point test settings at a live
database. Production mail settings remain untouched and console-only.

## Future owner deployment and rollback — instructions only

After separate review/push/CI/merge/deployment authorization: record exact release,
pause writers, back up DB/private media and verify recovery, stage migration source,
review migrate --plan for ONLY profiles/0003 and jobs/0008 (plus already-reviewed
history), apply before activating model code, then reload and verify. Stop on an
unexpected migration. Keep redirect=False/HSTS=0 pending the independent host gate.

New model code must not serve before new columns exist. Old code reads the expanded
schema; new ledger tables are unused by old code. Roll back reviewed code WITHOUT
reversing additive schema or replacing newer data. Dropping populated tables or
verification fields loses evidence and requires separate destructive-change approval.
Schema migrations are mechanically reversible but that is not routine rollback.

## Domain inspection and remaining decisions

Read-only Namecheap UI inspection confirmed michaelmathenge.dev ACTIVE through
19 August 2027 with Namecheap BasicDNS in Michael's signed-in account. It is a viable
domain for later sending authentication. This does not prove Brevo authentication,
mailbox existence, DNS propagation or actual deliverability. No domain/private
contact data was copied into source, and no DNS, MX, website or provider settings
changed. Website remains mathenge.pythonanywhere.com. DNS authentication and exact
sender mailbox/reply handling need a separate setup step and authorization.

Still gated: actual transport, reset/verification endpoints, quotas and retries,
account-email throttle defaults, uncertain receipt retention, legal review,
bounce/complaint handling and owner-only pilot approval. No automatic cleanup.
Queued UI fixes remain untouched. Stop after this package for Michael's review.

Reference for database constraints/model validation separation:
[Django constraints documentation](https://docs.djangoproject.com/en/dev/ref/models/constraints/).

</details>

<a id="record-checkpoint3b-phase-a-review"></a>

### checkpoint3b phase a review

<details>
<summary>Read dated details</summary>

Source: `docs/CHECKPOINT3B_PHASE_A_REVIEW.md`; input SHA-256 `f3a959bb64e926826476b389732a8cf933fe4a39672fb98f69172771d6901ca2`.

# Checkpoint 3B Phase A review


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026, Africa/Nairobi. Local implementation only, based on exact reviewed
main `c4b93647f65618e8d13f9baa47ded6d22a28f0fb`. Remote main was rechecked at handback
and still resolves to that SHA. No rebasing or changes to Michael's deployment SHA.
Michael confirmed Stage A deployed/reloaded on 16 October at c4b9364: redirect=False,
HSTS=0, shared cache writing counters, weak-password rejection, login, jobs list,
profile save and no public media mapping verified by him. This is owner-reported
evidence, not an agent inspection. Stage B awaits PythonAnywhere's HTTPS scheme
answer; keep redirect/HSTS off. The Phase A branch was already completed locally
before this confirmation; its base was not changed.

## 1. Package summary

| WP | Local status | Branch | Source range | Suggested points |
|---|---|---|---|---:|
| WP16 | gates passed; existing safe pins retained | feature/dependency-advisories | f96ec68..bf9547a | 3 |
| WP18 | gates passed; paired client/server change | feature/refresh-cookie-csrf | 4db333e..1e4197a | 8 |
| WP21 | gates passed; production configuration pending | feature/health-and-logging | 021f81f..3791833 | 5 |
| WP22 | gates passed; manual operation documented | feature/backup-routine | af8f62f..e969690 | 5 |

Each package merged into integration/checkpoint-3b with --no-ff after its gates.
WP22 also includes focused WP21 follow-up 391cf94: private permissions after log
rollover and sanitized fallback on logging I/O failures. Final full gates cover it.
First commit f96ec68 changed only AGENTS time-bound sections. Final handback is docs
only. Points total 21, relative sizing rather than a promise about elapsed time.
WP17/WP19/WP20 were not invented: only the four Phase A packages were authorized.

## 2. Changes

WP16 captures production and development pip-audit results and reconciles all 15
historical advisories, original versions, current fixes and applicability. Current
pins already include Django 6.1.2/PyJWT 2.15.1. No dependency files changed.
Historical clean claims without reproducible evidence remain unverified; advisory
matching does not establish exploitability. Primary advisory discrepancies and the
finding without a published fixed event are explicitly recorded.

WP18 adds GET /api/accounts/csrf/ with a masked Django token and no-store response.
Login, refresh and logout require a valid Django token and exact trusted Origin
before side effects. Stable csrf_failed JSON 403 responses enable one bounded
bootstrap/retry. Existing axios client bootstraps, renews after login, and shares
simultaneous silent refreshes. Refresh 401 still invalidates a session; CSRF 403,
429 and network failure do not erase an otherwise valid session. JWT lifetimes,
rotation/blacklisting and HttpOnly refresh-token storage remain unchanged.
Existing sessions bootstrap normally; old tabs may need a reload. No runtime
CSRF-disable switch. The committed frontend_build was regenerated once, as WP18's
last package commit; later builds were verification only.

WP21 adds unauthenticated GET/HEAD /api/health/ using SELECT 1, generic ok/unavailable
JSON, empty HEAD body and non-cacheable responses. Resolved-IP throttle defaults to
60/minute using the existing throttle cache. Sanitized JSON errors contain only
timestamp, severity, category, generated correlation ID, status and route name.
Private per-process files rotate at 1 MiB with three retained rotations by default.
Failure fallback also excludes original exception/message contents. Stale process
files need manual quota review. Console email remains unchanged and can still put
mail content into platform console logs; these are separate from sanitized files.

WP22 adds backup_private_data: required private destination, dry-run, SQLite backup
API, integrity checks, unique private directories, optional media, checksums and a
completion manifest published only after success. Media requires a declared paused
writer window and inventory consistency check. Unsafe paths/links and credential
files are rejected. Thirty-day retention is DRAFT and report-only: no automatic
deletion or pruning flag. Interrupted copies remain private/incomplete. The runbook
covers manual free-tier operation, conditional scheduling and isolated restore.

MIGRATION_DESIGN_3B1.md proposes Profile verification fields and delivery attempt/
budget tables, token alternatives, defaults, constraints, concurrency, old-row
impact, mixed-version compatibility and rollback. No fields/migrations added.

## 3. Actual verification

Python 3.12.6; isolated environment installed existing pinned requirements.
Supported Node 24.19.0 invoked explicitly (Windows npm.cmd otherwise selected an
older Node). Existing tools only; no project dependency additions. Test mail uses
Django's in-memory backend; no real SMTP or production data involved.

| Package | Full backend suite | Frontend component tests | Other gates |
|---|---|---|---|
| WP16 | 90 run: 89 passed, 1 skipped | 25 passed | all passed |
| WP18 | 94 run: 93 passed, 1 skipped | 32 passed | all passed |
| WP21 | 99 run: 98 passed, 1 skipped | 32 passed | all passed |
| WP22 / final code | 111 run: 110 passed, 1 skipped | 32 passed | all passed |

Every package ran pip check, manage.py check, makemigrations --check --dry-run,
full Django tests, locked npm ci, lint, component tests and build. Production-like
check --deploy used dummy settings: only intentional W005/W021 remain because
HSTS includeSubDomains/preload are disabled. No warning suppression. Dependency
scans returned no known vulnerabilities for both requirement files; exact outputs
and scanner version are retained in DEPENDENCY_ADVISORIES.md and audit-evidence/.

Final targeted backup/monitoring run: 17 passed. Initial backup tests exposed
SQLite handles remaining open on Windows; explicit connection closing fixed this
before the passing full suite. The one backend skip is Windows symlink privilege
coverage; Linux CI must exercise it after a separately authorized push. No CI run
or production verification is implied. Coverage/E2E/accessibility were not rerun.
Final frontend main bundle: 415.26 kB, gzip 134.63 kB (Vite output).

## 4. Manual review script — local first

Use the isolated checkout without switching Michael's dirty original checkout:

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test --noinput
```

Expected: no system issues/schema changes; 111 tests run, one Windows skip. Inspect
accounts/test_csrf.py and frontend src/test/csrf-client.test.js for origin rejection,
cookie/token rotation, existing sessions and bounded/concurrent recovery checks.
The strict backend CSRF tests enforce checks; ordinary Django test-client exemption
is not a production bypass.

For an already running LOCAL server (do not start one against production data):

```powershell
curl.exe -i http://localhost:8000/api/health/
curl.exe -I http://localhost:8000/api/health/
curl.exe -i http://localhost:8000/api/accounts/csrf/
curl.exe -i -X POST http://localhost:8000/api/accounts/refresh/ -H "Origin: http://localhost:5173" -H "Content-Type: application/json" --data '{}'
```

Expected: health 200 minimal status JSON; HEAD no body; CSRF bootstrap no-store
and CSRF cookie; tokenless refresh 403 with code csrf_failed. Do not paste token/
cookie output into chat. In a browser with a disposable local account, log in,
reload, trigger concurrent authenticated requests after access expiry, and log out.
Expect one silent refresh and retained login after temporary network/429 failures.

Read BACKUP_ROUTINE.md before invoking a backup: dry-run first, private destination
outside repo/media, never use real media mode without pausing all writers. Rehearse
hash/integrity checks and restore into a NEW isolated folder. This phase did not
copy production personal data or execute any live backup.

After a separate future deployment approval, Michael verifies origin/scheme behind
the trusted proxy, private log folder access/permissions, health/429, owner downloads,
blocked direct private URLs and a normal ingestion run. Follow MONITORING_RUNBOOK.md
and the existing deployment checklist; do not change the pinned 3A rollout now.

## 5. Rollback, limits and decisions

- Roll back reviewed WP18 client/server/build together. Reload old tabs; never
  disable CSRF on the server to accommodate a stale client.
- Health is not evidence of mail delivery or ingestion freshness. Existing DRF
  shared file-cache limits remain approximate rather than atomic mail quotas.
- Safe application error events do not sanitize separate platform access/console
  logs. Per-process rotations multiply disk usage; review stale worker files.
- Backup writer assertion cannot itself stop writers. Disk exhaustion can leave
  partial snapshots; retention never frees space automatically. Backup credentials
  are deliberately excluded, so this is not a complete machine/configuration image.
- No real SMTP, password reset, verification, consent or rights features implemented.
  Approve exact migration design, token expiry/revocation behavior, global delivery
  cap/allocation, metadata retention and unverified-account restrictions first.
- Future 3B rollout and Stage B HTTPS verification stay Michael-owned. Stage A
  success is owner-confirmed as above. See PHASE_A_DEPLOYMENT.md for exact server
  steps, requirements installation/version checks and rollback.
  No pushes, main merges, connector writes or production operations performed.

## 6. Git and review gate

Original lockfile/coverage changes, old stash and Git configuration were preserved.
All new author/committer identities were checked against the configured noreply
address using git log over c4b9364..integration/checkpoint-3b. No identity changed.
Inspect the final commit with the same command after handback.

```powershell
git log --format="%h %ae | %ce" c4b9364..integration/checkpoint-3b
```

STOP for Michael's migration-design review. Phase B requires a separate prompt.

## 7. Queued follow-ups — not started

- No-skills job cards: replace misleading 0% match with an add-skills prompt.
- Registration error-message styling.
- New-account job-alert checkboxes default off.

These remain later work, outside Phase A. No implementation was made.

</details>

<a id="record-checkpoint3b-account-email-review"></a>

### checkpoint3b account email review

<details>
<summary>Read dated details</summary>

Source: `docs/CHECKPOINT3B_ACCOUNT_EMAIL_REVIEW.md`; input SHA-256 `c0cac6895c7426cfef9f2c6142794a21f31d7470450f8b5a728946cd73b6b4f1`.

# Checkpoint 3B — account-email integration review


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026. Branch feature/account-email-integration, based on the approved
accounts package 5e98331. Suggested 5 points. Scope explicitly approved: integrate
account emails with delivery accounting, tests, real sending disabled, no push,
deployment or DNS changes, stop for review. No new migration/dependency.

## Changes

accounts/email_delivery.py bridges reset/verification link creation to the reviewed
DeliveryService. Requests use the common atomic ledger/daily budgets rather than
bypassing accounting with a direct EmailMessage call. Both purposes consume the
same 30-message account allocation, within the approved global 200 and fixed
150 application / 30 account / 20 alert partitions. Failed provider attempts count;
no refund for an attempted send. Existing IP/user/target throttles remain unchanged.

There is deliberately NO production transport factory in this package. The only
bridge sink is MemoryTransport; it requires explicit ACCOUNT_EMAIL_TEST_CAPTURE=True
AND the exact Django locmem backend, checked again at send time. Other backends,
including console/SMTP, cannot activate it. No Brevo credentials/configuration read,
API call, live email, DNS write or provider setting change. Existing console job
mail is untouched. Real activation needs a separately reviewed provider factory,
sender/domain and pilot controls; do not swap a backend to activate this test path.

When disabled, requests do not generate security tokens, create receipt/budget
rows, construct the test transport, or send email. Existing truthful disabled-email
UI remains. Opt-in tests exercise the real accounting service with an in-memory
message sink; mock results cover rejection and uncertainty without network calls.

## Request identity and retry behavior

Reset and verification request serializers accept optional request_id UUID in JSON;
absent IDs are generated server-side for older callers. Modern frontend creates a
UUID per logical action. Network errors keep it for a manual repeat, so a completed
request whose response was lost does not send again. Changing the target email
starts a new action. Explicit requests after accepted responses or definite 502
failures use a new ID. No new custom header or CORS change.

DeliveryService remains authoritative for same-key binding, atomic quota, concurrent
duplicates and uncertain receipts. A matching repeated ID reuses the old receipt;
another user/purpose/recipient cannot reuse it to send. A NEW explicit request may
select its latest definite-failure receipt for retry, consuming another slot. There
is no background/provider retry. Unknown/reserved outcomes block fresh sends even
after midnight; this API does not reconcile/reset them or provide a bypass button.

Only keyed recipient digests and minimal receipts enter the database. The bridge
derives its digest key from Django signing configuration using a separate purpose;
no new secret is stored. Email bodies, links and token material stay in memory and
the test outbox. Signing-key rotation and metadata expiry must be separately reviewed
to preserve uncertain-outcome duplicate protection. No automatic retention cleanup.

## Safe response contract

Public password-reset requests retain the SAME 202 JSON for known/unknown/inactive/
unusable accounts and for accepted, failed, quota-blocked or uncertain delivery.
They expose no receipt ID or provider state. Generic text warns that a previous
attempt may already have been accepted and to check the inbox before requesting
again. Validation errors and request throttles remain account-independent 400/429.
No claim of constant-time real provider sending is made: none is enabled here.

Authenticated verification can report its owner's outcomes:

| Outcome | HTTP / behavior |
|---|---|
| Disabled | 202, delivery_available false; no send |
| Already verified | 200, no new attempt |
| Accepted | 202; provider acceptance is not inbox delivery |
| Definite failure | 502; states capacity consumed and a new explicit request may retry |
| Account/platform quota | 429 plus Retry-After until next Nairobi midnight |
| Unknown, reserved or accounting unavailable | 409; check inbox and require reconciliation |

New responses retain private/no-store via existing account view finalization.
Frontend renders safe detail/error arrays, 429 guidance and network uncertainty
warning. Existing bounded CSRF retry remains limited to pre-side-effect rejection;
ordinary 409/429/502/network failures never automatically repeat a mutation.

## Tests / gates

Focused final integration plus existing recovery suite: 26 passed. New tests prove shared
purpose accounting, 30-slot cap, no allocation borrowing, one send per request ID,
generic public uncertainty/quota/absence, authenticated 409/502/429, consumed failed
attempts with explicit new retry, SMTP/Brevo no-call guards, no disabled token/DB
side effects, bad request IDs/origins, and Nairobi midnight Retry-After. No real
messages or credentials used. Existing service thread tests remain in full suite.

Recovery tests now use TransactionTestCase instead of TestCase because the delivery
service intentionally rejects outer database transactions before network I/O.
Fixtures/assertions remain; isolation now matches real non-atomic request handling.
Frontend adds tests for retained UUID after network failure and no automatic retry
of uncertain verification. Final gates: Python 3.12.6, pip check/system check and
migration-drift check passed; 167 backend tests run in 76.113 seconds, 166 passed
and one Windows symlink-privilege skip. Node 24.19 locked npm ci, lint, all 44
component tests and build passed. No CI/production/E2E run claimed. The memory sink
pins its connection explicitly to locmem even if configuration changes after the
gate; a dedicated test confirms it cannot open SMTP. Already-verified requests also
prove no charge or duplicate mail. frontend_build is packaged once as the final
package commit from the verified dist. No source dependency/lockfile changes.

## Local review (PowerShell)

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py test accounts.test_email_integration accounts.test_recovery --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Use synthetic test DB only. Tests themselves opt into memory capture; do not print
captured message bodies/links or enable it on production. On an independently
prepared local app with default settings, request reset/verification and confirm
the UI says no email was sent. No backend/credential change is needed for that check.

## Rollout, rollback and remaining prerequisites

No rollout is performed. This branch contains local schema, delivery and accounts
prerequisites. Any future approved release needs verified backup, staged migration
source, reviewed migrate --plan (jobs/0008 and profiles/0003/0004 if not yet applied),
migrations BEFORE code activation, and coordinated frontend/server smoke checks.
No new migration in this package. Keep production redirect=False/HSTS=0 pending the
independent host scheme gate. No changes to production configuration or deployment SHA.

Rollback must retain the reviewed password-reset marker/fingerprint refresh guard
after resets have occurred; see CHECKPOINT3B_ACCOUNTS_REVIEW.md. Disabling the new
bridge/test capture leaves real mail disabled. Retain ledger/budget rows and newer
DB writes. Do not restore an old database, reverse proof migrations or blindly revert
to pre-reset refresh code. Preserve receipts for uncertainty reconciliation.

Before real sending: authenticate domain/sender, approve owner-only recipient pilot,
configure credentials privately, review production factory/digest-key rotation,
bounce/complaint handling, uncertain-receipt reconciliation/expiry and legal retention,
then authorize a separate activation package. Account reset/verification consent is
not optional job-alert consent. Applications, alert defaults, pending UI fixes,
payments, auth-token logic and DNS/provider settings are untouched here.

All commits must use configured noreply identity. Stop after this package for review.

</details>

<a id="record-checkpoint3b-accounts-review"></a>

### checkpoint3b accounts review

<details>
<summary>Read dated details</summary>

Source: `docs/CHECKPOINT3B_ACCOUNTS_REVIEW.md`; input SHA-256 `4dd5e34824ce49446d46062eeb2af2f386308cb01d500ae87a1da9be8e674570`.

# Checkpoint 3B — password reset and email verification review


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026. Branch feature/account-recovery-verification, based on reviewed
dormant delivery package 1e0e412. Suggested 8 points. Michael authorized these flows
and separately approved the narrow reset-revocation design extension after the
existing untracked rotated-refresh issue was identified. No push or deployment.

## Changes and boundaries

New APIs under /api/accounts/:

| Route | Access / operation |
|---|---|
| password-reset/request/ | Public POST, generic 202 for eligible/unknown/inactive accounts |
| password-reset/confirm/ | Public POST, token plus matching validated new passwords |
| verification/request/ | Authenticated POST for current address |
| verification/confirm/ | Public POST with purpose-bound signed proof, explicit confirmation |
| verification/status/ | Authenticated GET, verified boolean for current address |

Every mutation uses existing Django CSRF/token plus exact Origin checks; no CORS
expansion. Public recovery endpoints ignore stale JWT headers and the existing
axios client gains only their public/CSRF classifications. CSRF retries remain
bounded and occur only for identified pre-side-effect csrf_failed rejections.
All new API responses are private/no-store. No JWT or token link in JSON responses.

Reset uses Django's standard PasswordResetTokenGenerator with PASSWORD_RESET_TIMEOUT
1800 seconds, explicit validation against configured password validators, every
field-keyed error, password confirmation, active/usable account checks, atomic
password/revocation updates and replay rejection. No automatic login. Password/email
changes invalidate old reset links. Existing hashes are never changed en masse.

Verification uses a separate signature purpose salt and 86400-second expiry,
binding user/current email/profile verification state/password state. GET does not
verify. Valid repeated clicks are harmless; mismatched/changed/expired/tampered links
fail. Resetting an unverified account's password invalidates its old verification
link. Status compares current address to proof; historical accounts remain unverified.
Email verification is not optional-processing consent or legal compliance.

## Real email remains disabled

Existing Django console EMAIL_BACKEND and the dormant Brevo service are unchanged.
New security links are NEVER written to console, sent through SMTP/Brevo, returned
through the API, or stored in a token table. A closed test-capture path requires BOTH
ACCOUNT_EMAIL_TEST_CAPTURE=True and the exact Django locmem backend. There is no
environment activation flag for real email. Default/mismatched backend does not
generate a reset token or send mail. No credentials were read or written.

UI explicitly states "Email delivery is not enabled yet. No email was sent."
This is a testable feature scaffold, not a functioning public mailbox recovery
service until a later reviewed sending integration. Future real email must go
through approved budgets, owner-only rollout controls and provider/domain setup;
do not simply replace the test backend with SMTP. Existing console job mail remains
unchanged and can still contain private content outside the new security-link flow.

## Approved reset revocation extension and migration

profiles/0004_profile_password_reset_at depends on profiles/0003. Adds only a nullable,
blank DateTimeField default=None. No User model change or historical migration edit.
Existing rows remain None; reset is the only new flow writing the marker.

Previously RefreshView manually rotated identifiers but did not persist the new
token in OutstandingToken. Blacklisting only recorded tokens after reset would
miss those old live tokens. New login tokens include a keyed password fingerprint;
refresh checks the current account/password, rejects inactive/missing owners,
and registers rotated tokens through the existing library outstand() method.

Legacy no-fingerprint tokens remain valid for accounts without a reset marker.
After that account resets, all legacy tokens fail, including untracked rotated
tokens. Fingerprinted tokens fail after password change. Reset also blacklists
recorded outstanding tokens and deletes the requesting browser's refresh cookie.
New login after reset works immediately. JWT lifetimes, existing rotation/blacklist
configuration, HttpOnly/Secure/Lax behavior and access-token validation are unchanged.
Existing access tokens retain up to their ordinary 15-minute lifetime.

The reset transaction's first operation is a no-op user update, serializing SQLite
writers BEFORE checking the token/password; select_for_update alone is insufficient
on SQLite. Verification similarly claims its Profile before checking/updating proof.
No SMTP/network I/O inside either transaction. No reusable stored raw reset token.

## Request limits and token handling

| Setting name | Default | Key |
|---|---|---|
| THROTTLE_ACCOUNT_EMAIL_RATE | 5/hour | Resolved IP for public reset; user ID for authenticated verification |
| THROTTLE_ACCOUNT_TARGET_RATE | 3/hour | Combined reset/verification, keyed digest of normalized email |
| THROTTLE_ACCOUNT_CONFIRM_RATE | 10/hour | Resolved IP |
| THROTTLE_VERIFICATION_STATUS_RATE | 60/min | User ID |

Rates are env-overridable and use the existing shared throttle-cache alias and
NUM_PROXIES configuration. These are approximate abuse controls, not atomic
delivery quotas. Target limits apply to unknown emails too; no plaintext address
is placed in cache keys. Generic reset status/body avoid account enumeration;
no claim of constant-time real provider delivery is made (none enabled here).

Frontend adds /forgot-password, /reset-password, /verify-email and authenticated
/email-verification. Login links to reset; Profile links to verification. Code is
lazy-loaded. Token links use fragments, not server-visible query/path credentials;
the component removes fragments from browser history and holds values only in
memory, clearing them on success. It supports React StrictMode without losing the
token. Refreshing the page after removal requires requesting a new link. It does
not store credentials in local/session storage. Requests render all field errors,
429 wait guidance, pending/disabled states and explicit success. No automatic
verification on page load or automatic retries of normal mutation failures.

## Actual verification

Python 3.12.6, pinned Django 6.1.2/PyJWT 2.15.1. pip check, Django system check and
makemigrations --check --dry-run passed. Full Django suite: 154 run in 88.184 seconds,
153 passed, one Windows symlink-privilege skip. Focused recovery plus existing CSRF
suite: 17 passed. No real email/production database used; capture only in memory.

Node 24.19: locked npm ci, lint, all 42 component tests (6 files) and build passed.
Focused recovery/client tests: 17 passed. First full frontend run exposed Profile's
test lacking router context for its new Link; corrected fixture, then lint/full
suite/build passed. No protection or assertion was removed. Linux CI/real-browser
end-to-end/production verification were not run. One committed build packaging is
the final package commit; no dependency/lockfile change.

Tests cover generic request responses, disabled and console no-send behavior,
validators/mismatch, reset expiry/tampering/email-change/replay, tracked blacklist,
untracked legacy rotation revocation, current fingerprint rejection, successful new
login, old access-token grace, signed verification expiry/purpose/address/reset
binding, idempotent confirmation, authorization/status, strict CSRF/stale JWT,
target throttle/reset, fragment cleanup under StrictMode, all frontend errors,
explicit verification click, missing links and truthful unavailable-email UI.

## Local review script (PowerShell)

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py test accounts.test_recovery accounts.test_csrf --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Tests generate synthetic credentials only internally; do not print mail/token
contents or point test settings to a live DB. On a separately prepared local app,
visit Forgot password and Email verification and confirm requests explicitly say no
email was sent. Missing/expired token forms must give recovery guidance. Automated
locmem tests exercise valid links without manual token handling or real sending.

## Future rollout and rollback — not performed

This branch includes unpublished schema/delivery prerequisites. After separate
push/review/CI/merge/deployment authorization, back up and verify DB/media, pause
writers, stage exact approved migration source and inspect migrate --plan. Expect
jobs/0008 and profiles/0003 then profiles/0004 if not already applied. Apply before
new model/auth code handles requests, then activate the paired frontend/server.
Never silently apply an unexpected migration. Keep host HTTPS and the currently
approved redirect=False/HSTS=0 until the separate scheme gate is resolved.

CRITICAL rollback: retain the new reset revocation guard and reset marker once
password reset has been used. Pre-package refresh code ignores that marker and
could accept old untracked tokens. Prefer a forward fix, or roll back UI/endpoints
while retaining patched refresh validation. A full old-auth rollback requires a
separately reviewed account/session invalidation plan. Do not reverse/drop the
marker, restore old DB over newer writes, or change signing credentials casually.
This supersedes older generic code-only rollback advice for the reset-bearing release.

## Remaining scope / stop

No real delivery activation, sender/domain configuration, secrets, CI/CORS/ingestion,
payments, registration styling, no-skills match prompt or alert-default changes.
No change to existing application send API or alert lifecycle. Account-email budget
integration and pilot recipients need the next separately authorized package.

References: [Django reset settings](https://docs.djangoproject.com/en/6.1/ref/settings/#password-reset-timeout),
[Django password recovery](https://docs.djangoproject.com/en/6.1/topics/auth/default/#django.contrib.auth.views.PasswordResetView),
[SimpleJWT blacklist](https://django-rest-framework-simplejwt.readthedocs.io/en/stable/blacklist_app.html).

All new commits must use Michael's configured noreply identity. Stop for review;
no push or deployment was performed.

</details>

<a id="record-checkpoint3b-delivery-review"></a>

### checkpoint3b delivery review

<details>
<summary>Read dated details</summary>

Source: `docs/CHECKPOINT3B_DELIVERY_REVIEW.md`; input SHA-256 `a69db249cb4bf766dd1674358a731e4994221e5222d26fe7faf7104bdc0b76cb`.

# Checkpoint 3B — dormant Brevo transport and quota service review


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026. Branch feature/brevo-delivery-service, based on locally approved
schema package 6fe90d3. Michael authorized this package and confirmed that definite
provider failures consume quota. No push, deployment, provider/DNS write or real
email. Schema package remains an unpublished prerequisite; no new migration here.

## Package / suggested points / files

Suggested 8 points: isolated adapter, transactional accounting, concurrency/recovery
tests and documentation. jobs/brevo_transport.py contains the standard-library HTTPS
adapter; jobs/delivery_service.py contains accounting and orchestration. Tests in
jobs/test_delivery_service.py. Existing endpoints, ingestion, matching, auth client,
Django EMAIL_BACKEND, configuration, dependencies and CI remain untouched.

## Delivery contract

- Disabled by default: DeliveryService requires explicit enabled=True from a future
  reviewed caller; there is no environment activation switch in this package. No
  production view/task imports the service. Existing console mail remains unchanged.
- The adapter receives configuration through its constructor (no credentials loaded
  or persisted). Repr redacts configuration. Uses POST only to Brevo's fixed HTTPS
  /v3/smtp/email endpoint, standard-library TLS verification, bounded timeout and
  response reads, with redirects forbidden. No arbitrary headers or recipients list.
- Frozen one-recipient payload: platform From, applicant Reply-To for applications,
  plain text and optional byte attachments. No URL attachments or file fetching;
  attachment limit must be explicitly supplied by future approved caller, otherwise
  attachments are disabled. No new numeric attachment policy was selected.
- Only a 201 with valid compact messageId is accepted. Acceptance is not delivery.
  4xx (except ambiguous 408) is definite failure; 5xx, redirect, timeout, malformed
  acceptance or unexpected transport errors are unknown. Never log raw provider
  bodies or exception text. No provider/network automatic retry loop.

Provider contract verified against [Brevo transactional API reference](https://developers.brevo.com/reference/send-transac-email)
on 16 October 2026. No authenticated API call was used to verify implementation;
all sending tests mock network access. No provider exactly-once guarantee claimed.

## Atomic accounting and eligibility

Defaults: 200 total attempts per Nairobi calendar day, fixed allocations 150
applications / 30 combined verification-reset / 20 alerts, and 10 applications per
user/day. Policy values are validated injectable configuration, not an activated
production setting. Allocations cannot borrow from each other. Conditional total
check also protects against legacy/changed policy counters already at the global cap.

Preflight checks payload/recipient/owner/purpose before reserving. Applications must
be email-ready and match the current verified mailbox; checks are repeated under
the reservation writer lock. Account recipients must match the account. Alert
delivery needs both notify_email and explicit confirmation supplied by a future
consent-aware caller; current historical preferences alone are insufficient proof.
No public account-email endpoint exists, and its request throttles remain a prerequisite.

The first DB operation inside the transaction is an insert-or-ignore global budget
row. On SQLite this serializes competing writers before read checks, including cold
initialization. One transaction conditionally reserves global/category and user
capacity and writes the validated unique receipt. Per-user failure rolls back its
global increment. Existing schema constraints guard unresolved application/alert
attempts and idempotency keys. No new cache, lock table or dependency.

Network I/O runs only after commit; caller transactions are rejected. Up to three
database-only lock attempts occur before any provider call, with short backoff.
If accounting stays busy, fail generically with no email attempted. No database
retry happens after a provider call. Payload/body/token/recipient address is never
stored in the ledger; only keyed recipient digest and minimal receipt metadata.

## Outcomes, retries and crash recovery

- Once reserved, accepted, definite failure and unknown all consume daily capacity.
  Invalid/preflight-rejected requests do not reserve. No refund API is exposed;
  a crash after reservation conservatively keeps capacity even if no send occurred.
- Repeating a key with the same purpose returns its receipt and never calls Brevo
  again. Reusing it for another owner/purpose/source/recipient fails without sending.
- A different key cannot repeat an accepted/reserved application/alert. Unknown
  outcomes block fresh attempts across midnight, preserving duplicate protection.
- A definite-failure application retry must explicitly name the failed receipt and
  use a new key; it consumes another attempt. Automatic retries are absent.
- Alert retry bounds have not been approved, so alert retries are disabled rather
  than inventing a count/backoff. Account resend/request limits remain future caller
  policy; no public path exists to exploit their missing integration.
- Unknown retries remain blocked until a separately reviewed reconciliation flow can
  resolve provider evidence and show a warning. A warning alone is not reconciliation.
  This package deliberately does not add an operator resend button or destructive
  state-reset command. Accepted/unknown expiry handling also remains pending.
- If the worker crashes or recording the receipt fails after provider acceptance,
  reserved state survives and blocks repeats. Database recovery can leave uncertainty;
  it does not justify retrying. Exceptions are replaced with generic safe messages.

The service writes accounting receipts only. It does not change existing Application
status or Notification.sent_email. Those lifecycle updates need a later coordinated
integration package; do not mix old senders and new services for real delivery.

## Actual verification

Focused tests (21 passed) cover payload/attachment limits/Reply-To, fixed endpoint,
redirect refusal, status classification, response limits, network ambiguity, redaction,
disabled defaults, verified ownership, ten-user cap, shared account allocation,
global/category boundaries, Nairobi midnight, idempotency conflicts, explicit failure
retry, alert consent/retry guard, unknown outcomes, DB-busy bound, no outer transaction,
sanitized unexpected errors, and durable reservation after receipt-write failure.

Two real-thread tests use the disposable SQLite test database with mocked transport:
same-request race produces one provider call; competition for the final platform
slot yields one acceptance and one quota rejection. Test transport asserts that no
network call occurs inside a transaction. No provider API key or real CV used.

Actual final gates: Python 3.12.6, pip check/system check/migration-drift check pass;
141 backend tests run in 75.542 seconds, 140 passed and one Windows symlink-privilege
skip. Node 24.19 locked npm ci, lint, 32 component tests and build pass. The Windows
skip still requires Linux CI after a future authorized push. No CI run claimed.
Frontend dist matches committed frontend_build byte-for-byte; verification build
only, with no artifact regeneration.
No changes to existing/new migrations from the previously approved schema package.

Reproduce locally in PowerShell:

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py test jobs.test_delivery_service --noinput
```

## Activation prerequisites / rollback / stop

Real delivery remains blocked pending authenticated sending-domain setup, sender/
reply handling, explicit owner-only recipient pilot approval, reviewed credentials
entry by Michael, account-email throttles, alert consent storage/confirmation, retry
bounds, attachment policy, bounce/complaint and unresolved receipt retention policy.
Website remains mathenge.pythonanywhere.com. michaelmathenge.dev DNS settings are
untouched. Console rollback halts real mail; no silent success claim should replace
real delivery after a later activation.

This package needs no production operation. Future integration requires review,
backup, schema migration before activation and end-to-end lifecycle/502/400/quota
UX tests. Until then, dormant service methods are internal building blocks, not a
supported sending API. To roll back this package, restore the reviewed code only;
keep additive schema and receipts. No DB restore, credential change or DNS rollback.

Stop for Michael's review. No push/deployment or further accounts/SMTP integration.

</details>

<a id="record-checkpoint3b-pilot-review"></a>

### checkpoint3b pilot review

<details>
<summary>Read dated details</summary>

Source: `docs/CHECKPOINT3B_PILOT_REVIEW.md`; input SHA-256 `63bde784633881dcc838c2a62f594db2842f807713777a78c8f8dabbf8094584`.

# Checkpoint 3B — owner-only account-email pilot review


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

16 October 2026. Branch `codex/owner-email-pilot`, based on documentation preparation
`c4b6a37` and reviewed account-email integration `92c739d`. Suggested 5 points.
Michael approved building the pilot controls/tests with real sending disabled,
no push/deployment and stop for review. Scope supersedes the previous test-only
factory restriction; no token/reset/refresh logic, migration, dependency, frontend
source, CI, ingestion, CORS, DNS or production changes.

## Changes

`accounts/pilot.py` validates explicit owner-only configuration and constructs the
isolated Brevo adapter. `REAL_EMAIL_ENABLED` defaults false. Disabled settings do
not read BREVO_API_KEY; no credential was accessed or created during this package.
Activation requires owner_pilot mode, a positive owner ID, one exact recipient,
one sender address, HTTPS link origin, timeout 1–60 seconds, console Django backend
and test capture off. Wildcards, surrounding whitespace and header injection are
rejected. Invalid/incomplete configuration yields sanitized system check accounts.E001
and fails closed at runtime. System checks construct but never call the transport.

Only an active matching owner whose current account address matches the recipient
can request a pilot reset/verification delivery. Eligibility is checked BEFORE
creating a security token or budget row. Recipients are normalized case-insensitively,
never rewritten. Non-owner reset responses remain generic; authenticated verification
truthfully reports delivery unavailable. No public lookup reveals provider outcomes.
Synchronous pilot responses are not constant-time; enumeration resistance has no
timing guarantee. The owner mailbox must be confirmed privately before activation.

The service repeats owner/channel/address checks under the SQLite writer reservation
lock. The transport wrapper checks single-recipient payload, sender and configuration
again before provider I/O. No CC/BCC, attachments, Reply-To overrides, application
or alert channels. From display name is fixed to Ajiri; sender address is privately
configured to the verified alias. Existing standard-library adapter retains fixed
HTTPS endpoint, redirect refusal, timeout bound, response bound and sanitized errors.

An extra ceiling defaults to five attempts per Nairobi day; configuration may lower
it to 1–4, not expand it. The existing atomic global conditional reservation uses
min(200, pilot ceiling), counting ALL prior global usage that day. Fixed approved
allocations remain 150 application / 30 combined account / 20 alerts, per-user
application cap 10. Those existing limits are Policy fields, not new env settings.
No migration, independent cache counter or quota refund. If earlier non-pilot usage
already exceeds five, the pilot waits until the next Nairobi day.

Failed sends consume capacity. Unknown/reserved outcomes block further attempts;
same-key requests never resend. Only explicit new requests after definite failure
may retry, consuming another slot. No network/background retry or reconciliation
bypass. The budget/receipt transaction completes before network I/O. A configuration
change after reservation can conservatively leave an unknown receipt rather than
permit sending outside the allowlist.

Application and alert callers remain on the EXISTING Django console backend;
they are not wired to Brevo. Pilot configuration refuses SMTP or another Django
backend. Existing console output can still contain private application/alert text;
new security links never fall back to console. Do not publish platform console logs.

## Actual verification

Python 3.12 environment: system check, migration drift check and pip check passed.
Full Django suite: **178 run, 177 passed, one Windows symlink-privilege skip**,
75.048 seconds. No CI/Linux/production/inbox test claimed. Focused first run caught
two issues: wildcard email local parts needed explicit rejection, and an existing
test-sink connection-pinning contract needed preserving. Both fixed; focused
22 tests then passed, and the full suite includes two additional pilot tests.

New tests cover default-off no-link/no-write behavior, incomplete settings, wildcard/
header rejection, sanitized checks, non-owner/changed address/purpose blocking,
single exact recipient, case normalization, fixed sender name, same-key idempotency,
shared purpose cap, concurrent last slot, prior-day/global use and next-day reset,
consumed failures, unknown no-retry, final-boundary CC/recipient/disable rejection,
no printed account links, generic public reset and truthful private rejection.
Every provider send is mocked; synthetic data only, no credentials or real email.
Existing adapter/service/recovery/ingestion tests remain in the full suite.

Production-like dummy `check --deploy`: only W005/W021 (includeSubDomains/preload)
remain, intentionally disabled under the approved short-HSTS policy. No settings
were applied to production; redirect/HSTS scheme gate remains independent.

Node 24.19: explicit locked npm ci, lint, **44 frontend tests passed**, build passed.
No frontend source/build/lockfile diff. Existing committed frontend_build remains
unchanged because this is a backend package. Initial restricted runs hit filesystem
permissions and the default npm launcher used old Node 22.15; corrected by explicit
Node 24 npm-cli and approved execution permissions. The restricted backend run was
interrupted after media filesystem errors; the complete unrestricted run above
passed. These were local tooling limitations, not passing claims for those attempts.

## Local review script (PowerShell)

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:REAL_EMAIL_ENABLED = 'False'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test accounts.test_pilot accounts.test_email_integration --noinput
```

Expected: system check clean, no model changes, all focused tests pass with mocked
provider calls only. Do not set live pilot credentials or enable sending for review.
Tests temporarily override settings internally with synthetic values.

## Release, rollback and remaining decisions

Follow `docs/OWNER_EMAIL_PILOT.md` only after separate release authorization:
reviewed pinned SHA, green CI, private verified backup/restore, stage code, inspect
and apply the previously approved prerequisite migrations BEFORE activation,
private credential entry by Michael, paired release smoke checks, then separately
approved owner-only sending. No migration in this package. Existing schema/account
prerequisites are unpublished local work; do not deploy this patch in isolation.

No actual owner ID/recipient or secret is committed. Before activation confirm the
owner account still uses the mailbox selected for the pilot; do not silently change
account addresses. Alias receipt and Brevo connectivity/delivery remain unverified
by this implementation. Confirm provider account sending eligibility privately.
Credential setup, push/merge/deployment and real-message tests remain unperformed.

Rollback: set REAL_EMAIL_ENABLED false, reload and verify disabled responses/no
provider contact. Retain receipts, verification state, password-reset marker and
patched refresh revocation guard. Prefer a forward fix. Never restore an old DB
over newer writes or roll back to pre-reset auth code. Runtime credential rotation,
uncertain-receipt reconciliation/expiry and legal retention need separate review.
Bounce/complaint automation is not implemented: stop the supervised pilot on either;
do not expand to public users. Application integration, attachment policy and
consent-aware alert delivery remain later packages. Queued product UI fixes untouched.

Commits use the configured noreply author/committer identity; Git config/stash and
the original checkout's lockfile/coverage are preserved. Stop for review here.

</details>

<a id="record-checkpoint4-phase-c-review"></a>

### checkpoint4 phase c review

<details>
<summary>Read dated details</summary>

Source: `docs/CHECKPOINT4_PHASE_C_REVIEW.md`; input SHA-256 `95610d89800303157b5cedae291f91561cb40d47bd03d9f109e53b7489adfd0b`.

# Checkpoint 4 Phase C review


19 October 2026, Africa/Nairobi. Local work only in
`C:\dev\ajiri\.worktrees\checkpoint-4`, integration branch `integration/checkpoint-4`.
No push, PR, remote merge, production inspection/deployment, real email, credential
handling, migration or new dependency. Local package merges were explicitly approved.

## 1. Baseline and package summary

Pinned base: **4b6e99bac4995fd3e36e6fbe1c7e3176383b6214**. Fetched remote main
includes PR21 checkout, PR22 npm updates, PR23 CV date/save feedback and PR24's
standalone copy of the concurrent-draft fixture repair. Last recorded production
is **641cdfb**, not the pinned main. No production state was inspected in Phase C.

The base-to-recorded-production delta is 36 files, 802 insertions/167 deletions:
CV date controls/save feedback, registration-to-CV coverage, frontend dependency
and committed build updates, checkout workflow updates, concurrent-draft fixture
repair and review/design documents. Six frontend direct dependency updates cover
lucide-react, React/React DOM, jsdom, oxlint and Vitest, plus lockfile resolution.
`git diff --name-only 641cdfb 4b6e99b -- '*migrations*' '*requirements*'` returned
no files. Earlier workflow changes belong to the base; Phase C changes no CI.

| Package | Branch | Source range | Local result | Points |
|---|---|---|---|---:|
| C1 | feature/acceptance-journey | 4b6e99b..aa7404e | Gates passed; API/client tests, browser E2E not claimed | 5 |
| C2 | feature/cv-layout-verification | b10d9ed..385102d | Gates and Word rendering passed; other viewers pending | 3 |
| C3 | feature/ui-polish | a096aef..18cdb7b | Gates passed; phone/browser visual QA pending | 5 |
| C4 | docs/housekeeping | 01da76c..944d61b | Gates passed on repeat; intermittent test failure retained below | 2 |
| D1 | docs/alert-defaults-design | bc03f2d..389b751 | Design only; gates passed | 3 |
| D2 | docs/certificates-decisions | 22d5869..8d9b964 | Design only; gates passed | 2 |
| D3 | docs/application-alert-sending-design | c8a0d96..9aca022 | Design only; gates passed | 5 |

Total suggested estimate: 25 points, relative sizing rather than elapsed-time
promises. Each package is merged locally with --no-ff after successful gates.
The handback documentation is a final integration commit. C1's final build commit
is intentionally empty: its test-only changes produce identical committed assets.
C3's actual regenerated frontend_build is its final package commit; later builds
are verification only and match the committed target after index LF normalization.

## 2. Delivered changes and decisions

C1 extends the actual registration/login/verification/profile/CV APIs through draft
validation, preview, explicit approval, private download, version selection,
application preparation and review. It verifies byte-identical CV snapshots,
cross-owner denials, unchanged bytes after Profile edits, empty preparation outbox,
no provider/mail call, unchanged DeliveryAttempt AND DeliveryDailyBudget rows and
no sent timestamp. Existing component tests cover account/profile/builder stages;
the new route test joins Job Detail selection to the real Applications review UI,
with Send disabled and exactly one preparation POST. This is API integration plus
mocked component transitions, not one automated browser journey. No application
runtime defect was found in C1; its mock URL and asynchronous focus assertion were
corrected as test defects.

C2 uses cv-v2 for future approvals: explicit Calibri font/sizes, black text and no
inherited Title border. Dates stay in separate paragraphs; structural tests cover
heading hierarchy, defined numbering, no layout tabs/tables, positive page bounds,
long entries and optional omission. No existing approval/snapshot was regenerated.
Installed Word COM exported one six-page and one one-page synthetic fixture;
installed Poppler produced PNGs and every page was inspected for wrapping, overlap,
clipping and readability. An unavailable fitz import was replaced with installed
Poppler, without installing anything. LibreOffice was not found at the checked
standard location. Google Docs/phone rendering remains UNVERIFIED.

C3 retains the existing empty-skills distinction, uses exactly "Add skills to see
matches", preserves genuine zero scores and does not interpret missing profiles
as empty skills. FormErrors now has readable labels and separate spaced messages,
with existing IDs/associations intact. Download headers use all name parts:
Name_CV.docx, Name_CV_Company.docx, Name_Cover_Letter_Company.docx. Approved content
provides personal names; current account/company provides application labels.
Unicode NFKC, control/path/unsafe-character removal, underscore whitespace and
60-character components keep names safe, with Applicant/Company fallbacks. Django
encodes Unicode headers; existing client parsing is covered by new tests. Uploaded
CVs use neutral Uploaded_CV plus the supported format extension (.bin for unknown
legacy formats). Storage UUIDs and bytes remain unchanged. Labels may change with
account/company edits; they are not immutable provenance. See UI_POLISH_PHASE_C_REVIEW.md.

C4 changed only AGENTS sections 1/4/6/12 and added ancestry-grounded dated banners
to 19 historical reviews. A content-comparison script confirmed standing sections
and historical bodies are unchanged after newline normalization. Banners distinguish
versions already present at recorded production from versions whose deployment is
unverified. Original checkout AGENTS/lockfile changes, coverage, stash and Git
configuration were preserved; its branch was not switched.

D1 recommends a reviewed model-default migration for new-user email OFF; the
signal-only alternative is narrower and incomplete across creation paths. Existing
rows stay unchanged and need explicit current confirmation. In-app defaults remain
a separate decision. D2 enumerates every certificate approval with options/defaults,
private evidence, quotas, removal/backups, schema and rollback. D3 proposes shared
transport/ledger integration, consent, verified Reply-To, separately accounted
optional copies, attachment-default-disabled policy, truthful outcomes, suppression,
owner-controlled synthetic pilot, proposed migrations and legal/privacy questions.
None of D1-D3 changes defaults, consent, certificates, senders or schema.

## 3. Actual quality gates and limitations

All successful rows include backend check, makemigrations --check --dry-run, full
Django suite, locked npm ci, lint, full Vitest suite and build. Python 3.12.6 uses
the existing checkpoint-3b virtualenv against this worktree; Node is explicitly
24.19.0. No new virtualenv/dependency was created. Every npm ci reported zero
advisories for that locked install; this is not a new pip vulnerability audit.

| Package/run | Full Django suite | Frontend suite | Other gates |
|---|---|---|---|
| C1 | 210 run, OK, 1 skip; 112.762s | 67 passed after fixture/focus fixes | Passed |
| C2 | 213 run, OK, 1 skip; 127.384s | 67 passed | Passed |
| C3 | 216 run, OK, 1 skip; 122.986s | 71 passed | Passed |
| C4 first run | 216 run, 1 failure, 1 skip; 122.275s | Not reached | Check/drift passed |
| C4 repeat | 216 run, OK, 1 skip; 121.696s | 71 passed | Passed |
| D1 | 216 run, OK, 1 skip; 117.739s | 71 passed | Passed |
| D2 | 216 run, OK, 1 skip; 114.358s | 71 passed | Passed |
| D3 | 216 run, OK, 1 skip; 110.615s | 71 passed | Passed |

The existing Windows symlink skip remains; it is not treated as a passed symlink
test. C4's failure was jobs.test_delivery_service.DeliveryServiceTests.
test_concurrent_same_request_produces_one_provider_call: one thread returned
DeliveryError. Unchanged isolated rerun passed (1 test, 0.158s), then the full repeat
passed. This intermittence remains unresolved; no delivery code or assertion was
weakened. Do not interpret the repeated pass as a production reliability fix.

Focused actual results also include the extended journey (1, 4.374s), layout
structure (3, 0.398s), layout + existing builder behavior after fixture-version
update (16, 19.486s), download headers/sanitization (3, 0.542s) and the added daily
budget invariant (1, 5.607s). C1's first frontend run had a new mock missing the
paginated list query; after correction an existing animation-frame focus assertion
flaked. waitFor preserves its assertion and the final 67-test suite passed.

Runtime commands were executed from each backend/frontend directory with dotenv
disabled and REAL_EMAIL_ENABLED=False. Expected synthetic error-path logs are not
evidence of live failures. Command transcripts/tool outputs informed these results;
no private payloads or raw logs are committed. No Python 3.13/3.14 or remote CI run
is claimed for this unpushed checkpoint. Real inbox/employer sending is not tested.

## 4. Manual verification script for Michael

Keep this local and use synthetic data. Do not point the journey at production or
change production settings. Exact PowerShell verification commands:

```powershell
$repo = 'C:\dev\ajiri\.worktrees\checkpoint-4'
$python = 'C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend\.venv\Scripts\python.exe'
$node = 'C:\Users\micha\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$npm = 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js'
$env:PATH = (Split-Path $node) + ';' + $env:PATH
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:REAL_EMAIL_ENABLED = 'False'
function Invoke-Checked {
    param([string]$Executable, [string[]]$CommandArguments)
    & $Executable @CommandArguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Executable" }
}
Set-Location "$repo\ajiri-backend"
Invoke-Checked $python @('manage.py', 'check')
Invoke-Checked $python @('manage.py', 'makemigrations', '--check', '--dry-run')
Invoke-Checked $python @('manage.py', 'test', '--noinput')
Invoke-Checked $python @('manage.py', 'test', 'profiles.test_registration_cv_journey', 'profiles.test_cv_layout', 'profiles.test_download_names', '--noinput')
Set-Location "$repo\ajiri-frontend"
if ((& $node --version) -ne 'v24.19.0') { throw 'Node 24.19.0 required' }
Invoke-Checked $node @($npm, 'ci')
Invoke-Checked $node @($npm, 'run', 'lint')
Invoke-Checked $node @($npm, 'run', 'test', '--', '--run')
Invoke-Checked $node @($npm, 'run', 'build')
Set-Location $repo
git diff --check
git status --short
```

Expected: check clean; no migration drift; 216 tests run/OK with one Windows skip;
focused suite 7 tests/OK; Node v24.19.0; 71 frontend tests; successful lint/build;
no tracked changes. Stop at any error rather than continuing to a release. Tests
create/destroy an isolated test database using existing migrations; no normal
development or production database is migrated by this script.

For interactive UI review, use an existing disposable local development setup with
the already-reviewed schema and real sending disabled. If absent, report that
prerequisite rather than copying production data or applying migrations in Phase C.

1. Register a synthetic account, log in and save profile/skills. Exercise weak
   password errors and multiple field messages. Confirm readable labels and input
   associations. Do not use personal credentials or send verification mail.
2. Clear skills: job cards offer the profile prompt. Add a nonmatching skill:
   genuine 0% returns. Check small-screen and keyboard use; unavailable profiles
   must leave jobs usable without asserting an empty skill list.
3. Start a CV; enter long synthetic names/titles and dates. Submit an incomplete
   entry: every error is shown and input retained. Correct it, save/preview,
   explicitly approve and download. Compare text/order with the approved preview.
4. Follow CV_LAYOUT_VERIFICATION.md to create synthetic short/long DOCX fixtures
   and inspect Word, Google Docs and phone viewers. No agent cloud upload is included.
5. Select the approval on Job Detail, prepare and open application review. Do not
   press Send. Download its CV: hash must match the approved version. Profile edits
   must not alter the existing snapshot; a newer approval must not silently replace it.
6. Verify readable company-last names, Unicode names, neutral uploaded-PDF label,
   anonymous denial and cross-owner denial. Comparing synthetic downloads:

   ```powershell
   Get-FileHash 'C:\path\Approved_CV.docx', 'C:\path\Application_CV.docx' -Algorithm SHA256
   ```

   Expected: identical hashes. Do not paste document contents or private links.
7. Review D1-D3 as proposals, particularly in-app defaults, consent/retention,
   certificate malware risk/quotas, attachment limits, copy policy and suppression.

## 5. Open risks, rollout and rollback

- Delivery concurrency intermittence remains open despite successful repeat gates.
- Real phone/browser visuals and Google Docs rendering remain unverified; Word
  synthetic rendering does not guarantee all viewer pagination or fonts.
- Alert defaults remain True in current code; existing True values are not consent.
  Current legacy console sender status cannot establish inbox delivery. Broader
  application/alert transport stays gated until the proposed integrations are reviewed.
- Certificate uploads, scanning, new schema, recipient expansion and attachments
  are not implemented. Retention/erasure/legal/privacy decisions remain open.
- Production is not updated here. HSTS/proxy assurance, renewal, backup routines
  and future release approval remain operational follow-ups, not Phase C actions.

Future release requires a separately approved pinned CI-green SHA and verified
backup/stage/check/activation procedure. No new migration or backend requirements
change is planned by Phase C. Recheck the actual deployment delta before release.
Rollback paired source/client/build, retain all newer data/files and immutable
approvals. Reverting cv-v2 affects future generation only; never regenerate old
approvals or restore an old database routinely. Never revert reset revocation or
activate a legacy console/SMTP sending bypass as part of this rollback.

## 6. Jira-ready lines

- C1 — Registration to approved-CV application review | AC: real API journey plus
  client transitions; explicit approval/selection; exact snapshot bytes; ownership
  denial; no mail, provider call or budget change during preparation. Suggested 5.
- C2 — Verify portable CV document layout | AC: structural style/date/list checks;
  installed Word pages inspected; long/minimal fixtures; old approvals unchanged;
  Google Docs/phone checklist and honest limitations. Suggested 3.
- C3 — Polish matching prompts, errors and document names | AC: no-skills prompt;
  true zero preserved; all readable errors with stable IDs; safe Unicode/company-last
  headers; storage names/bytes unchanged; regressions/build pass. Suggested 5.
- C4 — Reconcile checkpoint scope and release status | AC: only four time-bound
  AGENTS sections changed; standing rules preserved; 19 historical review bodies
  retained beneath ancestry-backed banners; merged/deployed distinguished. Suggested 2.
- D1 — Design opt-in alert defaults and consent | AC: signal/model comparison,
  recommendation, preserved existing rows, explicit confirmation/evidence/unsubscribe,
  independent in-app decision, tests/rollback; no code/migration. Suggested 3.
- D2 — Decide private certificate evidence policy | AC: every format/validation,
  quota/storage/ownership/deletion/backup/sharing/schema choice has options,
  recommendation/default and pending approval; no implementation. Suggested 2.
- D3 — Design controlled application and alert delivery | AC: shared Brevo budgets,
  consent, Reply-To/copy, default-disabled attachments, truthful unknown/accepted
  states, bounce/complaint, synthetic owner-only pilot, proposed migrations,
  tests/rollback/privacy questions; no sending/code/migrations. Suggested 5.

## 7. Identity and stop

The required non-empty range was audited against git config user.email. Every new
author and committer matches Michael's configured noreply identity. It is rechecked
after the final handback commit. Remote main was fetched again at handback and
remains exactly the pinned SHA; no rebasing or base advancement occurred.

```powershell
git log --format="%h %ae | %ce" 4b6e99bac4995fd3e36e6fbe1c7e3176383b6214..HEAD
```

The isolated worktree is clean after handback. The original checkout still has its
pre-existing AGENTS.md/lockfile modifications, coverage and untracked worktrees;
its branch, stash and Git configuration were not changed.

Stop for Michael's review. No publication, deployment, new migration or wider
sending authorization is inferred from this handback.

</details>

<a id="record-sprint3-review"></a>

### sprint3 review

<details>
<summary>Read dated details</summary>

Source: `docs/SPRINT3_REVIEW.md`; input SHA-256 `686ff232fe200d1898807988eb171c3162e2a14c970932baf13e9443c0abf431`.

# Sprint 3 review


> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

15 October 2026 (Africa/Nairobi). Read directly from Jira board 34, sprint ID 3,
Ajiri Sprint 3, all nine issues AJ-8 through AJ-16. Jira reports this sprint as
future and Sprint 4 as active; no sprint or issue was changed. Source tested:
integration/checkpoint-3 at 5e15a11, isolated branch codex/sprint-3-evidence.

## Scope and acceptance

| Issue | Evidence / outcome | Remaining acceptance |
|---|---|---|
| AJ-8 GitHub hygiene | Earlier session configured protection, Dependabot and secret scanning; see ROADMAP_WORKING_PROMPTS.md | Current live settings not reverified this run; owner-scoped credentials cannot distinguish Michael from an agent |
| AJ-9 Password validation | Existing WP11, b792a9f; password regression suite included in fresh passing tests | Review; no forced resets |
| AJ-10 Throttling | Existing WP12, 89af1fa/f4e819f; fresh tests pass | Not fully done: LocMemCache is per-process; live proxy/hop/cache verification and shared-counter choice pending (THROTTLING.md) |
| AJ-11 Upload content | Existing WP13, 183b18b; spoof/empty/ZIP limits tested | Review; structural checks are not malware scanning |
| AJ-12 Deploy hardening | Existing WP14, 82d8931; tests and rollback in DEPLOY_SECURITY_VERIFICATION.md | Not done against Jira acceptance: Michael must verify production; no production action authorized |
| AJ-13 Refresh CSRF design | Existing WP15, fe656ff; REFRESH_COOKIE_CSRF_DESIGN.md | Michael's explicit design approval; no auth mitigation implemented |
| AJ-14 Scan / coverage | Executed and recorded in MODERNISATION_AUDIT.md below | Scan task complete; dependency remediation remains an open release risk |
| AJ-15 Backup / renewal | Manual checklist below | Blocked: production backup transfer and reminder not performed |
| AJ-16 Audit / planning | Existing MODERNISATION_AUDIT.md, CHECKPOINT3_PLAN.md, SMTP_EMAIL_DESIGN.md, DECISIONS_NEEDED.md; prior design approvals in chat | No new 3B implementation authorized |

Existing packages were merged --no-ff; do not recreate them or claim all nine issues
Done. Suggested sizing retains Jira's estimates (31 total); this evidence-only follow-up
is AJ-14's existing 2 points, not another implementation of 3A.

## Fresh verification

- Existing Python 3.12 virtualenv, installed pip-audit 2.10.1 and coverage 7.16.2;
  no new packages installed or requirement files changed by this run.
- `manage.py check`: no issues. `makemigrations --check --dry-run`: no changes.
- Coverage-wrapped full Django suite: 88 run, 87 pass, one Windows symlink skip.
  In-memory email, disposable test database/media; no provider or production call.
- Statement coverage: 1182 statements, 121 missed, 90%, excluding tests,
  migrations and upload fixtures. Branch coverage not measured. See audit for commands.
- `pip_audit -r requirements-prod.txt --progress-spinner off`: exit 1,
  15 advisories across two pinned packages. This is findings, not a tool failure.
- First sandbox attempts failed on temporary-file permissions; successful reruns
  used normal temporary-file access. No security check was bypassed.
- Documentation changes only: frontend install/lint/tests/build not rerun and
  frontend_build not regenerated. Previous 3A frontend results remain historical.

## Michael-only outstanding operations

1. Follow DEPLOY_SECURITY_VERIFICATION.md for AJ-12. Do not enable trusted proxy
   headers until the platform's header sanitation is verified. Confirm the short
   HSTS policy, redirects without loops, and cookies/headers; retain rollback steps.
2. For AJ-15, sign into PythonAnywhere privately. Locate the verified private backup
   described by DEPLOYMENT_CHECKLIST.md and confirm its date and contents. A historical
   backup alone does not protect newer production data; take a fresh backup manually
   if necessary using that checklist. Download DB and private-media backup through
   the authenticated dashboard to an encrypted, access-restricted local folder outside
   the repo and public/cloud-synced folders. Never attach it to Jira or chat.
3. Compare a SHA-256 digest on server and local copy (PowerShell:
   `Get-FileHash -Algorithm SHA256 -LiteralPath 'YOUR_PRIVATE_BACKUP_PATH'`).
   Rehearse integrity/restore against a disposable local copy; record only success
   and date, never data or credentials. Do not delete server backups as part of this step.
4. Recheck the web-app expiry in the dashboard; 14 November 2026 is historical,
   not newly verified. Set a private calendar reminder one week before the actual
   expiry and another two days before; renew manually and confirm the updated date.
   No calendar event or automation has been created by this run.

## Boundaries and handback

No app, dependency, migration, CI, hosting, auth or production changes. No pushes,
PR merges, Jira writes or 3B work. Preserve the original checkout's modified npm
lockfile and untracked coverage data. Review the audit findings and approve a separate
dependency-remediation scope before addressing them; no automatic audit fix.

## Approved follow-up — 15 October 2026

Michael confirmed the proposed remaining-task choices. AJ-10 now has an opt-in
private file-cache implementation and separate-process regression test; activation
and live proxy/worker verification remain pending. See THROTTLING.md. AJ-13 option C
is approved as a design only; no auth changes authorized by that acceptance.

Read-only production checks: authenticated Web dashboard confirms Python 3.12,
Force HTTPS enabled, no static mappings, expiry **14 November 2026**. Public HEAD
HTTP /login returns 302 to HTTPS; HTTPS /login returns 200, no redirect loop,
DENY frame policy, nosniff, same-origin referrer and no-store. **No HSTS header**
was returned: AJ-12 is not fully accepted. No reload, renewal or configuration edit
performed. Live cookie flags and trusted proxy hop/worker topology remain unverified;
no real account login or request-exhaustion probe performed.

AJ-15: authenticated directory listing confirms the verified-deploy backup folder
exists. Backup bytes were not opened or transferred; Michael must supply a private
local destination before download. Renewal reminder creation was rejected by automatic
approval review because exact persistent-automation authorization was unclear. No
reminder exists; request explicit approval for 7 and 12 November at 09:00 Africa/Nairobi.
Production verification authorization does not authorize a deployment to fix HSTS.

Fresh follow-up gates: backend check and migration check passed; **90 tests run,
89 passed, one Windows symlink skip**. Six targeted throttle tests passed, including
two new separate-process/configuration regressions. npm ci, lint, all 25 frontend
tests and build passed. Frontend source/lockfiles/build package unchanged; build was
a gate only. No regeneration or dependency upgrade needed. Suggested incremental
effort for the shared-cache follow-up: 2 points within AJ-10's existing estimate.

Proposed local backup destination: `C:\Users\micha\AjiriBackups`, outside the repo
and standard OneDrive folders. It does not exist yet. Drive encryption could not be
verified with the available local BitLocker cmdlet (absent). Before transferring
production data, Michael should confirm device encryption in Windows Settings and
approve an account-restricted folder (or encrypted removable storage). No backup
contents, .env or credentials were downloaded; no new backup was taken on production.

## Subsequent backup evidence and deployment readiness

Michael completed a fresh production backup at manual-20261015-181545 with writers
idle and ingestion paused, then re-enabled ingestion. The downloaded database and
revision hashes matched; browser-decompressed media matched the decompressed server
hash. Michael's local rehearsal verified all hashes, database integrity `ok`, and
restored 4 media files / 12,866 bytes into a disposable private directory. BitLocker
Protection On, recovery-key backup and account/SYSTEM/Administrators folder access
were confirmed by Michael. This supersedes the earlier backup-transfer blocker;
it is a basic restore rehearsal, not an authenticated application restore test.

On Michael's request to handle the remaining tasks, read-only server checks found:
clean tracked checkout at **2d5d175**, DEBUG=False, Django SSL redirect=False,
HSTS=0, proxy SSL header=None, secure session/CSRF cookies=True, no NUM_PROXIES
configuration and default LocMemCache. No server settings were changed or reloaded.

Remote main is **1ef6159**; frontend and all three backend CI checks passed. The
shared-cache commit b860658 is absent from remote main, so shared-cache activation
cannot proceed through the reviewed release path until Michael reviews/publishes
that change. No direct production patch, push, PR or main merge was attempted.

PythonAnywhere's current client-IP documentation guarantees the last X-Forwarded-For
item is the peer seen by its load balancer, but an application's additional upstream
proxy/CDN topology must be established before configuring NUM_PROXIES. Its Force HTTPS
documentation confirms host-level redirection; the consulted SSL-header material did
not establish the required X-Forwarded-Proto sanitation contract. Per
DEPLOY_SECURITY_VERIFICATION.md step 3, stop the HSTS/redirect rollout until that
contract or an appropriate native secure-scheme configuration is verified. Keep
Force HTTPS enabled; do not infer proxy trust from a passing synthetic test.

References: https://help.pythonanywhere.com/pages/WebAppClientIPAddresses/ and
https://help.pythonanywhere.com/pages/ForcingHTTPS/ .

Renewal automation creation was again rejected by automatic approval review as
insufficiently specific persistent-action authorization. No reminder exists. Exact
approval requested: reminders on 7 and 12 November 2026, 09:00 Africa/Nairobi, for
the 14 November expiry; no automatic renewal or production modification.

</details>

<a id="record-sprint3-release"></a>

### sprint3 release

<details>
<summary>Read dated details</summary>

Source: `docs/SPRINT3_RELEASE.md`; input SHA-256 `9a12fe5ad77f12b0f43da09e0de198fb99c0b39825e0da16144df746dcdf3440`.

# Sprint 3 release review and activation gates


Prepared on 15 October 2026 from remote main 1ef6159, branch
codex/sprint3-release-review. This contains only the shared-cache follow-up and
Sprint 3 evidence. No push, PR merge or production deployment is implied.

## Review change

Optional THROTTLE_CACHE_DIR selects a dedicated built-in FileBasedCache for
endpoint counters. Default caching and local behaviour remain unchanged.
Separate-process tests prove sequential workers consume the same budget.
Rates remain approximate under concurrent updates; do not use as an atomic quota.
No migrations, dependency changes, auth/cookie/CORS/ingestion or CI changes.
The existing frontend package matches the freshly built dist byte for byte.

## Required release sequence

1. Michael explicitly authorizes a push and PR for this branch; current AGENTS
   requires authorization for those exact GitHub actions. Michael reviews and
   merges only after frontend and Python 3.12/3.13/3.14 CI pass. No agent merge.
2. Record the resulting reviewed main SHA; do not deploy the local branch tip or
   silently substitute a newer revision. Reconfirm clean server checkout and retain
   current production SHA 2d5d175 for rollback.
3. Reconfirm the backup window: verified manual-20261015-181545 snapshot and restore
   rehearsal exist, but any subsequent writes require a fresh backup before cutover.
   Pause writers using the existing maintenance procedure. No credential files in chat.
4. Stage the approved code with no traffic activation, run check and migrate --plan.
   No new migration is expected from this change. Stop on an unexpected plan.
   Complete the approved migrations before reloading new code.
5. Create /home/Mathenge/ajiri-throttle-cache as a dedicated private 0700 directory,
   owned by the web-app account, outside repository/media/static/backup mappings.
   Confirm shared filesystem visibility and writable access for all actual workers.
   Set THROTTLE_CACHE_DIR to that directory privately; no new credentials required.
6. Resolve the HTTPS scheme gate below before enabling Django redirect/HSTS.
   Retain host Force HTTPS throughout. If unresolved, do not activate redirect defaults;
   explicitly retain SECURE_SSL_REDIRECT=False and SECURE_HSTS_SECONDS=0.
7. After scheme verification, enable redirect and HSTS max-age 300, with no preload
   or includeSubDomains; retain secure cookies and standard headers. Reload only
   after all preceding gates pass. Verify no HTTPS loop, forged-proto behaviour,
   private URLs blocked, owner downloads and one normal ingestion run. No live
   password guessing or quota-exhaustion tests.

## HTTPS scheme gate

Django normally derives scheme from WSGI `wsgi.url_scheme`; if the host supplies it
correctly, no forwarded-header trust override is needed. If a proxy header is used,
its sanitation/overwrite guarantee must be established first. Synthetic local
RequestFactory tests cannot prove the live host contract. Do not set arbitrary
client headers as proof, or add a public diagnostic endpoint exposing request data.

Michael can send this focused question to PythonAnywhere support (not sent by Codex):

> For my free-tier Django web app with Force HTTPS enabled, does your WSGI layer
> supply wsgi.url_scheme=https on external HTTPS requests? If X-Forwarded-Proto is
> needed instead, do your proxies strip/overwrite all client-supplied occurrences,
> including comma-separated values? Can external callers bypass that proxy? What
> worker/shared-filesystem guarantees apply to a private file cache under my home?

Use the confirmed native scheme where available. Otherwise choose proxy trust only
after assurance and adversarial HTTPS/HTTP header tests. For IP throttles, the host
guarantees only the rightmost X-Forwarded-For peer; confirm whether a separate CDN
or proxy exists before selecting NUM_PROXIES. Do not expose client addresses in logs.

Sources: https://docs.djangoproject.com/en/6.1/ref/settings/#secure-proxy-ssl-header
and https://help.pythonanywhere.com/pages/WebAppClientIPAddresses/ .

## Rollback

Keep Force HTTPS and private media mappings intact. If redirects loop, set Django
redirect=False and HSTS=0 through the existing private configuration, restore the
previous verified proxy-trust configuration/reviewed revision, then reload. Existing
300-second HSTS policies may persist until expiry; HTTPS must remain available.
Unsetting THROTTLE_CACHE_DIR restores process-local counters and resets budgets;
record reduced cross-worker protection. Do not delete cache/DB/media or restore an
old DB over new writes as a routine rollback. Preserve all backups.

## Local verification of the release-review branch

On the branch based on main 1ef6159: backend check and migration check pass;
90 tests run, 89 pass and one Windows symlink privilege skip. Frontend npm ci,
lint, 25 component tests and build pass with the merged main lockfile. System
Node 22.15 emits engine warnings for updated transitive dependencies; use a
supported runtime (Node >=22.22.2 in the 22 line, or the installed 24.19 runtime).
No dependency pin or lockfile was changed to work around this. Exact dist versus
committed frontend_build bytes matched; the committed build was not regenerated.
No production activation or new live verification is claimed by these local tests.

</details>

<a id="record-phase-a-deployment"></a>

### phase a deployment

<details>
<summary>Read dated details</summary>

Source: `docs/PHASE_A_DEPLOYMENT.md`; input SHA-256 `5f5dd2e8c5d8cba4e1957a4cb2931b8d1c2c0b0c5e754caa1f5c921ca7779578`.

# Phase A future release — Michael's server steps and rollback


Stage A at c4b9364 is owner-confirmed deployed on 16 October 2026. This runbook
does NOT deploy anything now. Phase A remains local and requires review, an exact
release SHA, authorized publication, passing CI and a separate deployment decision.
Do not substitute the current local integration tip for Michael's deployed SHA.
Stage B remains independent: keep Django redirect=False and HSTS=0 pending the
PythonAnywhere scheme answer. Preserve host Force HTTPS and all private mappings.

## WP16 release impact

WP16 changes documentation/evidence only; no dependency pins changed from c4b9364.
It requires no new migration, service or pip-audit installation on production.
If production already installed c4b9364's requirements, no additional upgrade is
needed for WP16. A future combined Phase A release still checks the actual venv
and installs the reviewed production requirements when necessary. Do not install
development requirements or scanners on the free-tier server for this release.

## Preflight and backup — before changing code or the active venv

In PythonAnywhere Bash, Michael runs:

```bash
cd /home/Mathenge/ajiri
workon ajiri
git status --short
git rev-parse HEAD
python --version
python -m pip --version
python -m pip check
python -c "from importlib.metadata import version; print('Django', version('Django')); print('PyJWT', version('PyJWT'))"
```

Require a clean checkout and expected current release c4b9364, Python 3.12 and the
ajiri virtualenv. Expected pinned versions: Django 6.1.2 and PyJWT 2.15.1. Stop on
unexpected versions/errors; do not silently downgrade or repair live dependencies.
Record the current full code SHA and non-sensitive package versions privately.
Verify backup freshness; pause writers and take/verify DB and private-media backups
using the existing DEPLOYMENT_CHECKLIST.md procedure, including off-server hashes
and isolated restore verification. The new WP22 command is not available on c4b9364.

If an actual package change is required, preserve a known-good environment before
touching the active one. If space cannot hold that recovery copy, stop and arrange
a reviewed recovery plan; never delete backups to make room. Unexpected dependency
drift requires review rather than a blind install on the serving venv.

## Stage the separately approved release, check dependencies, then activate

Only after review/publication/CI, replace the placeholder with that exact approved
SHA (not a floating main reference). No command here merges or pushes:

```bash
cd /home/Mathenge/ajiri
RELEASE_SHA='REPLACE_WITH_REVIEWED_FULL_PHASE_A_SHA'
git fetch origin
git rev-parse --verify "${RELEASE_SHA}^{commit}"
git merge-base --is-ancestor c4b9364 "$RELEASE_SHA"
git diff --name-only c4b9364 "$RELEASE_SHA" -- '*migrations*' '*requirements*'
```

Stop unless ancestry succeeds and no unexpected migration/requirement change is
present. Pause HTTP callers/writers using the owner's maintenance procedure before
switching the serving checkout or changing its venv; a worker restart can load new
files before an explicit reload. Do not rely on reload alone as a staging barrier.

```bash
git switch --detach "$RELEASE_SHA"
cd /home/Mathenge/ajiri/ajiri-backend
workon ajiri
python -m pip install --requirement requirements-prod.txt
python -m pip check
python -c "from importlib.metadata import version; print('Django', version('Django')); print('PyJWT', version('PyJWT'))"
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
```

The pip command is reconciliation to existing reviewed pins, not an unbounded
upgrade. Expect Django 6.1.2/PyJWT 2.15.1 and no new Phase A migration. Stop on
unexpected plans or failures. If already-current history has no pending operations,
`python manage.py migrate --noinput` is a no-op; otherwise obtain review first.
Do not add a Phase B migration to this release.

Privately configure exact `CSRF_TRUSTED_ORIGINS=https://mathenge.pythonanywhere.com`
for WP18's same-origin browser flow; do not expand CORS or trust proxy headers
without the host guarantee. Keep current redirect/HSTS-off values. Existing Secure
cookies remain enabled. CSRF origin validation needs the canonical HTTPS origin
even while the server's scheme handling is awaiting clarification.

Verify the existing throttle directory and create the private logging directory:

```bash
umask 077
mkdir -p /home/Mathenge/ajiri-private-logs
chmod 700 /home/Mathenge/ajiri-private-logs
stat -c '%U %a %n' /home/Mathenge/ajiri-private-logs
```

Expect owner Mathenge, mode 700; ensure no ancestor/link/static mapping exposes it.
Set PRIVATE_LOG_DIR to this path privately. Keep console mail unchanged. Reload
only after all preceding gates pass; resume callers after smoke checks.

Verify health GET/HEAD and no-store; CSRF bootstrap and rejected tokenless mutation;
login, refresh, logout, profile save, owner downloads, blocked direct media and
one normal ingestion run. Reload old browser tabs so server/client contracts match.
Check for unexpected redirect loops and private-log permissions/disk quota. Do not
deliberately break the production DB or exhaust production throttles. Follow the
Phase A review manual script and MONITORING_RUNBOOK.md. After release, rehearse
WP22 dry-run and isolated restore as documented in BACKUP_ROUTINE.md.

## Rollback

1. Pause callers/writers; preserve new DB writes, private files and diagnostic logs.
2. Restore the recorded known-good c4b9364 code/client/build as a pair:

   ```bash
   cd /home/Mathenge/ajiri
   git switch --detach c4b93647f65618e8d13f9baa47ded6d22a28f0fb
   cd ajiri-backend
   workon ajiri
   python -m pip install --requirement requirements-prod.txt
   python -m pip check
   python manage.py check
   ```

   Phase A and c4b9364 pins are identical: this does not roll back to vulnerable
   historical Django/PyJWT pins. If the venv is damaged, use the retained known-good
   environment/reviewed recovery plan; do not improvise dependency downgrades.
3. Restore reviewed prior non-secret configuration as needed, keeping shared cache,
   private media, host HTTPS and redirect=False/HSTS=0. Never disable WP18 CSRF on
   new code alone: roll back server and frontend together and reload old tabs.
4. Reload, verify login/download/privacy and normal ingestion, then resume callers.
   No Phase A schema reversal or routine old-DB restore is needed. Preserve backups;
   never overwrite newer writes with the pre-deployment database as routine rollback.

</details>

<a id="record-decisions-pending-2026-10-31"></a>

### decisions pending 2026 10 31

<details>
<summary>Read dated details</summary>

Source: `docs/archive/DECISIONS_PENDING_2026-10-31.md`; input SHA-256 `cbcf6d61ef133af6830c2c9832e67c70ad1a3654afef9661d14bf6e10c3db7c8`.

# Decisions pending — 31 October 2026

Implementation choices below are reversible defaults, not activation approval.
No deployment, production migration, runtime flag changes, live recipient mail,
Daraja calls, charging, real-account export/erasure or retention pruning is authorized.

| Item | Options | Default chosen | Impact / final decision |
|---|---|---|---|
| Account security mail | Owner pilot only; general transactional security mail | Separate default-off ACCOUNT_SECURITY_EMAIL_ENABLED and account_security delivery mode | Existing pilot preserved. General verification/reset uses current active mailbox and existing 30-account/200-total Nairobi-day budgets; provider/legal/operational activation remains pending. |
| Employer/public vacancy path AJ-53/AJ-42 | Publish synthetic vacancies; require genuine reviewed source | Retain independent review and strict current-evidence checks | Genuine organisation/listing evidence remains external; no fabricated inventory or freshness relaxation. |
| Certificates AJ-79 | PDF; images; office formats | PDF, 5 MiB/file, five files/20 MiB, owner only, quarantine required | Existing AJ-79 reused rather than duplicate ticket. No automatic employer sharing; scanner/capacity/retention activation pending. |
| AJ-17/26/43 delivery | Direct backend bypass; shared ledger | Shared ledger, consent and immutable application authorization | Unknown handoffs cannot auto-retry; no real inbox acceptance claimed. |
| AJ-51 analytics | External SDK; first-party aggregate collection | Default-off first-party allowlisted aggregates, no identifiers in events | Purpose, choice wording, lawful basis and retention require final factual decisions. |
| AJ-52 scanner | External upload service; self-hosted ClamAV | Private fail-closed scanner boundary | Hosting/signature freshness/resource capacity need real evidence; content validation is not malware scanning. |
| AJ-47/48 infrastructure | Production switch now; inactive durable integration | No storage/broker switch | Actual target access, isolated restore and host durability remain prerequisites. |
| AJ-44/45/46 commerce | Invent prices/merchant terms; hold pending | No charging or paid entitlement activation | Merchant/product/legal facts cannot be inferred. Free browsing/applying/existing documents preserved. |
| 23 Update tickets AJ-54–AJ-76 | Delete; rename/resolve after provenance review | Proposal only, preserve all issue history/statuses | Inspect comments/links before suggesting specific merges or replacements. |
| Jira dry run | Execute sync; prepare reviewable inputs | Do not execute tools/jira_sync.py per AGENTS.md section 13 | Provide commands and validated JSON; no fabricated dry-run execution output. |

</details>

<a id="record-deployment-checkpoint2"></a>

### deployment checkpoint2

<details>
<summary>Read dated details</summary>

Source: `docs/archive/DEPLOYMENT_CHECKLIST_CHECKPOINT2.md`; input SHA-256 `0757513c619f486fa8ba4571f3b6db17b09c299d4f29f79202c4344112b7a408`.

> Historical Checkpoint 2 checklist, archived 21 October 2026. Use [the current release checklist](../docs/DEPLOYMENT_CHECKLIST.md) for operations. Original text follows unchanged.

# PythonAnywhere Checkpoint 2 deployment checklist

**Michael performs these steps manually after reviewing and approving Checkpoint 2.**
Nothing here has been deployed by Codex. Do not deploy an unreviewed feature tip.
Use Python 3.12 locally and on PythonAnywhere; CI keeps 3.12/3.13/3.14.
This checklist supersedes older instructions to expose `/media/` publicly.

## 1. Review and prepare

- [ ] Review `CHECKPOINT2_REVIEW.md`, the approved private-media design, and actual
  CI results on a pull request. Approve/merge the selected revision yourself.
- [ ] Record the approved revision, previous deployment revision, effective DB
  path, previous MEDIA_ROOT and all Web → Static files mappings privately.
- [ ] Verify your backup restore procedure, available disk quota (copies plus
  backups), the current Python 3.12 virtualenv and web worker account.
- [ ] Choose a maintenance window and recovery owner. Pause uploads, application
  preparation/sending, ingestion/sweep callers and any Celery workers/Beat. Pause
  scheduled GitHub Actions from the dashboard if they target this deployment.
  Use the site's existing maintenance procedure. Do not continue if writers remain.
- [ ] Save a known legacy uploaded-CV URL and both application-document URLs for
  your own test account privately; these are sensitive. Prepare a second test user
  and a synthetic job/employer target. Never send a test to a real employer.

## 2. Back up before migrations or mapping changes

- [ ] In the PythonAnywhere **Bash** console, replace account/timestamp below.
  These variables must point at your verified deployment, not a guessed folder:

```bash
cd /home/YOURNAME/ajiri/ajiri-backend
workon ajiri
python --version
umask 077
OLD=/home/YOURNAME/ajiri/ajiri-backend/media
NEW=/home/YOURNAME/ajiri-private-media
AUDIT=/home/YOURNAME/ajiri-private-backups/checkpoint2-YYYYMMDD-HHMMSS
export AUDIT
test -d "$OLD" || exit 1
test -f db.sqlite3 || exit 1
mkdir -m 700 -p "$NEW" "$AUDIT"
chmod 700 "$NEW" "$AUDIT"
realpath "$OLD" "$NEW" "$AUDIT"
```

- [ ] Require Python 3.12. Check all resolved paths against the mapping table.
  Do not use chmod 777 or place private paths beneath any mapped directory.
- [ ] Back up the actual SQLite DB using its backup API (handles WAL contents),
  plus the full media tree and environment. Do not overwrite a previous backup.
  If your DB is not `db.sqlite3`, substitute its verified path before executing:

```bash
python -c 'import os, sqlite3; from pathlib import Path; src=sqlite3.connect("file:db.sqlite3?mode=ro", uri=True); dst=sqlite3.connect(str(Path(os.environ["AUDIT"])/"db.sqlite3")); src.backup(dst); result=dst.execute("PRAGMA integrity_check").fetchone()[0]; dst.close(); src.close(); assert result == "ok", result'
tar -czf "$AUDIT/media.tar.gz" -C "$OLD" .
tar -tzf "$AUDIT/media.tar.gz" >/dev/null
git rev-parse HEAD > "$AUDIT/previous-revision.txt"
if test -f .env; then cp -p .env "$AUDIT/environment.backup"; chmod 600 "$AUDIT/environment.backup"; fi
```

- [ ] Stop on any nonzero exit. Verify a restore to a separate private directory
  and inspect the restored database's integrity before changing live data. Record
  totals and checksums privately. No backups/manifests/environment files enter Git.

- [ ] Recovery gate: if backup integrity or restore rehearsal fails, stop before
  staging code, migration, relocation or mapping changes. Keep the original DB
  and files in place and correct the backup problem first.

## 3. Stage approved code, then migrate before activating it

```bash
cd /home/YOURNAME/ajiri
git status --short
git fetch origin
git switch --detach APPROVED_COMMIT
cd ajiri-backend
python manage.py check
python manage.py showmigrations jobs
python manage.py migrate --plan
```

- [ ] Do not switch with unexplained working changes. Replace APPROVED_COMMIT
  with the reviewed revision. Keep the web app in maintenance and do not reload
  into the new code yet. Staging code on disk precedes running its migration tools;
  **database migrations precede activation/reload**.
- [ ] Review the plan. Checkpoint 1 introduced `jobs/0007_notification_in_app`:
  existing notification rows default to in-app visibility. If absent it must be
  applied before the new code handles requests. WP7/WP8 add no migration.
- [ ] Stop if the plan includes unexpected or destructive migrations. Once the
  backed-up plan is approved, run:

```bash
python manage.py migrate --noinput
python manage.py showmigrations jobs
```

- [ ] Confirm `[X] 0007_notification_in_app` and all expected migrations applied.
  Do not edit migration history or reverse 0007 as a routine rollback. Auth/CORS,
  cookie settings, ingestion keys and the auth client remain unchanged.

- [ ] Migration recovery gate: on failure, keep maintenance in place and inspect
  the migration state and verified backup. Do not reload new code or automatically
  reverse migrations/restore the DB; use the reviewed recovery decision in section 7.

## 4. Relocate media while writers remain paused

The implemented command copies regular files, preserves all relative names and
bytes, and never deletes originals or updates DB rows. It includes unreferenced
files as private copies, rejects unsafe paths/symlinks/junctions, missing referenced
files and conflicting destinations, and resumes safely over identical files.
Dry-run is the default and writes nothing, including no manifest file.

```bash
python manage.py relocate_private_media --help
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --dry-run
```

- [ ] Review counts, missing references, destination safety, permissions and disk
  quota. Resolve every error before applying; never replace a missing snapshot
  with an empty file or regenerate a user's approved application.
- [ ] Run the copy with a fresh manifest path, then verify the complete source
  inventory and current references:

```bash
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --apply --manifest "$AUDIT/relocation.json"
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --verify
```

- [ ] Require exit 0, matching totals and verified hashes. Inspect the private
  manifest's copied/already-identical counts. If apply was interrupted, keep
  maintenance in place, fix the cause and rerun with a new manifest filename.
  Existing identical destination files are accepted; conflicts are never renamed
  or overwritten. The source is still intact. Manifests may contain personal names.
- [ ] Set `PRIVATE_MEDIA_ROOT=/home/YOURNAME/ajiri-private-media` in the existing
  private server configuration mechanism, usually `.env` beside manage.py.
  Real process environment overrides `.env`; confirm the effective root without
  printing secrets. Keep DEBUG=False and `.env` at 0600.
- [ ] Verify NEW directories are 0700 and files 0600 and the web account can
  read/write them. Verify newly created files receive these permissions too.
  The command sets copy permissions; Windows testing does not establish Linux
  permission enforcement. Never add a public mapping to fix a permissions error.

- [ ] Relocation recovery gate: if copy/verification fails, leave OLD intact and
  keep writers paused. Do not switch the root or reload. Correct the cause and
  rerun the safe copy, or stop cutover and retain the previous revision/root.

## 4a. Remove public media mappings before reload

- [ ] In PythonAnywhere **Web → Static files**, remove `/media/` and every alias
  or parent mapping that can expose old media, private media, backups or manifests.
  Retain public assets only. Do not map the whole repository or home folder.
- [ ] Keep all writers and public traffic paused. Mapping changes become effective
  on the platform reload below. Do not resume traffic while old public URLs work.
  If any alias cannot be removed, stop cutover and keep maintenance in place;
  application permissions cannot override platform mappings. Never restore a
  public mapping as rollback (see section 7).

## 5. Activate and verify before restoring traffic

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
```

- [ ] Use **Web → Reload** only after migration, relocation and configuration
  checks pass. Keep maintenance until the checks below pass.
- [ ] Repeat anonymous and signed-in GET/HEAD tests against all known old media
  URLs, aliases and hostnames with browser cache disabled. No private bytes may
  be served; `/media/` must not fall through to an SPA 200. Previously downloaded
  browser/proxy copies cannot be revoked by this deployment.
- [ ] Owner can download uploaded CV, saved CV and saved letter through their
  existing API endpoints. Check original bytes/filenames and private/no-store
  headers. Another user's snapshot request is 404; anonymous requests are 401.
- [ ] Upload a synthetic PDF/DOC/DOCX, prepare a synthetic application and download
  its snapshots. Verify new files appear only in NEW. Existing snapshot bytes
  remain unchanged after editing the profile. Fresh generators still work.
- [ ] Use captured/console email in a separate local or staging environment to
  run the double-send review below; do not change production mail settings just
  for this test. Inspect live error logs privately for storage/permission failures.
- [ ] Public static assets, login/refresh/logout, jobs, preferences and alerts
  still work. The existing frontend_build is unchanged.
- [ ] Recheck every static mapping, then resume traffic and paused callers.
  Keep OLD, the backup, and audit manifests private until an agreed retention
  review. No automated deletion/cleanup is introduced by this checkpoint.

- [ ] Activation recovery gate: any failed privacy/download/health check blocks
  resuming traffic. Keep mappings removed; restore the recorded revision/root only
  as described in section 7, preserving any new writes. Never fix a failed owner
  download by restoring a public mapping.
- [ ] After activation and privacy/health checks pass, resume exactly one scheduled
  ingestion run from the existing GitHub Actions workflow. Check its Actions result,
  HTTP success and expected job/no-duplicate outcome; then resume the normal
  schedule. No ingestion code/key changes are needed. A failed run blocks declaring
  deployment verified; inspect private logs without exposing X-Ingest-Key.

## 6. Local double-send verification (PowerShell)

Run the deterministic overlapping-request test, using only its synthetic DB,
temporary attachments and captured email. No server or real account is needed:

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py test jobs.test_send_concurrency --noinput
```

Expected: three tests pass. One test blocks request A at delivery while request B
tries to send with a stale ready-state read. B must receive 400; after A is released,
A receives 200 and exactly one email with saved attachments exists. A failure test
requires 502, restores ready_for_review with no timestamp, then a retry sends once.
A stale dismiss cannot overwrite the send claim. `sent` is visible while delivery
is pending; no new status or schema was introduced.

For a UI check in a captured-mail local environment, prepare a fresh synthetic
email application, open it in two signed-in tabs, approve both drafts, and trigger
send in both. Expect one success, one 400, and one captured message. Repeat with
another synthetic application if both tabs were not ready before the first send.
The automated test is the reliable overlap proof; manual tab timing alone is not.

## 7. Rollback without restoring the privacy leak

- [ ] Keep writers paused and mappings removed if any acceptance check fails.
  Do not restore `/media/`, a parent alias, or DEBUG media serving.
- [ ] Before any new writes, revert application revision/root setting to the
  recorded previous state so endpoints read intact OLD, then reload and verify
  owner access. Keep production DEBUG=False. 0007 is additive and normally stays.
- [ ] After new writes, preserve them: reconcile NEW into the old **unmapped**
  root with explicit inventory/hash/conflict review, or fix forward with NEW.
  Do not blindly copy over conflicts or restore an old DB over new user records.
- [ ] Database restoration, migration reversal, data deletion and source cleanup
  require a separate reviewed recovery decision. Recover from verified backups
  only while maintenance is in force; protect environment secrets throughout.
- [ ] Recheck privacy and owner downloads before resuming traffic. Document the
  outcome and retain audit evidence privately.

SMTP ambiguity is a separate recovery case: after a process crash or lost provider
acknowledgement, a claimed application can remain sent even if delivery is uncertain.
Check provider/server evidence manually before any reset/retry. No automatic reset
or exactly-once SMTP guarantee is provided; a server may accept email then raise.

</details>

<a id="record-roadmap-next-actions-2026-10-26"></a>

### roadmap next actions 2026 10 26

<details>
<summary>Read dated details</summary>

Source: `docs/archive/ROADMAP_NEXT_ACTIONS_2026-10-26.md`; input SHA-256 `68c48c7a680a4f12c5215f6514f7da72e38a5747e95a9a534fbca84db7410106`.

# Remaining roadmap: 26 October 2026

The previous live Jira reconciliation returned12 unfinished non-Epic issues with no next page.
AJ49 (reasoned moderation) and AJ50 (pipeline first scope) are now Done with deployed
evidence. This list distinguishes tested implementation from missing live acceptance.
No test provider is a live service. PR51 preparation and PR52 moderation are
deployed; PR53/54 offline contracts are included in verified release b6cc6af.
The final local suite passed467 tests (one platform skip), all six CI checks passed
for each PR, and production source/build/health checks passed. No analytics,
scanner, financial service or broader sending was activated. Use JIRA_ROADMAP_PROGRESS.md for actual revisions.

| Issue | Existing evidence | Next concrete boundary |
|---|---|---|
| AJ17 application/alert delivery | Shared ledger, exact approval/authorization and completed25October owner application inbox/content check; Brevo Delivered and one accepted receipt | Pilot flag switched OFF and reloaded afterwards. Broader delivery still needs its scoped consent/provider/privacy and operational gates. |
| AJ26 notification email | Explicit choice/revocation and owner synthetic inbox/unsubscribe proof | Normal production transport/eligibility and bounded live acceptance remain gated. Earlier enabled preferences do not grant new consent. |
| AJ42 public jobs | Public templates/sitemap/metadata and strict freshness tests | Anonymous publication flag remains off; confirm publication/source evidence and release eligibility. Never publish unknown or stale jobs just to populate search. |
| AJ43 saved searches | Deployed owner queries, frequency windows, in-app integration and captured email contract | Real saved-search email transport/consent/budget acceptance remains pending. Saving alone does not opt into mail. |
| AJ44-46 payments/entitlements | Offline synthetic checkout/status/reconciliation contract and expiry/refund cases | Merchant ownership, real sandbox access, commercial/refund/tax/privacy terms, durable financial evidence and verified adapters. No transaction or premium upgrade is authorized by a fake callback. |
| AJ47 storage migration | PR56 deployed fixture-restore fix; actual synthetic PostgreSQL rehearsal preserved161 rows/34models/four files and26October controlled rollback/resume passed | Historical PostgreSQL schema/bootstrap/search strategy, object-storage privacy, host/storage-failure recovery and actual production target remain unverified. See STORAGE_MIGRATION_REHEARSAL.md. No cutover. |
| AJ48 queue | Inline executor plus real isolated worker/broker-process crash recovery and uncertain captured-IO receipt reuse | Host/disk-loss recovery, actual production broker/worker, real provider uncertainty reconciliation and dead-letter operations remain unverified. See QUEUE_BROKER_REHEARSAL.md. The free WSGI app is not proof of an always-on worker. |
| AJ51 analytics | Merged memory-only independent-choice/aggregate contract | Actual purpose, consent wording/schema, retention/cohort/report-access and provider/legal decisions; no production collection yet. |
| AJ52 scanning | Memory quarantine contract plus actual offline ClamAV/custom harmless-signature rehearsal | Vendor-definition freshness/coverage, durable private quarantine, actual host/processing authorization and legacy-file policy remain open. Existing uploads are not malware-scanned. See SCANNER_ENGINE_REHEARSAL.md. |
| AJ53 employer posting | Deployed expiry/evidence, owner dashboard and independent staff review | General employer verification/onboarding beyond owner-only security mail, plus genuine organisation/listing review. No real employer was approved by Codex. |

The owner may enter credentials only through the actual approved service privately.
No purchase, legal acceptance, personal consent, irreversible deletion or live
financial transaction is inferred from the implementation request. Routine backups
remain automated where access is available, with verified off-server copies and
isolated restoration; retention stays report-only. Hosting renewal is still due
before19 November2026. Account quota was427.9/512MB after the latest release backup;
no retained backup has been deleted. A concrete pruning policy needs its own decision.

## Showcase-first order confirmed 26 October

PythonAnywhere is selected now; retain SQLite/private media for the showcase.
Finish the public introduction, accessible CV entry point and honest employer guide,
then demonstrate registration through approved CV download. Follow
SHOWCASE_RELEASE.md (historical path: `SHOWCASE_RELEASE.md`) and
EMPLOYER_REVIEW_PLAN.md (historical path: `EMPLOYER_REVIEW_PLAN.md`). No unknown/stale jobs are reactivated.
General employer onboarding needs verified account mail and a genuine independent
organisation/listing review; it is not established by synthetic tests. Daraja and
commercial decisions are deferred to the end. Broader sending/scanning/queue services
remain gated and are not prerequisites for a truthful CV showcase.

The 26 October scheduled backup completed with an off-server copy and isolated
17-file restore. Account quota was457.9/512MB after it; retention remains report-only.

</details>

<a id="record-backend-readme-pre-first-release"></a>

### backend readme pre first release

<details>
<summary>Read dated details</summary>

Source: `ajiri-backend/docs/archive/README_PRE_FIRST_RELEASE.md`; input SHA-256 `56407f81232f63f8f0aaef582eb8680bc081991fbb27fdb53f83ae3af32a755b`.

# Ajiri Backend

Django REST API backend for Ajiri (ajiri.co.ke) — a Kenyan job-finding platform.

**Status:** In development. Deployment-ready (free-tier PythonAnywhere runbook written and rehearsed locally), not yet live. Private repo.

**Completed phases:** Identity & Access ✅ · User Profile ✅ · Job Pipeline ✅ · Job Discovery ✅ · CV Upload ✅ · Automated CV Formatting ✅ · Automated Cover Letter Generation ✅ · Auto-Apply ✅ · Job Alerts (email + in-app) ✅ · React frontend (walking skeleton) ✅ · Remote ingestion + deployment prep ✅
**Current phase:** First deployment — follow `DEPLOY_PYTHONANYWHERE.md` (historical path: `DEPLOY_PYTHONANYWHERE.md`)

---

## Stack

- Python 3.12 locally (checks and tests also pass on 3.13, which PythonAnywhere runs, and 3.14)
- Django 6.1
- Django REST Framework 3.18 + SimpleJWT (JWT auth) + django-filter (query filtering)
- React + Vite frontend in the sibling `ajiri-frontend/` folder; its production build is committed in `frontend_build/` and served by Django through WhiteNoise (one origin, no CORS in production)
- Celery 5.6 + Redis (Docker container `ajiri-redis`) — **local development only**; production runs the same jobs from GitHub Actions
- GitHub Actions — CI (`ci.yml`) plus scheduled ingestion and match sweep (`ingest.yml`, `sweep.yml`)
- feedparser — RSS ingestion
- python-docx — generates CVs and cover letters as real .docx files from structured profile/job data
- python-dotenv — loads the git-ignored `.env` file; WhiteNoise — serves static files and the React build
- SQLite (local, and the free-tier deploy) — move to Postgres if the free tier is outgrown
- Windows / PowerShell dev environment
- Docker Desktop (for Redis only, and only if you run Celery locally)

---

## Prerequisites

- Python 3.12 installed and available as `py -3.12`
- Node.js (for the frontend)
- Git
- Docker Desktop (only if you want Redis/Celery locally)
- PyCharm (or any editor)

---

## First-time setup

Clone the repo (it holds both apps, `ajiri-backend/` and `ajiri-frontend/`; see the repository layout under "Project structure"), then from `ajiri-backend/` (the folder with `manage.py`):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`requirements.txt` is the development set (runtime packages plus IDE type stubs). The server installs the smaller `requirements-prod.txt`.

`.env` is git-ignored. The example already sets `DEBUG=True`, which is all local development needs. With `DEBUG` off and no `SECRET_KEY`, settings refuse to load — by design, so a misconfigured server fails loudly instead of running insecurely.

Apply database migrations and create an admin account:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

You'll be prompted for **email** (not username) and a password — this project uses a custom User model with email-based login.

Run the tests:

```powershell
python manage.py test
```

Optional — Redis for running Celery locally (only needs to be created once — after that, just start it):

```powershell
docker run -d --name ajiri-redis -p 6379:6379 redis:latest
```

---

## Every time you come back to work on this

Only the first two are needed for everyday work; each in its own terminal tab:

```powershell
# 1. Django dev server
cd ajiri-backend
.venv\Scripts\activate
python manage.py runserver

# 2. React dev server (talks to Django at http://127.0.0.1:8000 via ajiri-frontend/.env.development)
cd ajiri-frontend
npm run dev
```

Only if you want to run ingestion locally through Celery:

```powershell
docker start ajiri-redis
python -m celery -A config worker --loglevel=info --pool=solo
python -m celery -A config beat --loglevel=info
```

(`python -m celery` rather than bare `celery`: a virtualenv's `.exe` launchers hard-code its original path and break if the folder is ever moved.)

If you pulled new code that changed `models.py` anywhere, also run `python manage.py migrate`.

**Before every `git commit`, run `git branch` first** to confirm you're on the feature branch you think you're on — this project has repeatedly (accidentally) committed feature work straight to `main` because a branch switch got lost mid-session after a debugging detour. Not catastrophic solo, but worth the 2-second habit.

---

## Project structure

One git repository holds the whole project. The repository root is the folder *above* this one:

```
ajiri.co.ke/               # repository root (clone the repo into a folder with this name)
├── .github/workflows/     # ci.yml (backend + frontend checks), ingest.yml + sweep.yml (scheduled calls to the production API)
├── CLAUDE.md, SETUP.md    # rules for AI assistants; first-time setup
├── ajiri-frontend/        # React + Vite app
└── ajiri-backend/         # this Django project, described below
```

```
ajiri-backend/
├── config/            # Project settings, URL routing, Celery app config
│   ├── settings.py    # Environment-driven (.env); fail-safe defaults
│   ├── celery.py      # Celery app instance, autodiscovers tasks.py in every app
│   ├── urls.py        # API/admin routes, then a catch-all that serves the React app
│   └── views.py       # The catch-all view (index.html for client-side routes)
├── accounts/          # Custom User model (email, phone_number, full_name), JWT auth
├── profiles/          # Profile + Skill models, CV upload, CV generation
│   ├── cv_generator.py    # Generates a .docx CV from structured Profile data
│   └── serializers.py     # Note: full_name/phone_number live on User, not Profile —
│                           # see "Key architectural decisions" below for the read/write split
├── jobs/               # Job, Application, Notification; RSS ingestion; scam filter; Discovery API; cover letters
│   ├── ingestion.py           # ingest_feed(feed) processes a parsed feed; ingest_myjobmag_kenya() fetches then calls it
│   ├── scam_filter.py         # Rule-based red-flag detection
│   ├── matching.py             # Match percentage, match alerts, and the periodic sweep
│   ├── filters.py              # django-filter FilterSet (location/job_type/skill)
│   ├── cover_letter_generator.py  # Generates a tailored .docx cover letter per job
│   ├── utils.py                # Application-method detection, fix_mojibake()
│   ├── management/commands/    # fix_mojibake: one-off repair of mis-decoded text
│   └── tasks.py                # Celery task wrappers (local development)
├── deploy/             # WSGI file template for PythonAnywhere
├── scripts/            # build_frontend.ps1: builds the React app into frontend_build/
├── frontend_build/     # Committed production build of ajiri-frontend, served by Django
├── docs/
│   ├── README.md       # This file
│   ├── DEPLOY_PYTHONANYWHERE.md  # Step-by-step deployment runbook
│   ├── CONCEPTS.md     # Glossary of Django/DRF/React/git/DevOps concepts learned along the way
│   └── Github.md       # Notes on git push output, PR workflow
├── .env.example        # Template for the git-ignored .env
├── requirements.txt / requirements-prod.txt
├── manage.py
└── db.sqlite3          # Local dev database (not committed to git)
```

---

## Key architectural decisions

- **Custom User model (`accounts.User`)**: email login (required), phone_number and full_name both optional (`blank=True`). Set up before any real data existed.
- **`AUTH_USER_MODEL = 'accounts.User'`** in `config/settings.py` — load-bearing, do not remove.
- **Shared `Skill` model**: defined once in `profiles/models.py`, reused in `jobs/models.py`. This is what makes match-scoring possible across both CV/cover-letter generation and Discovery.
- **`full_name`/`phone_number` live on `User`, but are edited through the Profile API** — `ProfileSerializer` declares them as plain (non-`source=`) fields for reliable write behavior, and overrides `to_representation()` to explicitly pull the real values from `instance.user` on read. A dotted `source='user.full_name'` approach was tried first and silently dropped the fields from responses — avoid that pattern here.
- **CV and cover letter generation are template-based (python-docx), not AI-generated** — deliberate v1 choice: free, predictable, no external API dependency. Parsing an uploaded CV to auto-extract data, and AI-generated cover letter text, are both explicitly deferred to a "V2" phase (logged in Monday.com).
- **Cover letter tone is driven by `calculate_match_score()`** — the exact same function Discovery uses to show match percentages. Three tiers (≥75%, 40-74%, <40%) produce different opening-line language. One scoring function, reused everywhere match quality matters.
- **Match-scoring** (`jobs/matching.py`): percentage of a *job's* required skills that the profile has (not the other way around).
- **Scam filtering runs on ingestion**, not on read — checked once at creation time, cached on `is_flagged_scam`/`scam_flags`.
- **Discovery, CV generation, and cover letter generation all require authentication** — no anonymous access anywhere in this API by design.
- **Applications are created on demand, never automatically.** Clicking Apply generates the CV and cover letter once, snapshots the job's application method, and stores an `Application` for review; nothing is sent until the user confirms. Email-method jobs send a real email with both files attached; link-method jobs are just marked sent once the user says they applied.
- **Job alerts are automatic** because they cost nothing (an email and a database row). SMS/WhatsApp alerts are deferred until there is revenue to cover per-message costs.
- **Ingestion can be pushed in.** PythonAnywhere's free tier can only reach whitelisted sites, so a scheduled GitHub Actions workflow downloads the feed and POSTs it to `/api/jobs/ingest/`, protected by a shared secret (`X-Ingest-Key`), not a user login. `/api/jobs/sweep/` works the same way for the match sweep.
- **Configuration comes from the environment.** `DEBUG` defaults to off and a missing `SECRET_KEY` stops startup. Cookies are `Secure` whenever `DEBUG` is off.
- **One origin in production.** Django serves the built React app and its API together, so there's no CORS or cross-site cookie handling in production. CORS is only enabled for the Vite dev server.
- **Generated CVs get unguessable filenames** (random prefix), because `media/` files are served by URL without a login check. This is obscurity, not access control; serving them through an owner-checking view is the proper fix and is still to do.

---

## Known gotchas

- **Older notes claimed Python 3.14 breaks the Django admin.** With Django 6.1 the admin pages rendered fine on 3.14 in testing (and there's a test that opens them), so that no longer holds. 3.12 stays the local default because it's what the pinned requirements were generated on.
- **`InconsistentMigrationHistory`**: delete `db.sqlite3`, re-run `migrate` fresh — only safe with no real user data.
- **Never copy a `db.sqlite3` over a live one.** A snapshot silently deletes every account created since it was taken.
- **Virtualenvs are not relocatable.** Moving the project folder (it happened with OneDrive) breaks every `.exe` launcher inside `.venv\Scripts`. Recreate the venv, use `python -m ...`, and keep projects out of synced folders.
- **`curl` on Windows/PowerShell**: use `curl.exe` explicitly, not bare `curl`.
- **Django shell doesn't hot-reload**: exit and restart `python manage.py shell` after any code change.
- **`blank=True` ≠ a database default**: still need `default=''` (or `null=True`) or object creation without that field fails with `NOT NULL constraint failed`.
- **Celery token rotation**: `str(refresh)` alone does NOT create a new token — must `blacklist()` then `set_jti()`/`set_exp()`/`set_iat()` first.
- **A stale access token breaks public endpoints.** DRF authenticates before checking permissions, so an expired token sent to login/register is rejected even though those views allow anyone. The frontend never sends the token to those endpoints.
- **`pip install python-docx` but `import docx`** — the PyPI package name and importable module name don't match. Easy to forget the install step exists at all since the import line looks self-contained.
- **When adding new imports/classes to an existing file, ADD to what's there — never regenerate the whole file from a partial snippet.** This project hit real bugs (missing `generics`/`permissions` imports, a URL never registered) purely from a new code block replacing the top of a file instead of being inserted alongside existing imports. When in doubt, paste the full corrected file rather than a fragment.
- **`git rm --cached`** needed once for `celerybeat-schedule.*` — Celery Beat's local runtime state, correctly `.gitignore`'d now; harmless if they reappear untracked.
- **A zip of this project once arrived with three files missing** and no error. Cause unknown. When sharing the project as a zip, check the file count or use the checksum manifest from the clean copy.

---

## Roadmap

1. ~~Custom User model~~ ✅
2. ~~Registration + login API (JWT)~~ ✅
3. ~~Profile editing~~ ✅
4. ~~Job ingestion (MyJobMag Kenya RSS, hourly via Celery Beat; or pushed in from GitHub Actions)~~ ✅
5. ~~Job search/browse + match-scoring~~ ✅
6. ~~CV upload~~ ✅
7. ~~Automated CV formatting (generate from profile data)~~ ✅
8. ~~Automated cover letter generation (match-score-aware)~~ ✅
9. ~~Auto-apply + job alerts (email + in-app)~~ ✅
10. ~~React frontend, walking skeleton (register, log in, browse, apply, review/send, notifications)~~ ✅
11. **First deployment on PythonAnywhere (free tier)** ← next up
12. Authenticated CV/cover-letter downloads (owner-only)
13. M-Pesa / Visa / Mastercard payments
14. Subscription tiers
15. Employer dashboard
16. Custom domain → ajiri.co.ke (needs a paid hosting plan)

**Deferred to V2** (logged in Monday.com, Product discovery status): CV parsing/auto-extraction from uploaded files; AI-generated (vs. template-based) cover letter text; Salary Negotiation Coaching upsell with admin notification; SMS/WhatsApp alerts.

**CI/CD**: CI exists — `.github/workflows/ci.yml` (at the repository root) runs on every push to `main` and every pull request. The backend job runs `manage.py check`, a missing-migrations check and the full test suite on Python 3.12, 3.13 and 3.14; the frontend job runs lint and a production build, and fails if the committed `ajiri-backend/frontend_build/` doesn't match what that build produces. Deployment is manual for now: `git pull`, `migrate`, `collectstatic`, then Reload on PythonAnywhere (see the runbook).

---

## Environment variables

Set in the git-ignored `.env` file (copy `.env.example`) or in the server environment. Real environment variables win over `.env`.

| Variable | Purpose | Default |
|---|---|---|
| `DEBUG` | Development mode. Leave off in production | off |
| `SECRET_KEY` | Django signing key. Required when `DEBUG` is off | none (startup fails) |
| `ALLOWED_HOSTS` | Comma-separated hostnames, e.g. `yourname.pythonanywhere.com` | empty |
| `CSRF_TRUSTED_ORIGINS` | Origins with scheme, for admin login over HTTPS | empty |
| `INGEST_API_KEY` | Shared secret for `/api/jobs/ingest/` and `/api/jobs/sweep/`. Must match the GitHub secret | empty (endpoints disabled) |
| `TRUST_PROXY_SSL_HEADER` | Believe the proxy's `X-Forwarded-Proto` (only if the host's proxy sets it) | off |
| `CORS_ALLOWED_ORIGINS` | Extra allowed origins | the Vite dev server when `DEBUG` is on, else none |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | Real email (SMTP) | console backend |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Redis for local Celery | `redis://localhost:6379/0` |

Never commit a real value. The old hard-coded `SECRET_KEY` is in git history — treat it as public.

---

## Contact

Solo project — Michael Mathenge (michael@michaelmathenge.dev)

</details>

<a id="record-housekeeping-review"></a>

### housekeeping review

<details>
<summary>Read dated details</summary>

Source: `docs/HOUSEKEEPING_REVIEW.md`; input SHA-256 `d2cf36bde3dddaaa17fbc8118e55c9eb61032f49250f5ab9d0846ceb3c165e54`.

# Housekeeping evidence

## Documentation cleanup — 1 November 2026

Performed locally in `codex/job-feed-display`, preserving its uncommitted feed
implementation and the dirty original checkout. No production operation, push,
merge, Jira edit or sync-script execution occurred in this housekeeping pass.

- Replaced duplicated backend onboarding and obsolete decision/prompts/CI proposal
  text with short current entry points. Six superseded documents were copied into
  labelled archives; each copy's SHA-256 matched its source before replacement.
  See [archive inventory](HISTORY.md#record-previous-archive-index) and the
  [backend snapshot](HISTORY.md#record-backend-readme-pre-first-release).
- Added a documentation index (historical path: `README.md`), rewrote next actions (historical path: `ROADMAP_NEXT_ACTIONS.md`)
  as the single ordered pending-work list, and limited
  open decisions (historical path: `../DECISIONS_PENDING.md`) to unresolved facts and consequential
  choices. Completed designs, owner inbox pilots and the first scheduled backup
  are not presented as new tasks.
- Labelled 17 old checkpoint/audit/release records as historical without removing
  their evidence. Corrected active release, backup, job-display, certificate and
  initial-hosting pointers. The implemented CI test step is no longer a proposal.
- Reconciled all 14 open non-Epic Jira issues read-only (13 In Progress, AJ-80
  To Do, no next page). Distinguished deployed MVP1, uncommitted feed code, PR73
  stage2 and the broader inactive PR71 work; none is rebuilt or declared live.
- Used the recorded MVP1 source `3408565`, last observed 482.4/512 MB quota and
  30 November expiry from the later release report, superseding older local
  headings. These are recorded observations, not fresh production checks.

No historical review, backup, database, private document, environment, Docker
lesson, lockfile, stash or Git configuration was deleted. Original archive content
is intentionally unchanged; relative links in snapshots resolve from the original
locations listed in their archive index. Active navigation uses maintained links.

Validation is documentation-only: check preserved archive content, active local
Markdown targets, all 14 open issue keys in the action list, and `git diff --check`.
Runtime tests are not rerun or newly claimed for this documentation pass; the
separate feed implementation's actual test/build evidence remains in the ledger.

Actual results: six archive copies matched reviewed `3408565` content after
newline normalization; all 83 local Markdown targets across 18 active/index
documents existed; all 14 live Jira issue keys appeared in the action list;
`git diff --check` exited 0. No runtime behavior changed in this pass.

## Historical cleanup — 20 October 2026

20 October 2026. Cleanup is limited to verified redundant material and recoverable
tracked changes. It does not authorize deletion of databases, private documents,
backups, environments, stash, Git configuration or uncommitted work in the original
checkout.

- Replaced the stale Checkpoint-1 README/setup instructions with short current
  entry points, the user journey guide and links to operator evidence. Historical
  reviews remain available; their content is not discarded as unused merely
  because it is old. CLAUDE.md is referenced by existing documentation and retained.
- Removed `ajiri-frontend/public/icons.svg` (5,031 bytes), an unused social-icon
  sprite. Repository searches for its filename and fragment references found no
  consumers in source, HTML, public assets, backend or documentation. The active
  favicon remains; its HTML reference was verified. The next generated frontend
  build removes the redundant copied sprite too.
- Added ignores for `.verification/` and `.worktrees/` so local test installations
  and isolated checkouts cannot be accidentally committed. The original Docker
  learning files, lockfile changes and coverage data remain preserved.
- Generated hashed frontend assets are replaced only from a verified build;
  superseded bundles are recoverable in Git. No private backup pruning occurs.
- A Windows-locked native Tailwind binary was left intact. Tests/build are being
  verified in a fresh isolated installation instead of killing unrelated processes
  or forcibly deleting a potentially in-use directory.

No broad “delete all untracked files” or Git clean/reset operation is appropriate
for this workspace. Future candidates require a reference/use check and explicit
identification in this report before removal.

</details>

<a id="record-previous-archive-index"></a>

### Previous archive index

Replaced by the source inventory below; no separate archive directory is needed.

## Consolidation inventory

Original source identities are retained below. A removed filename is provenance,
not a link to an expected live file. The four maintained screenshot guides remain.

| Checkout | Original file | Action | Input SHA-256 |
| --- | --- | --- | --- |
| Original checkout | `docs/CHECKPOINT1_REVIEW.md` | Consolidated; original removed | `a021efa8cfac3f12adc1663f8a9272bf078cd2be7d495253cb7f163c99dd6210` |
| Original checkout | `docs/CHECKPOINT2_REVIEW.md` | Consolidated; original removed | `5e84819a9f82642caeee9b1e8e51b4be271beed43c3e071ce5826070e16fdd42` |
| Original checkout | `docs/CHECKPOINT3_PLAN.md` | Consolidated; original removed | `84e712f86c666b087ac147a988c437f92d7c6fee12d2f933dc99797eda1bb5b4` |
| Original checkout | `docs/CHECKPOINT3A_REVIEW.md` | Consolidated; original removed | `0b6276ca6aea0430f35e5cdf51602a8d209f8f88f5fbf87cc63af72b16d6f524` |
| Original checkout | `docs/CI_PROPOSAL.md` | Consolidated; original removed | `729a2111f4db755260baf35cea5067d2ffd26ded53a0382bbd14b58252f9404c` |
| Original checkout | `docs/DECISIONS_NEEDED.md` | Consolidated; original removed | `5d29feaa061a230076fd94fdaeb9606eeb8bc0dd674b3f900c4b343d7eaaa55e` |
| Original checkout | `docs/DEPLOY_SECURITY_VERIFICATION.md` | Consolidated; original removed | `ec2b0dab5d0ca7d803f8676917b0a060623c533205e243f32730649ca5e95a97` |
| Original checkout | `docs/MODERNISATION_AUDIT.md` | Consolidated; original removed | `d0cbad2a0316bc2d2b9b9c080e855cb63932a1b06235614fe53d0fa1cf70ed75` |
| Original checkout | `docs/PHASE1_REVIEW.md` | Consolidated; original removed | `5b596fdf9d002f3591dbd751c17cf51a6fed79008ce7d85d87db54f20f12ae23` |
| Original checkout | `docs/PRIVATE_MEDIA_DESIGN.md` | Consolidated; original removed | `f2394020c87fea4b962b82b96f8c4c1d497cdbdc61d44c03a5f16db1c0c58284` |
| Original checkout | `docs/REFRESH_COOKIE_CSRF_DESIGN.md` | Consolidated; original removed | `94923297e326d6ed3c45a729e5fbc17946f21d20e8f403f6b637c7fa79a2121e` |
| Original checkout | `docs/ROADMAP_WORKING_PROMPTS.md` | Consolidated; original removed | `702426f763a2cf8a4e34fccf648fc25b978f8bbedb74427583fc911c2a2817b1` |
| Original checkout | `docs/SMTP_EMAIL_DESIGN.md` | Consolidated; original removed | `08f4c49a62797bf7f48ad333cb1a2f7538f0e1867b74fe62ffee9c16e941747c` |
| Reviewed worktree | `docs/CHECKPOINT1_REVIEW.md` | Consolidated; original removed | `f1a3c761de13d272ec6f536d8b259f7f576506dae4c07c9d5811697c4c49c45b` |
| Reviewed worktree | `docs/CHECKPOINT2_REVIEW.md` | Consolidated; original removed | `fbc28378a2a89ef49ee4e5165a1dba9ef5e395e673220c84d613e2f7421cbfda` |
| Reviewed worktree | `docs/CHECKPOINT3_PLAN.md` | Consolidated; original removed | `9f071091d3853370d6999147ac99ee96bc6eaaa6177f98fc1d6063316e367d06` |
| Reviewed worktree | `docs/CHECKPOINT3A_REVIEW.md` | Consolidated; original removed | `e7fb105035d7a7c2e842747184bb47e5c3c91d44b772a4451e5e66a886dc1e8e` |
| Reviewed worktree | `docs/CI_PROPOSAL.md` | Consolidated; original removed | `30b8a41c6693b07bb9fcfa22c96b0e6036f5fe7b281da499c6df975ef0955bac` |
| Reviewed worktree | `docs/DECISIONS_NEEDED.md` | Consolidated; original removed | `9775411a1bf3126a0decb8201a3c7a3f149cd811316ca008bfbe621c0630fc35` |
| Reviewed worktree | `docs/DEPLOY_SECURITY_VERIFICATION.md` | Consolidated; original removed | `46502a889a3406b5dae234daac449b5473bb061819b2a654839c4f0f642ffa37` |
| Reviewed worktree | `docs/MODERNISATION_AUDIT.md` | Consolidated; original removed | `a759f0f0e0b67782a139832784583be79d219724d03ca69f148b9f9da1703efc` |
| Reviewed worktree | `docs/PHASE1_REVIEW.md` | Consolidated; original removed | `c91778f1f1034a8ad0d50dda661a80c43d2425d061ffa27ae5865229c4ce6381` |
| Reviewed worktree | `docs/PRIVATE_MEDIA_DESIGN.md` | Consolidated; original removed | `f2394020c87fea4b962b82b96f8c4c1d497cdbdc61d44c03a5f16db1c0c58284` |
| Reviewed worktree | `docs/REFRESH_COOKIE_CSRF_DESIGN.md` | Consolidated; original removed | `daa0d137dce3ccb35544f172e97f9d2af2fe59e3e6818a40ce444a3eff3a0ed4` |
| Reviewed worktree | `docs/ROADMAP_WORKING_PROMPTS.md` | Consolidated; original removed | `3762888b7711e2cead7b25c2a45a9618cfe8acd4d7eb56eabd565bacee5739cb` |
| Reviewed worktree | `docs/SMTP_EMAIL_DESIGN.md` | Consolidated; original removed | `a76775f6335e48339174f034c32797c6700a31b6f764f192c95e1cebd824c1a5` |
| Reviewed worktree | `docs/CHECKPOINT3B_SCHEMA_REVIEW.md` | Consolidated; original removed | `bc87f7249171da4ed620d38e39b23b11ec9e2e073ec25cb5c2aa7aa6d855b3ee` |
| Reviewed worktree | `docs/CHECKPOINT3B_PHASE_A_REVIEW.md` | Consolidated; original removed | `f3a959bb64e926826476b389732a8cf933fe4a39672fb98f69172771d6901ca2` |
| Reviewed worktree | `docs/CHECKPOINT3B_ACCOUNT_EMAIL_REVIEW.md` | Consolidated; original removed | `c0cac6895c7426cfef9f2c6142794a21f31d7470450f8b5a728946cd73b6b4f1` |
| Reviewed worktree | `docs/CHECKPOINT3B_ACCOUNTS_REVIEW.md` | Consolidated; original removed | `4dd5e34824ce49446d46062eeb2af2f386308cb01d500ae87a1da9be8e674570` |
| Reviewed worktree | `docs/CHECKPOINT3B_DELIVERY_REVIEW.md` | Consolidated; original removed | `a69db249cb4bf766dd1674358a731e4994221e5222d26fe7faf7104bdc0b76cb` |
| Reviewed worktree | `docs/CHECKPOINT3B_PILOT_REVIEW.md` | Consolidated; original removed | `63bde784633881dcc838c2a62f594db2842f807713777a78c8f8dabbf8094584` |
| Reviewed worktree | `docs/CHECKPOINT4_PHASE_C_REVIEW.md` | Consolidated; original removed | `95610d89800303157b5cedae291f91561cb40d47bd03d9f109e53b7489adfd0b` |
| Reviewed worktree | `docs/SPRINT3_REVIEW.md` | Consolidated; original removed | `686ff232fe200d1898807988eb171c3162e2a14c970932baf13e9443c0abf431` |
| Reviewed worktree | `docs/SPRINT3_RELEASE.md` | Consolidated; original removed | `9a12fe5ad77f12b0f43da09e0de198fb99c0b39825e0da16144df746dcdf3440` |
| Reviewed worktree | `docs/PHASE_A_DEPLOYMENT.md` | Consolidated; original removed | `5f5dd2e8c5d8cba4e1957a4cb2931b8d1c2c0b0c5e754caa1f5c921ca7779578` |
| Reviewed worktree | `docs/archive/CI_PROPOSAL_2026-10.md` | Consolidated; original removed | `729a2111f4db755260baf35cea5067d2ffd26ded53a0382bbd14b58252f9404c` |
| Reviewed worktree | `docs/archive/DECISIONS_NEEDED_CHECKPOINT3.md` | Consolidated; original removed | `5efd3e80585cf8e860f63abbe61359f51a0e7305f534184df0bcb1326d5e93af` |
| Reviewed worktree | `docs/archive/DECISIONS_PENDING_2026-10-31.md` | Consolidated; original removed | `cbcf6d61ef133af6830c2c9832e67c70ad1a3654afef9661d14bf6e10c3db7c8` |
| Reviewed worktree | `docs/archive/DEPLOYMENT_CHECKLIST_CHECKPOINT2.md` | Consolidated; original removed | `0757513c619f486fa8ba4571f3b6db17b09c299d4f29f79202c4344112b7a408` |
| Reviewed worktree | `docs/archive/ROADMAP_NEXT_ACTIONS_2026-10-26.md` | Consolidated; original removed | `68c48c7a680a4f12c5215f6514f7da72e38a5747e95a9a534fbca84db7410106` |
| Reviewed worktree | `docs/archive/ROADMAP_WORKING_PROMPTS_2026-10-15.md` | Consolidated; original removed | `702426f763a2cf8a4e34fccf648fc25b978f8bbedb74427583fc911c2a2817b1` |
| Reviewed worktree | `ajiri-backend/docs/archive/README_PRE_FIRST_RELEASE.md` | Consolidated; original removed | `56407f81232f63f8f0aaef582eb8680bc081991fbb27fdb53f83ae3af32a755b` |
| Reviewed worktree | `docs/HOUSEKEEPING_REVIEW.md` | Consolidated; original removed | `d2cf36bde3dddaaa17fbc8118e55c9eb61032f49250f5ab9d0846ceb3c165e54` |
| Reviewed worktree | `docs/archive/README.md` | Consolidated; original removed | `3aa8c8a8f1bc4ae9947910713a308680711104ef86e947fd909c33b9e2cca7f4` |
| Original checkout | `docs/DEPLOYMENT_CHECKLIST.md` | Old content consolidated; current guide retained | `1a20726e10d97f3dce7daa80e384f59d1abe73b0eef21ff480a69f9f4de2b56a` |


## Additional completed package records

These dated reviews describe completed implementation/review packages; remaining
live acceptance is tracked in the current next-actions guide. They are consolidated
here rather than kept as separate active files.

- [ACCEPTANCE_JOURNEY_REVIEW.md](#record-acceptance-journey-review)
- [APPLICATION_CV_INTEGRATION_REVIEW.md](#record-application-cv-integration-review)
- [APPLICATION_PACKAGE_APPROVAL_REVIEW.md](#record-application-package-approval-review)
- [APPLICATION_PACKAGE_EDITOR_REVIEW.md](#record-application-package-editor-review)
- [APPLICATION_PACKAGE_FINAL_REVIEW.md](#record-application-package-final-review)
- [APPLICATION_PACKAGE_SCHEMA_REVIEW.md](#record-application-package-schema-review)
- [APPLICATION_SEND_AUTHORIZATION_REVIEW.md](#record-application-send-authorization-review)
- [APPLICATION_SEND_CLIENT_REVIEW.md](#record-application-send-client-review)
- [APPLICATION_SEND_SCHEMA_REVIEW.md](#record-application-send-schema-review)
- [APPLICATION_SEND_WORKFLOW_REVIEW.md](#record-application-send-workflow-review)
- [CV_BUILDER_REVIEW.md](#record-cv-builder-review)
- [CV_DATE_CONTROLS_REVIEW.md](#record-cv-date-controls-review)
- [CV_SAVE_FEEDBACK_REVIEW.md](#record-cv-save-feedback-review)
- [CV_SCHEMA_REVIEW.md](#record-cv-schema-review)
- [DELIVERY_CONCURRENCY_REVIEW.md](#record-delivery-concurrency-review)
- [DEPENDABOT_CHECK_FAILURES_REVIEW.md](#record-dependabot-check-failures-review)
- [INGESTION_RELIABILITY_REVIEW.md](#record-ingestion-reliability-review)
- [NPM_DEPENDENCY_BUILD_REVIEW.md](#record-npm-dependency-build-review)
- [OPERATIONS_ROADMAP_REVIEW.md](#record-operations-roadmap-review)
- [PRIVACY_REGISTRATION_REVIEW.md](#record-privacy-registration-review)
- [REGISTRATION_CV_JOURNEY_REVIEW.md](#record-registration-cv-journey-review)
- [UI_FEEDBACK_REVIEW.md](#record-ui-feedback-review)
- [UI_POLISH_PHASE_C_REVIEW.md](#record-ui-polish-phase-c-review)
- [CERTIFICATES_DECISIONS.md](#record-certificates-decisions)
- [DEPENDENCY_ADVISORIES.md](#record-dependency-advisories)
- [MIGRATION_DESIGN_3B1.md](#record-migration-design-3b1)

<a id="record-acceptance-journey-review"></a>

<details>
<summary>ACCEPTANCE_JOURNEY_REVIEW.md — historical package evidence</summary>

Original SHA-256: `97160fbbd51d2fd906c8387dad1255294188967bbde49b71a5e18bc2a120e190`.

# Acceptance journey review

19 October 2026. C1, local Phase C only. Base: 4b6e99b; no deployment.

The real-endpoint Django journey now selects its approval, prepares an application,
reads the review list and downloads its independent snapshot. It proves byte
identity before/after Profile edits, cross-owner denial, no mail/provider call,
unchanged delivery attempts and no sent timestamp. Captured verification mail is
cleared before preparation. Existing JWT/CSRF behavior is exercised, not changed.
Vitest now follows selection through the real Applications component to review;
registration/login/profile/builder transitions retain their existing component
coverage. This is API integration plus mocked client coverage, not browser E2E.

Actual gates: Python 3.12.6 check passed; makemigrations --check --dry-run reported
no changes; full Django suite 210 passed in 112.762s, one existing Windows symlink
skip. Node 24.19.0 npm ci (0 advisories), lint, 67 tests and build passed. The first
frontend run exposed a new mock missing ?page=1; corrected. The second exposed an
existing animation-frame focus assertion; waitFor now waits without weakening it.
The final frontend run passed all 67. No application defect was found in this
journey. Generated assets are byte-identical to the pinned committed build after
index newline normalization. No dependencies, migrations or production actions.


</details>

<a id="record-application-cv-integration-review"></a>

<details>
<summary>APPLICATION_CV_INTEGRATION_REVIEW.md — historical package evidence</summary>

Original SHA-256: `fa126ec01eb5d892c4f738f603f45769f7af5920ee51c5add554d199b143d3e9`.

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


</details>

<a id="record-application-package-approval-review"></a>

<details>
<summary>APPLICATION_PACKAGE_APPROVAL_REVIEW.md — historical package evidence</summary>

Original SHA-256: `c8137685ea4b4e10698accda25fdcead5a03eb3e802b8ad6c2a3d99721322f36`.

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


</details>

<a id="record-application-package-editor-review"></a>

<details>
<summary>APPLICATION_PACKAGE_EDITOR_REVIEW.md — historical package evidence</summary>

Original SHA-256: `9172c4fe9cff8a21374f7ac748fc5e284a7a755546864fa1c10e0644a8476f30`.

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


</details>

<a id="record-application-package-final-review"></a>

<details>
<summary>APPLICATION_PACKAGE_FINAL_REVIEW.md — historical package evidence</summary>

Original SHA-256: `51ab99636b2f1c58a346aaaedfd8a52ab51d9b7c32991d3b7b89b51636337a7e`.

# Application package roadmap — local final review

20 October 2026. Michael approved completing remaining P4b/P4c/P5 readiness without
intermediate approval pauses. This is the final local batch; no push, PR, main merge,
production action or real message was performed. Production remains recorded at
894d1eb, not freshly verified. Root checkout, existing Docker lesson, uncommitted
AGENTS/lockfile/coverage, stash and Git configuration were preserved.

## Package status and ranges

| Package | Local evidence | Status / suggested points |
|---|---|---|
| Delivery concurrency repair |09b76a1| Previously reviewed; one provider call with bounded receipt-only retries |
| P1 additive package schema |e1e8f94| Previously reviewed;3 |
| P2 select CV/edit/revision |622d639,ae8d05f| Previously reviewed;5 |
| P3 exact preview/document approval |18b7092,9f08327| Previously reviewed;5 |
| P4 approved design |b1bd394| Previously reviewed; no sending activation |
| P4a additive authorization schema |b1bd394..d6b7b1e| Previously reviewed;3 |
| P4b authorization/withdrawal/shared dispatch |d6b7b1e..711872a| Implemented/tested locally;5 |
| P4c UI/final concurrency hardening |711872a..local final HEAD| Implemented/tested locally;5 |
| P5 pilot readiness/runbook |Included with P4c final batch| Documentation ready;3 proposed; live pilot NOT RUN |

Current branch is codex/application-send-client in
`C:\dev\ajiri\.worktrees\application-package-schema`. Resolve the final commit
range using the identity command below; the frontend-build commit is last.

## What the user can do after a reviewed release

Choose an approved CV and draft/edit a job-specific cover letter, save immutable
revisions, review/download exact DOCX bytes, approve those documents, review the
exact outgoing email plan and separately record/withdraw per-application permission.
The system distinguishes permission, dispatch handoff and provider receipt. It does
not infer future-job permission or submit forms on employer websites.

The current web sender remains explicitly disabled. Mocked shared-service dispatch
requires the exact authorization and verifies bytes/payload/current identity/job
again inside the atomic budget reservation. It commits one receipt/link and handoff
before one provider call. Replays only reconcile; unknown outcomes block new sends;
one explicit initial-failure retry costs another slot. No console/SMTP workaround.

## Verification summary

P4b: backend check/drift passed,275 tests/156.140s,OK with one existing Windows
symlink skip. Node 24.19 locked install/lint passed,86 component tests/14 files,
build passed;21 generated files matched existing committed assets.

P4c/final: commands, focused/UI regressions and final outcome details are in
APPLICATION_SEND_CLIENT_REVIEW.md. Current runbook is
APPLICATION_OWNER_PILOT_RUNBOOK.md. Only disposable test DBs were migrated; jobs0009/
0010 were added by earlier reviewed schema packages, no new migration here.

Final results: system check/drift passed; **279 backend tests in141.350s, OK with
one existing Windows symlink skip**; explicit **Node24.19.0**, locked install/lint,
**98 frontend tests/15 files** and build passed. Subsequent build matched all21
generated files (index.html CRLF normalized). New source and generated build are
separate local commits, with the build last. No manual browser/inbox claim is made.

Before handback, verify the nonempty local range and identity:

```powershell
Set-Location C:\dev\ajiri\.worktrees\application-package-schema
git branch --show-current
git status --short
git log --format="%h %ae | %ce" d6b7b1e..HEAD
git diff --check
```

Every new author/committer must equal the configured noreply identity; actual
verification is appended after final commits. Do not amend configured identity.

## Clear remaining release path

1. Michael reviews this finished local batch, test results and manual instructions.
   No action is required between individual local packages.
2. On final approval, explicitly authorize push/PR/merge and the specific disabled
   release/deployment. Pin the CI-green release; pause writers, fresh verified
   backup/off-server copy, stage migration source, review/apply only expected0009/
   0010, then activate paired code and perform manual acceptance. Dependencies did
   not change; no routine pip install is needed. Resume/verify ingestion afterwards.
3. Real application pilot additionally needs a reviewed connection of the currently
   disconnected adapter, freshly verified sender/provider size/owner/suppression
   evidence, privacy/retention review and explicit final live-send approval. Use one
   synthetic owner-addressed job/application, not a real employer destination.
   Configuration alone cannot enable sending in this current release.
4. Run one supervised attempt and record receipt plus independent inbox/attachment
   checks; stop on ambiguity/bounce/complaint. This remains open in Jira rather than
   claiming the live pilot or AJ-17 is Done from passing mocks.
5. Broad employer/alert sending, copies, certificates, alert defaults/consent,
   suppression/webhooks and erasure remain outside this agreed narrow local batch.
   Existing design approvals do not expand the implementation scope automatically.

No fresh Jira writes were performed during this local batch. Each package review
contains a Jira-ready title/acceptance line and honest point suggestion. The HTTPS
scheme/support/HSTS question and web-app renewal remain separate operational items.


</details>

<a id="record-application-package-schema-review"></a>

<details>
<summary>APPLICATION_PACKAGE_SCHEMA_REVIEW.md — historical package evidence</summary>

Original SHA-256: `9f62a1cc3112d81be4324c9e559018852d60ccd505cf332a776841b4c9bc956f`.

# P1 application package schema review

19 October 2026. Branch `codex/application-package-schema`, isolated worktree
`C:\dev\ajiri\.worktrees\application-package-schema`, based on reviewed local
concurrency repair `09b76a1` (production base `894d1eb`). Michael explicitly
approved the schema handback and P1 implementation. Stop after this migration
package for review; no P2 UI/API or real sending implementation.

## Changes

- jobs migration 0009 creates ApplicationPackage and ApplicationPackageApproval,
  with FKs to existing Application, CVApproval and User. It adds no existing-table
  columns, data migration or backfill. AUTH_USER_MODEL and historical migrations
  remain unchanged. The swappable dependency is a reference, not a User change.
- Packages hold positive per-application unique revisions, explicit approved-CV
  provenance, job snapshot, letter/email content, private document fields, hashes,
  sizes and template version. Four SQL constraints cover revision uniqueness and
  positive revision/CV size/letter size.
- Approval has a unique package link, protected approver, timestamp, content
  fingerprint and document-policy version. It conveys no sending authorization.
- A UUID upload function ignores supplied filenames and uses existing private
  storage. No files are generated by model construction or migrations.
- No endpoint, serializer, admin registration, signal, task, deletion hook, provider
  caller, preference change, dependency or frontend source change is introduced.

## Verification

Focused `manage.py test jobs.test_application_package_schema --noinput --failfast`:
**5 passed, 0.581 seconds**. First run exposed a Windows separator mismatch in a
test assertion, corrected by normalizing only that assertion; storage names still
use UUID DOCX paths. No production behavior was weakened to pass it.

The populated upgrade test uses MigrationExecutor on an isolated test database
and temporary private media. It confirms the plan includes only jobs0009 and only
CreateModel/AddConstraint operations, then compares all existing User, Profile,
CVApproval, Application, DeliveryAttempt and DeliveryDailyBudget rows, plus saved
CV/letter/approval file bytes. New tables remain empty. Historical model code can
still read applications while new tables remain present. Constraints test duplicate
revisions/approvals, nonpositive/null sizes, missing provenance, safe distinct UUID
paths and PROTECT behavior. Tests never contact Brevo.

Commands from the backend (existing Python 3.12 virtualenv at checkpoint-3b):

```powershell
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:REAL_EMAIL_ENABLED = 'False'
& $python manage.py makemigrations jobs --name application_package_schema
& $python manage.py check
& $python manage.py makemigrations --check --dry-run
& $python manage.py test jobs.test_application_package_schema --noinput --failfast
& $python manage.py test --noinput --failfast
```

Frontend verification explicitly uses Node v24.19.0 with existing npm CLI:
`npm ci`, `npm run lint`, `npm run test -- --run`, `npm run build`.
Full outcomes and build comparison are recorded after completion below. No existing
development or production database was migrated; only disposable test DBs use0009.

## Review limits and next boundary

These tables are dormant. ORM writes are not globally immutable, and SQL does not
validate cross-owner FKs, hash/content correspondence, allowlisted job JSON, upper
size limits or latest-revision approval. Those must be implemented transactionally
and tested in P2-P3 before exposing a writer. The tests explicitly distinguish SQL
constraints from future service checks. The proposed email attachment limits remain
separately gated; P1 enforces positive stored sizes only, as in the approved schema.

PROTECT prevents source approval/approver deletion once referenced. This behavior
is intentional in the approved schema and tested; AJ-25 erasure design must resolve
retention semantics before an erasure feature is implemented. Django cascades do
not automatically remove file bytes. No automatic orphan/deletion policy is added.

Old sender code ignores the new tables. P1 must not be described as enforcing new
application approval or fixing legacy sending. Keep existing owner account-email
pilot boundaries; broader sending/attachments stay disabled. P2-P3 must close the
legacy sender bypass before exposing new controls. Do not deploy a mixed sender
fleet that bypasses the future authorization rules.

## Future deployment and rollback — not performed

After a separately approved CI-green release: pause writers, verify fresh private
backup, stage migration source, review migration plan (only expected jobs0009),
apply migration, then activate paired reviewed code. No new dependency install is
needed for P1. Stop on any unexpected migration, permission or integrity failure.

Routine rollback reverts code while retaining tables, snapshots, approvals, newer
writes and files. Do not reverse populated0009: its generated reverse operations
drop the new tables and lose their data. A destructive rollback requires separate
approval; never restore an older database over newer writes routinely. Do not
enable legacy console/SMTP sending as a rollback tactic.

Suggested size: **3 points**, within AJ-17's application workflow scope. Jira-ready:
**Add dormant application package and document-approval schema | AC: populated
upgrade preserves existing rows/files; per-application revisions and approval
uniqueness enforced; no backfill, API or sending; full gates pass; rollback retains data.**

Stop for package review. No push, PR, merge, deployment or production migration.

## Completed frontend verification — 19 October 2026

Node v24.19.0: locked `npm ci` passed (180 packages installed, zero reported
vulnerabilities); lint passed; Vitest passed 71 tests across 12 files; build passed.
All 21 generated frontend files matched the committed build after normalizing
index.html line endings. No frontend source or generated asset change is included
in P1. These results belong to this package's earlier verification, not a new
20 October run. Frontend files remain unchanged at resumption.

## Final backend verification — 20 October 2026

`manage.py check`: no issues. `makemigrations --check --dry-run`: no changes.
Full `manage.py test --noinput --failfast`: 223 tests run in 97.454 seconds,
OK with one existing Windows-specific symlink skip. Synthetic error-event logs
were expected failure-path coverage, not provider calls. The initial sandbox run
failed on Windows temporary-directory permissions; the same suite passed outside
that sandbox without source changes. `git diff --check` passed.

All verification used disposable test databases. No normal development or
production migration was applied. The local commit's author and committer must
match the configured noreply identity; verified in the handback Git range.


</details>

<a id="record-application-send-authorization-review"></a>

<details>
<summary>APPLICATION_SEND_AUTHORIZATION_REVIEW.md — historical package evidence</summary>

Original SHA-256: `a745a6b039056aa1c809d45bcf3b23f1e88dcb26d708ac82e5d9e644ede6eec1`.

# P4 design handback

20 October 2026. Branch `codex/application-send-authorization-design`, from reviewed
P3 `9f08327`. Michael approved proceeding to the separately gated P4 design review.
This package changes documentation only. No migration/code/provider/configuration,
push, deployment, DNS or real sending action is included.

Read APPLICATION_SEND_AUTHORIZATION_DESIGN.md for the exact proposal, including:

- separate document approval, one-application authorization and explicit dispatch;
- two additive tables and their field types/defaults/nullability/constraints,
  ownership validation, retry associations, retention and data-preserving rollback;
- SQLite reservation/handoff cutoff, cancellation race semantics, immutable plan,
  safe unknown outcomes and shared accounting without changing account-pilot scope;
- primary-only sending, copies OFF, separate attachment/provider/pilot/privacy gates;
- tests and staged P4a/P4b/P4c implementation, each stopped for review with real
  transport disabled. A design approval is not an application-pilot-send approval.

## Decisions awaiting review

| Choice | Proposed default | Approval status |
|---|---|---|
| Authorization wording/purpose | Explicit per job/package/recipient; distinct Send button | Pending |
| Lifetime | 24 hours; changes require a new plan and authorization | Pending |
| Schema | Authorization plus attempt-link tables, no backfill; PROTECT evidence | Pending migration design review |
| Withdrawal cutoff | Atomic dispatch handoff; no promise of recall afterward | Pending |
| Retries | One explicit retry after a definite failure; none after unknown/accepted | Pending |
| Copies | OFF; no CC/BCC or copy-role schema in first implementation | Pending |
| Attachments | Exactly two saved DOCX, 2 MiB each / 4 MiB raw total | Pending separate attachment-policy approval |
| Pilot application cap | One attempt per Nairobi day within existing shared five-message cap | Pending; activation not included |
| Provider payload ceiling | Verify current official limit and approve conservative ceiling | Unverified; activation blocker |
| Changed destination | Fail closed; no silent retarget or arbitrary-recipient editor | Pending limited-scope decision |
| Broad launch | Secure suppression/events, consent and privacy review first | Not approved |

No proposed default is described as an existing user choice. Certificate/alert
defaults and broad employer/alert delivery remain separate backlog decisions.

## Verification commands

Read-only corroboration: jobs/models.py, jobs/application_packages.py,
jobs/package_review.py, jobs/delivery_service.py, jobs/brevo_transport.py,
accounts/pilot.py, OWNER_EMAIL_PILOT.md and APPLICATION_ALERT_SENDING_DESIGN.md.
No current provider or production claim is inferred from these local files.

Required repository gates were run for this documentation package, using existing
Python 3.12 and explicit Node v24.19.0, with environment-only DEBUG=True,
PYTHON_DOTENV_DISABLED=1 and REAL_EMAIL_ENABLED=False:

```powershell
$python = 'C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend\.venv\Scripts\python.exe'
$node = 'C:\Users\micha\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$npm = 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js'
$env:PATH = (Split-Path $node) + ';' + $env:PATH
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

Actual results and generated-build comparison are appended after completion.
No new runtime behavior is claimed or tested as implemented; future P4 tests above
remain proposed. Existing suite results verify the unchanged implementation only.

## Handback and next boundary

Suggested design slice: **2 points**, within P4's originally suggested 5-point
package; implementation should be re-estimated after this review rather than
pretending schema/consent/provider work is included in two points. Jira-ready:
**Review exact application send authorization and ledger design | AC: consent,
schema, withdrawal cutoff, immutable plan, limits, retry/unknown behavior and
data-preserving rollback documented; implementation and activation remain gated.**

Next requested decision is approval/amendment of this exact design. If approved,
start **P4a additive schema and migration tests only**, disabled real sending, then
stop for its review. Do not start P4b/c or P5 from that schema-only approval.

## Final results — 20 October 2026

- Backend check: no issues. Migration drift: no changes. Full existing suite:
  **247 tests run in 143.398 seconds, OK with one existing Windows symlink skip**.
- Node **v24.19.0**, npm ci: 180 packages installed / 181 audited, zero reported
  vulnerabilities. Lint passed without warnings; Vitest **86 passed across 14 files
  in 14.28 seconds**; build passed in 1.28 seconds.
- All **21 generated files match** the committed P3 frontend_build after normalizing
  index.html line endings. No generated files or frontend/runtime code changed.
- No new tests were added for unimplemented proposals. No ordinary development or
  production database was migrated, no provider limits/production state were
  inspected, and no email was sent. The original checkout/Docker lesson remain intact.
- Final diff is documentation only; git diff --check passed. Before commit the branch
  is checked; the non-empty 9f08327..HEAD author/committer range is verified against
  the configured noreply identity at handback. No push or deployment.


</details>

<a id="record-application-send-client-review"></a>

<details>
<summary>APPLICATION_SEND_CLIENT_REVIEW.md — historical package evidence</summary>

Original SHA-256: `b9bb0ecbad26f90d7ae4cbfbcbfe33406080bfdab7318e572c98e825da8df14c`.

# P4c client authorization and P5 readiness review

20 October 2026. Branch `codex/application-send-client` starts from P4b711872a.
Michael approved the remaining local roadmap as one batch for final review. No
push, remote merge, deployment, production inspection, provider call or live pilot.

## Changes

- An approved latest saved email package exposes a separate plan/status panel.
  It loads only after an explicit review click, not when listing applications.
  It shows actual recipient/verified Reply-To/From, exact email text, package revision,
  both outgoing filenames/byte sizes, copies OFF, 24-hour expiry and disabled state.
- Permission checkbox starts unchecked, resets on edits/revision changes and grants
  one exact application only. Recording permission does not dispatch. Dispatch is
  a separate explicit action, disabled by the current server response. Withdrawal
  requires another plan review before fresh permission. Document approval remains
  independent, including historical downloads and external website confirmations.
- Single-flight mutations; unknown replies reconcile by owner GET/request key or
  receipt. No automatic POST repeat. Working edits unmount the review; late replies
  cannot restore an old checkbox/plan. Read-only history supports refresh/reload.
- Provider acceptance, definite failure, reserved and unknown have distinct truthful
  labels. One explicit retry requires a new reviewed plan and unchecked permission;
  no retry chain, copy, automatic delivery or claim of inbox delivery.
- Final hardening binds the current job ID/name as well as the package, reconciles
  an identical handoff committed during preflight, validates receipt-link provenance
  and reads link/cutoff together in one SQL snapshot. This avoids a stale authorization
  read turning a successful concurrent handoff into a false new-send failure. It
  preserves one provider call and the existing database-only receipt retry.
- P5 readiness/runbook explicitly separates local completion from the unperformed
  live pilot. Current provider size ceiling, sender/allowlist/suppression checks,
  reviewed live adapter connection and final approval remain activation requirements.
  See APPLICATION_OWNER_PILOT_RUNBOOK.md for exact release and rollback steps.

## Actual verification

Runtime/PowerShell definitions are in APPLICATION_SEND_SCHEMA_REVIEW.md. All backend
commands use Python 3.12 with PYTHON_DOTENV_DISABLED=1,DEBUG=True,REAL_EMAIL_ENABLED=False.

Focused `npm test -- --run src/test/application-send.test.jsx
src/test/package-review.test.jsx`:20 tests/2 files passed in4.23s; lint passed.
New client coverage includes explicit separate actions, exact unchecked consent,
disabled send, lost create/dispatch replies, missing reconciliation key, double
clicks, withdrawal, unknown/accepted/failed states, bounded retry, revision/unmount
and approval gating. These component/API mocks are not one browser end-to-end test.

Full frontend with explicit Node 24.19.0: `npm ci`180 packages/181 audited, zero
reported vulnerabilities; `npm run lint` passed; `npm test -- --run`98 tests/15
files passed in16.63s; `npm run build` passed in6.29s. No new dependencies/lockfile
change. Frontend build is committed separately as the last frontend-package commit;
a subsequent verification build must match all generated bytes (index CRLF only
normalized). Final backend and generated-file results are recorded below.

Earlier full backend check/drift passed;276 tests in162.072s,OK/one existing Windows
symlink skip. That is interim evidence before adding the final three corruption/
shared-cap tests and single-snapshot link fix, not the final code's test count.

## Manual acceptance instructions — not executed

After a separately approved paired release into an isolated synthetic environment:

1. Register/login, verify a captured test mailbox, save synthetic profile/CV, review
   and approve the CV. Use a synthetic job with a stable genuine owner-controlled
   email destination and a configured synthetic From; never retarget a real listing.
2. My applications → choose approved CV → draft/edit exact letter and email text →
   save new revision. Review saved DOCX text/order and download both exact documents.
3. Approve saved documents. Verify this records no sending permission or ledger entry.
4. Review email plan. Inspect To/Reply-To/From, subject/body, two names/sizes, copies
   OFF and disabled notice. Verify permission starts unchecked. Record it explicitly;
   check 24-hour expiry and that no message/attempt/quota is created. Send stays disabled.
5. Reload/check status; it shows the same authorization. Withdraw, review again,
   and confirm fresh permission requires another unchecked action. Make/save a new
   revision and confirm the older permission is superseded. Changing job/mailbox/
   name/From or file bytes blocks a new dispatch instead of silently changing consent.
6. For dispatch states use the provided fake-transport tests. A real pilot is NOT
   part of this manual checklist. Unknown/reserved blocks resending; accepted means
   provider acceptance only; one failed initial attempt can get one new explicit retry.
7. Confirm external website submission behavior, keyboard/tab/focus and mobile
   wrapping, full nested errors and private file denial remain correct.

Manual browser/mobile, Word/Google Docs rendering and real provider/inbox checks
were NOT performed for this batch. Existing root Docker lesson uses a different
checkout and does not demonstrate these local branch changes. Do not silently
replace its database, media, container or current checkout to perform this review.

## Rollback, risks and Jira-ready result

Use the runbook's disabled paired-code rollback, retaining populated schema/files/
evidence and newer writes. No old database restore or receipt deletion. Remaining
limits: no live factory/activation, automated suppression/webhook/erasure workflow,
broader sending or copy support. Provider ceiling/current sender/owner evidence
must be established before live connection. File/network changes after handoff
cannot be recalled atomically. Protected provenance can affect future deletion.

Suggested5 points for P4c plus3 readiness points, not a completed live pilot.
Jira-ready: **Review and authorize exact application email in My applications |
AC: document-only approval precedes private plan, unchecked per-application 24-hour
permission and separate disabled dispatch; withdrawal/status/retry UI is truthful,
uncertain requests reconcile by GET, edits reset state and full gates/build pass.**

## Final gate results — 20 October 2026

- `python manage.py check`: no issues.
- `python manage.py makemigrations --check --dry-run`: no changes.
- `python manage.py test --noinput`: **279 tests in 141.350 seconds, OK with one
  existing Windows symlink skip**. Includes the final corrupt-file/link, shared
  pilot-cap, handoff-during-preflight and single-SQL-snapshot regressions.
- Node **v24.19.0**; locked installation, lint, **98 component tests across 15
  files**, build and committed-build comparison passed. Subsequent build1.24s;
  all **21 generated files match**, normalizing only index.html CRLF.
- `git diff --check` passed. The local source/readiness commit precedes the generated
  frontend-build commit. Check the nonempty final range's author/committer identity
  with APPLICATION_PACKAGE_FINAL_REVIEW.md's command; configured noreply is retained.
- No new migration/dependency, live email, production check, push or deployment.


</details>

<a id="record-application-send-schema-review"></a>

<details>
<summary>APPLICATION_SEND_SCHEMA_REVIEW.md — historical package evidence</summary>

Original SHA-256: `4dc297ef62edecfc347f4cf13eb56e5b535d1f208f5dd0fb288348b6b2fcfc3e`.

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


</details>

<a id="record-application-send-workflow-review"></a>

<details>
<summary>APPLICATION_SEND_WORKFLOW_REVIEW.md — historical package evidence</summary>

Original SHA-256: `270bfef36c4f677650ef842e16ecc46ba6cc97f0c1b7536678fddf3cec56a523`.

# P4b application authorization and mocked dispatch review

20 October 2026. Branch `codex/application-send-workflow`, based on P4a `d6b7b1e`.
Michael approved completing P4b, P4c and P5 readiness as one local batch with final
review. This supersedes intermediate stop instructions in historical P4 notes.
Recorded production is `894d1eb`; it was not inspected or changed in this batch.

## Behavior

- Private owner-only no-store send-plan, authorization create/lookup/history/detail,
  withdrawal and dispatch-reconciliation APIs. Strict types/unknown-field rejection.
  GET/HEAD never create authorizations, quotas, files or messages.
- Exact bounded versioned plan: current owner/name, latest document proof/package,
  current unchanged job/destination, verified Reply-To, configured From, exact email
  text and two saved verified DOCX byte hashes/sizes/ASCII filenames. Copies off.
  Missing sender configuration blocks preview; no placeholder sender is selected.
- Explicit unchecked consent is required by API and service; authorization lasts
  24 hours. Same owned request key/binding returns its historical record before
  fresh eligibility checks. Changed binding conflicts; another owner's key is404.
  GET derives expiry; creation closes expired evidence before allowing replacement.
- New saves supersede active authorizations atomically. Withdrawal is idempotent
  until the committed dispatch handoff; after it, cancellation is not promised.
- Direct application DeliveryService calls now require exact authorization identity.
  Full payload/current proof/files/name/mailbox/job revalidation occurs before and
  inside reservation. Shared transaction reserves budgets, creates receipt/link and
  closes permission; rollback leaves no partial budget or cutoff. Network stays
  outside transactions. Receipt-only retries preserve the earlier concurrency fix.
- One explicit retry of the initial definite failure; no chain/fork, unknown retry,
  quota refund, copy or accepted resend. Existing account and alert policy unchanged.
- Separate injectable application-pilot boundary, exact owner/actual recipient,
  synthetic subject, exactly two attachments, 2 MiB each/4 MiB raw, nonzero reviewed
  serialized ceiling, one application/Nairobi day and five total shared messages.
  No live factory exists and the endpoint remains disconnected even if global or
  application flags are set. Tests use fake transport only. No credentials read.

## Gates and evidence

Commands/environment match APPLICATION_SEND_SCHEMA_REVIEW.md, using Python 3.12,
PYTHON_DOTENV_DISABLED=1, DEBUG=True, REAL_EMAIL_ENABLED=False and explicit
Node 24.19.0. Actual results are recorded below after completion.

Final backend gates: `manage.py check` no issues;
`manage.py makemigrations --check --dry-run` no changes;
`manage.py test --noinput` **275 tests in156.140s, OK, one existing Windows
symlink skip**. This includes the added save/dispatch cutoff and concurrent name
change regressions. Expected synthetic failure-path logs are not live failures.

Focused `manage.py test jobs.test_delivery_service jobs.test_send_authorization
--noinput`:40 passed in16.789s before adding three cutoff/name regressions.
Initial fixture replay errors were fixed by refreshing the authorization fixture
state; unsafe-name normalization now collapses redundant underscores. Core replay
and owner conflict are explicitly tested; no failed run is counted as passing.

Node 24.19: `npm ci`180 installed/181 audited, zero reported vulnerabilities;
`npm run lint` passed; `npm test -- --run`86 tests/14 files passed in21.04s;
`npm run build` passed in4.41s. All21 generated files match committed frontend_build
after index.html CRLF normalization. No frontend source/assets changed in P4b.

No new dependency or migration. Historical migrations, auth/CORS, ingestion, CI,
hosting, original checkout/Docker files, stash/config and existing coverage preserved.
Only disposable test databases were migrated. Windows-only verification does not
claim Linux or Python 3.13/3.14 results; existing Windows symlink skip is recorded.

## Remaining manual/release checks

P4c adds the UI without sending. P5 supplies the supervised runbook/readiness report;
no real pilot is performed in this batch. Provider size/terms, verified sender,
owner allowlist and manual bounce/complaint review must be freshly established at
activation. Broader sending, copies, suppression/webhooks, certificates and alert
consent/defaults stay outside this local package. AJ-25 retention/erasure remains
unresolved; protected evidence can block deletion. Filesystem/network operations
cannot be atomic with SQL after the handoff.

Rollback to a reviewed email-disabled server/client pair while retaining populated
tables, private documents, receipts/links and newer writes. Do not reverse jobs0009/
0010, delete receipts to retry, or restore an old DB over newer writes. Exact later
server procedure is in APPLICATION_OWNER_PILOT_RUNBOOK.md (P5).

Suggested5 points, AJ-17 slice. Jira-ready title/acceptance:
**Bind application dispatch to exact revocable authorization | AC: private plan,
explicit 24-hour permission, atomic withdrawal/dispatch cutoff, exact saved bytes,
one explicit retry, shared budgets/replay safety, fake-only tests and disabled
production endpoint pass all gates.**


</details>

<a id="record-cv-builder-review"></a>

<details>
<summary>CV_BUILDER_REVIEW.md — historical package evidence</summary>

Original SHA-256: `c5066963a9d83e070cb80bc00382d569ffcea932fd5f42b80e2f483df91526a2`.

# Personal CV builder review

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

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


</details>

<a id="record-cv-date-controls-review"></a>

<details>
<summary>CV_DATE_CONTROLS_REVIEW.md — historical package evidence</summary>

Original SHA-256: `48d61552346c90b7948b04b30ee6c12205b7ef83eefdefbb78feec4996d726db`.

# CV date controls review

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. Deployment of this document version/package is not verified here. Historical statements/results below are preserved; see AGENTS.md section 4.

17 October 2026. Local batch branch `codex/cv-save-feedback`. Suggested estimate:
2 points for date controls; certificate uploads are a separate proposed package.

The browser-dependent month picker is replaced for employment, education and
certification dates with a named month dropdown and numeric year input. Users can
type an older year directly without paging through calendars, or clear both parts
explicitly. Blank optional dates remain supported. Partial input stays in unsaved
state and browser validation requires the missing part rather than silently
discarding it. Server date/order validation remains unchanged. Selecting current
work/study clears and disables its end date and shows Present.

No API, stored date format, model, migration, dependency or production setting
changed. Complete dates still save as YYYY-MM. Existing approved CV documents are
not regenerated. Certificate uploads are not implemented: see the separate schema
and storage proposal in CERTIFICATE_UPLOAD_DESIGN.md.

## Verification

Backend check passed, migration drift reported no changes, and the full Django
suite passed: 210 tests in 148.715s, one existing Windows symlink skip. Node 24.19.0
locked npm ci, lint, all 66 frontend tests and production build passed. Generated
frontend_build refreshed once, with index.html normalized to LF. git diff --check
passed. Added component regressions cover
named month choices, typing a historical year, preventing partial-date submission,
unchanged YYYY-MM payloads, current-work end-date clearing/disabling, clear action,
loading existing certificate dates and preserving an independent expiry date.

## Manual checklist after review

1. In a test CV, choose September and type 2018. Save and verify 2018-09 in the
   preview. Reload a saved draft and confirm both controls retain the date.
2. Choose a month without a year, then try Save. Expect focus at the missing year
   with a browser validation message; typed CV information remains intact.
3. Set an end date, select currently work/study here, then save. End controls should
   be disabled/empty and preview should say Present. Unchecking re-enables them.
4. Clear dates; save and confirm they are omitted. Try an end before the start;
   expect the existing server validation summary and retained input.
5. Check issue/expiry separately, mobile widths, touch selection and keyboard tab
   order. Real-browser/mobile visual QA remains unverified in this package.

No push/deployment. Roll back the paired frontend source/build together. No data
rollback or migration is needed. Original-checkout changes/stash/config preserved.


</details>

<a id="record-cv-save-feedback-review"></a>

<details>
<summary>CV_SAVE_FEEDBACK_REVIEW.md — historical package evidence</summary>

Original SHA-256: `559cc519b6ef067c65888f94e4339262723ee79be1df8dfaa472a23f91c81b3f`.

# CV save feedback fix

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. Deployment of this document version/package is not verified here. Historical statements/results below are preserved; see AGENTS.md section 4.

17 October 2026. Branch `codex/cv-save-feedback`. Suggested estimate: 1 point.

The live CV form submitted successfully, but the server rejected incomplete added
entries. The summary appeared above the long editor and flattened nested errors
into repeated section-level messages. Read-only inspection confirmed this cause;
no production CV fields were changed or submitted by the agent.

The editor now focuses and scrolls to validation errors, preserving section, row
number and field label. Successful saves focus the saved preview. Unsaved values,
revision checks, approval rules and request retry behavior remain unchanged. No
backend behavior, dependencies, migrations, auth or production configuration changed.

## Verification

- Node 24.19.0: locked `npm ci`, lint, 64 component tests across 10 files and build
  passed. The regression covers repeated errors, exact entry/field labels, focus,
  scrolling, retained input and explicit resubmission. Existing preview test checks
  that focus moves to its heading.
- Initial restricted npm install failed with Windows EPERM; normal-permission
  install passed without lockfile changes. A test initially checked focus before
  the second rejected save finished; corrected to await the rendered feedback.
- Backend check: no issues. Migration drift: no changes.
- Full Django suite: 209 tests, OK (one existing Windows symlink skip), 108.858s.
  Initial restricted run produced filesystem errors and was stopped;
  normal-permission rerun passed.
- Committed frontend build regenerated from the verified build, index LF-normalized.
- Live browser testing of this new fix and screen-reader announcement remain
  unverified; the production page retains the previous release.

## Manual verification after a reviewed release

1. Keep any current unsaved edits on the open production page; do not reload it
   merely to inspect this local fix. Complete missing required fields or remove
   unused entries before saving the current draft.
2. In a test CV with two work entries, leave the second Role/Employer empty. Save
   from the bottom of the editor. Expect focus and scroll at the error summary,
   with “Work experience 2” and each missing field named. Values remain intact.
3. Correct the fields and save. Expect focus at “Review revision …”, with exact
   saved preview content. Approval still requires explicit review consent.
4. Try an invalid date pair, a stale revision and a network failure. Expect useful
   visible feedback and no automatic mutation retry or lost input.

Push and deployment are pending review. Roll back the matching frontend build and
source together; this fix has no schema or data rollback requirement.


</details>

<a id="record-cv-schema-review"></a>

<details>
<summary>CV_SCHEMA_REVIEW.md — historical package evidence</summary>

Original SHA-256: `139293e66308d7df8a802f0732cce207e66318d3db4a337dc6383da97dc10a1c`.

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


</details>

<a id="record-delivery-concurrency-review"></a>

<details>
<summary>DELIVERY_CONCURRENCY_REVIEW.md — historical package evidence</summary>

Original SHA-256: `fe5a9be490e9fac2720f759f40c814237c3ec0f0b0cd9e3f311c857652f338cb`.

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


</details>

<a id="record-dependabot-check-failures-review"></a>

<details>
<summary>DEPENDABOT_CHECK_FAILURES_REVIEW.md — historical package evidence</summary>

Original SHA-256: `ece3cccfba09857994443da68ed90b188b4b09aad7fa5c1ad9bb9fb613e27a75`.

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


</details>

<a id="record-ingestion-reliability-review"></a>

<details>
<summary>INGESTION_RELIABILITY_REVIEW.md — historical package evidence</summary>

Original SHA-256: `7eacf4b0d5db0697ff5b4e50650ec4f3eeeadb63511a6026aa896d4627175898`.

# Ingestion failure investigation — 17 October 2026

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

Branch `codex/ingestion-reliability`, based on reviewed CV batch `948eafa`.
Suggested estimate: 2 points. Local change only; no push, merge, deployment,
credential change, workflow dispatch or notification change.

## Verified evidence

- [Scheduled run #36](https://github.com/michael-mathenge/ajiri/actions/runs/39002307699):
  feed download passed; Send the feed to Ajiri failed with curl exit 22 / HTTP 404.
  Its response was PythonAnywhere's “Coming Soon” placeholder page rather than
  Ajiri's JSON API response.
- [Scheduled run #35](https://github.com/michael-mathenge/ajiri/actions/runs/38982100501):
  the same posting step returned the same host placeholder.
- [Manual run #37](https://github.com/michael-mathenge/ajiri/actions/runs/39023366845)
  and [scheduled run #38](https://github.com/michael-mathenge/ajiri/actions/runs/39025797298)
  succeeded later on the same main revision `3309803`. #38 was scheduled at
  13:40 Nairobi on 17 October and completed successfully in 9 seconds.

This identifies a host availability/routing response, not a demonstrated feed
parser defect or invalid-key response. The precise reason the host served its
placeholder (disabled app, routing, expiry or another host condition) is
**UNVERIFIED**. Later success establishes recovery at those run times, not a
guarantee that the host condition cannot recur. No failed run was rerun merely to
clear its red badge. Earlier failures outside the two inspected runs are not
claimed to share this cause.

## Local fix

The workflow checks out its reviewed code with read-only repository permission
and no persisted Git credential. Feed downloading retains bounded retries and
adds a retry-time budget. The job timeout is eight minutes to accommodate download,
readiness checks and the single bounded POST without the old retry budget overrun.

The dependency-free helper validates private configuration without logging it,
then probes `/api/health/` up to three times (10-second timeouts, 5-second waits).
Only HTTP 200 with the exact healthy JSON permits delivery. Persistent 404/HTML or
other unhealthy responses produce a short actionable error before any feed POST.

POST is attempted once, with the existing X-Ingest-Key/XML contract. HTTP 403,
HTTP 404 and uncertain network/server/invalid-response outcomes have distinct safe
messages. No redirects, raw HTML, exception details or secret values are logged.
Success prints only validated nonnegative integer created/skipped/flagged/notified
counters. Backend endpoints, parser, authentication, matching, alerts and schedules
are unchanged. The separate sweep workflow is unchanged; do not infer its health
from this ingestion investigation.

This improves resilience/diagnosis and avoids replaying ambiguous side effects;
it cannot repair an unavailable PythonAnywhere web app. Failures still alert you.

## Verification

- `python -B -m unittest discover -s .github/scripts -p 'test_post_feed.py'`:
  nine tests passed, with mocked network requests only. Cases include persistent
  and transient host failures, successful JSON validation, no uncertain POST replay,
  invalid configuration, secret-free output, 403/404 and redirect refusal.
- Backend `check`: no issues; migration drift check: no changes; full suite:
  202 tests, OK, one existing Windows symlink skip, 134.401 seconds. Real email
  disabled and dotenv disabled; no application backend files changed here.
- Frontend locked install, lint, 59 component tests and production build passed
  on bundled Node 24.19.0. Output matches the reviewed committed frontend_build;
  no frontend source/artifact change is needed for this workflow-only package.
- `git diff --check` passed. Workflow indentation/structure reviewed manually;
  no YAML/actionlint tool is installed, so that validator is **UNVERIFIED**.
- New helper not run against production, and new workflow not run on GitHub:
  **UNVERIFIED until the reviewed batch is merged**. Existing scheduled recovery
  was observed independently; no production repair is claimed from this local fix.

## Activation and operational checks

Held for the batch release. This workflow change takes effect only after review
and merge into the default branch. No PythonAnywhere code deployment, dependency
install or migration is needed for this helper itself. The CV batch separately
requires its reviewed migration before code activation.

After merge, inspect one normal scheduled ingestion run. Expect the helper tests
to pass, readiness to pass, and exactly one POST with the four integer counters.
Do not run local helper code with production secrets to test it.

If host 404s recur:

1. Open PythonAnywhere → Web. Confirm the existing app is enabled, expiry is in
   the future and its configured hostname is the intended Ajiri hostname.
2. Check the public `/api/health/` response and private platform error log. A host
   placeholder is not an instruction to create another app or rotate credentials.
3. Compare the repository's configured base URL privately; never paste secret
   values or environment content into chat or logs.
4. For planned maintenance, pause both ingestion and sweep writers, then resume
   after verification. Use the existing documented backup/deployment procedure.
5. After an uncertain POST, reconcile database/job counters and logs before
   manually dispatching again; a timeout does not prove nothing was processed.

Rollback is a reviewed revert of this workflow/helper pair. The old workflow
replays some POST failures and dumps raw response bodies, so prefer a forward fix.
No database rollback or history rewrite is needed.

## Development continuation

The personal CV builder is reviewed and retained in this local batch. The next
application package should explicitly select an owner-approved CV version, copy
its verified bytes into the application's existing private snapshot, and preserve
separate letter/email review before sending. It must never regenerate or silently
rewrite an approved CV. Real sending and automatic alerts remain separate gates;
neither is enabled by this workflow fix.


</details>

<a id="record-npm-dependency-build-review"></a>

<details>
<summary>NPM_DEPENDENCY_BUILD_REVIEW.md — historical package evidence</summary>

Original SHA-256: `37d7d616dfdbb2ab0208529e723c351777d79f47c32873eefb911e3bb991eaef`.

# PR22 dependency build repair

19 October 2026. Prepared from PR22 head 8cbcbf9, preserving its dependency
versions and lockfile. Includes the separately reviewed concurrency-test correction
from 47783e9 (PR24), with no application runtime or CI workflow changes.

The frontend failure was a committed-build mismatch after dependency updates.
Locked npm ci, lint, all 66 component tests and build passed on Node 24.19.0.
Generated frontend_build is refreshed and index.html LF-normalized. File/hash
comparison with dist passed; the generated entry is index-UFH464Hx.js, matching
the output expected by the failed CI run. No lockfile modification was needed.

On this combined branch, backend check and migration drift passed; all 210 Django
tests passed in 119.030s, with one existing Windows symlink skip. Real email was
disabled and only disposable test database/private media were used.

No main merge or production deployment. CI remains required before merging this
PR. Review PR24 separately for the shared test correction. Roll back dependency
manifest, lockfile and generated build together; no migration/data rollback.


</details>

<a id="record-operations-roadmap-review"></a>

<details>
<summary>OPERATIONS_ROADMAP_REVIEW.md — historical package evidence</summary>

Original SHA-256: `187ac50d8dfabab6ff3ec2b82c7d105bb0a5f637e163d5323bc9f2047dfb81ce`.

# Operations and staging package

21 October 2026. Branch `codex/jira-operations`, based on deployed PR #27 merge
`cc731976de13a5b5d561739def8dd93a26f70bff`. Local until its PR/activation evidence
is recorded in JIRA_ROADMAP_PROGRESS.md. No migrations or dependency changes.

## Changes

- AJ-35: existing `.env.example` now has a valid local mail sink and approved local
  CSRF origins instead of blank values that break fresh setup. The read-only
  `scripts/release_preflight.py` validates exact clean source, reviewed migration
  delta and safe committed build references. It does not install, migrate or reload.
  Actual runtime migration planning and off-server recovery verification remain
  mandatory. The current deployment checklist replaces stale canonical instructions;
  the original Checkpoint2 version is preserved in `docs/archive/`.
- AJ-36: isolated non-root/read-only-root container, private named data volume and
  loopback port8001, real mail forcibly off, no ingestion credential. Docker copies
  only application/build source and excludes credentials/databases/private files.
  The original learning container on port8000 remains intact. This local staging
  arrangement is not a second hosted public environment.
- Backup automation support: `verify_private_backup` independently verifies
  completed manifests, all hashes, database integrity and bounded safe archives;
  optional restoration uses a new private folder and writes completion evidence
  only after success. Partial/corrupt/traversal/existing destinations are rejected.
  No live restore or retention deletion. Git-free packaged snapshots explicitly
  report unverified source provenance instead of failing to protect local data.
- Container-safe private path guards distinguish the checkout root from a packaged
  `/app`; `/` is not treated as the entire application tree. Production Git checkout
  protection remains. Header settings tests no longer write unrelated platform logs.
- The SQLite last-slot regression permits only the service's documented bounded
  busy/no-handoff result, then reconciles the same losing key after workers finish.
  It still requires exactly one accepted attempt/provider call/quota claim. A
  deterministic exhausted-lock test proves zero handoff/budget consumption.
  No delivery service retry policy or real sender changed.
- A render boundary addresses the observed stale-tab lazy-chunk blank screen with
  a safe explicit reload action, unsaved-edit warning and no exception detail,
  authentication clearing or automatic mutation retry.

## Actual checks

```text
Docker Compose configuration/build                     passed
Fresh isolated staging migrations                      passed
Localhost:8001 health and UID10001/data/mail isolation   passed
manage.py check and migration drift in staging          passed, no changes
Full final allowlisted-image Django suite               296 passed, no skips, 79.426s
Native focused backup/preflight tests                   20 passed
Concurrency regression, five separate invocations       all passed
Actual private off-server backup verifier/restore       12 files, 212184 bytes; passed
Node24.19 locked install, lint, component tests/build    passed;102 tests,16 files
```

Two useful failures were fixed rather than hidden: the original packaged path
guard rejected every backup under `/`, and a contending SQLite caller can truthfully
return busy after bounded pre-network retries. The earlier Windows-locked Tailwind
binary remains untouched; the Node gate used the documented fresh isolated runner.
The final generated build is committed last. The clean-checkout release planner
must be executed after that commit, and remote CI must pass before merge.

## Operation and rollback

Read STAGING.md, BACKUP_AUTOMATION.md and the current DEPLOYMENT_CHECKLIST.md. Keep
production code/client pairs aligned; no schema reversal is needed for this batch.
The staging volume is preserved on routine compose down. Never use --volumes or
copy developer data over production. Sending and account credentials are unchanged.

Suggested sizing: AJ-35 **3**, AJ-36 **3**, backup/portability/concurrency repairs
**3**, recovery UI **2**. Do not mark remaining application/alert/privacy-export or
provisional integrations complete based on this package. Requirements for AJ-42–52
are documented separately; fake/live integrations are still pending.


</details>

<a id="record-privacy-registration-review"></a>

<details>
<summary>PRIVACY_REGISTRATION_REVIEW.md — historical package evidence</summary>

Original SHA-256: `e82e46cf34cb48db9ed7ae3b419b9a1c903305240479852ab491d16dcd1f814d`.

# AJ-24: registration privacy notice

20 October 2026. Local package, not yet deployed.

New public registrations require an unchecked explicit agreement and current
`privacy-draft-v1` policy version. Missing, declined or stale agreement is rejected
before account creation. An atomic account/profile write stores server time and
version; profile responses expose this only to its owner and make it read-only.
Existing accounts and admin-created accounts acquire no historical agreement.

`profiles.0006_privacy_notice` adds nullable timestamp and blank version only.
No User changes, existing-row data update, historical consent inference or email
permission is introduced. Old registration tabs must reload. Deploy the reviewed
server/client pair after the migration, with writers paused; rollback to the
preceding pair while retaining the additive fields and newer account records.

The public notice describes actual account/profile/document processing, current
providers, separate alert/application choices and backup limits. It stays DRAFT
for legal review; code approval is not legal certification. The statement must be
reviewed again when retention/providers/sending change. Registration agreement is
not a universal legal basis for every future use.

References: [ODPC rights](https://www.odpc.go.ke/rights-of-a-data-subject/) and
[ODPC consent guidance](https://www.odpc.go.ke/wp-content/uploads/2024/02/ODPC-Guidance-Notes-on-Consent.pdf).

Focused backend: 16 tests passed, including actual registration-to-approved-CV
journey; migration-drift check passed. Full backend: 286 passed, one Windows skip. Updated frontend: 100 tests, lint and build passed; exact commands and platform limitations are recorded in the roadmap progress report.


</details>

<a id="record-registration-cv-journey-review"></a>

<details>
<summary>REGISTRATION_CV_JOURNEY_REVIEW.md — historical package evidence</summary>

Original SHA-256: `60267fcaf47570a4913a1eac09d335a1f164fa05272413882d1456e8c6bcb157`.

# Registration to approved CV journey

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. Deployment of this document version/package is not verified here. Historical statements/results below are preserved; see AGENTS.md section 4.

17 October 2026. Synthetic test data only. No production writes, mail, applications,
credential changes or pilot allowlist expansion were performed for this review.

## Automated integration journey

`profiles.test_registration_cv_journey` follows real API endpoints with CSRF
enforcement, JWT login/refresh and temporary private storage. It does not use
`force_authenticate` or create the account directly in the ORM. Real sending is
off; verification email is captured with the existing test-only locmem sink.

The journey verifies weak-password rejection, successful registration, automatic
Profile creation, login cookie protection, CSRF bootstrap after login rotation,
verification request/confirmation, profile/skills save without uploading a CV,
explicit draft start, invalid-entry rejection without revision advancement,
revision 2 save, prevention of download before approval, explicit approval consent,
download ownership, private/no-store response, byte-for-byte stored snapshot match,
exact normalized text/order against the saved preview, refresh and repeat download,
logout and anonymous download denial. No Application exists at the end; the only
email attempt is the captured verification. The focused test passed in 2.628s.

Frontend locked install, lint, all 64 tests and build passed on Node 24.19.0. The
build matches the already committed assets. Backend check and migration-drift
checks passed. The first full suite stopped at an existing concurrent pilot-budget
test after 123 tests; that test and this journey then passed together (2 tests,
3.219s). The full repeat passed: 210 tests, 133.369s, one existing Windows symlink
skip. The intermittent concurrency failure remains an open reliability concern;
no delivery code was changed or claimed fixed here. This is an API
integration journey plus component regression coverage, not a single automated
browser journey. Visual navigation, mobile interaction, actual mail delivery and
Word pagination still need manual verification.

## Finding requiring review

Fresh Profile rows currently default both `notify_email` and `notify_in_app` to
True. The first journey run exposed this mismatch with the agreed opt-in direction.
No real alert was sent. The continued test explicitly saves both False, exercising
the existing user preference path rather than concealing the default issue.

Proposed correction: alter both BooleanField defaults to False with an additive
AlterField migration, leaving existing rows untouched. No historical consent may
be inferred. This is a design proposal only: model/migration changes await review.
Separately review whether existing True rows need a consent confirmation workflow.

## Manual browser journey before applying

1. Keep the existing approved CV/account intact. Open a separate private browser
   session. Register using an owner-controlled test address and a new password,
   entered privately by Michael. Expect redirect to Login, no automatic email.
2. Log in, open Profile, record the initial alert checkbox states, switch both off
   and save synthetic headline, summary, location and skills. Do not upload a CV:
   confirm the builder supports users starting from information alone.
3. Open Build and review my CV. Expect no automatic draft until Start my CV.
   Start and verify the copied profile details, then fill synthetic experience,
   education, certification and project data. Leave unused optional sections empty.
4. Leave an added Employer blank and save. Expect validation without losing edits.
   On currently deployed 641cdfb the summary is above the form; the local feedback
   fix makes it scroll/focus automatically after its own reviewed deployment.
5. Correct the field and save. Compare every preview section with the inputs.
   Confirm approval is disabled until review consent is checked. Approve and
   download; compare Word text, order and layout with the saved revision.
6. Edit and save a new revision. Confirm it requires new approval and the earlier
   approved download remains unchanged. Reload only after saving, then log out/in
   and confirm the saved draft and version remain accessible to their owner.
7. Stop before Apply. Do not create applications, send employer mail or turn on
   alerts. A different signed-in owner must not access another user's CV download.

The live owner-only email pilot cannot verify a fresh account: it requires both the
existing approved owner ID and exact recipient. Do not widen the allowlist, reuse
the existing owner's identity or mark a test user verified in the database. The
verification leg above is proven with captured email; a fresh live inbox test
requires a separately reviewed pilot change. Browsing and personal CV preparation
remain available to unverified accounts.

## Status

Local test addition only, pending review. No push or deployment. No schema change.


</details>

<a id="record-ui-feedback-review"></a>

<details>
<summary>UI_FEEDBACK_REVIEW.md — historical package evidence</summary>

Original SHA-256: `361f0abf16e1841a2565fe3f96952cd61774e42a6f47c72b2beed36d4acd0591`.

# UI feedback review — 17 October 2026

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

One local frontend package, three approved steps. Base: main `3309803`.
Branch: `codex/ui-feedback-polish`. No push, deployment, real email, backend
behavior, dependencies, migrations, auth interceptor, CI or production changes.

| Step | Result | Suggested points |
|---|---|---|
| Empty-profile job cards | Add skills link instead of a misleading score; genuine zero scores preserved | 2 |
| Registration errors | Bordered summary, spaced field messages, visible invalid input borders; all errors and associations preserved | 1 |
| Account email retry wait | Readable minutes/seconds, disabled submission until Retry-After expires, manual retry only | 2 |

The jobs screen reads `/profiles/me/` once per mount for all cards, independently
of jobs pagination/filter requests. Failed/pending profile reads withhold scores
and empty-profile advice without blocking jobs. Returning from Profile refetches.
Job detail and historical notification scores are unchanged.

The countdown accepts seconds and HTTP dates. It accounts for elapsed time in a
background tab. Invalid/missing headers show generic guidance. Reloading resets
the display; server throttling remains authoritative. No limit is bypassed and no
email or mutation is automatically retried. Delivery remains unconfirmed by this
package; the earlier 429 does not prove repeated clicking or a successful send.
The queued new-user alert-default change remains outside this UI package.

## Actual verification

Executed in the isolated checkout on 17 October 2026:

- Backend with dotenv disabled, DEBUG=True, REAL_EMAIL_ENABLED=False:
  `python manage.py check`: no issues;
  `python manage.py makemigrations --check --dry-run`: no changes;
  `python manage.py test --noinput`: 178 tests, OK, one Windows symlink skip.
- Frontend using bundled Node 24.19.0 and npm CLI explicitly:
  `npm ci`: 180 packages installed, zero reported vulnerabilities;
  `npm run lint`: exit 0;
  `npm run test -- --run`: 51 tests across eight files passed;
  `npm run build`: passed, Vite 8.3.4.
- Focused tests cover empty versus populated skills and failed profile fetches,
  all registration messages/associations, 429 submission blocking and manual
  expiry, background elapsed time, malformed headers and HTTP date parsing.
- Browser visual QA: **UNVERIFIED**. The browser's localhost address reached a
  different app rather than this checkout; no actions were taken in that app.
  Light/dark/mobile appearance and real screen-reader behavior need manual review.

## Review steps

Use the isolated checkout; leave the original checkout's dirty files untouched.
In PowerShell:

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-frontend
$env:PATH = 'C:\Users\micha\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;' + $env:PATH
node 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js' run test -- --run
```

Expected: 51 tests pass and the command exits. For a local development preview,
use your normal local backend and `npm run dev`; never point it at production.

1. With a local test account containing no skills, browse jobs. Cards offer
   “Add skills to see your match”, linking to Profile. Add a skill and return:
   scores appear, including genuine zero matches. Simulate a failed profile GET:
   jobs remain available without a guessed score or empty-profile claim.
2. Submit registration with server-rejected test values. Every returned error is
   readable in the bordered summary; affected inputs have visible borders and
   associated descriptions. Check both themes and a narrow phone viewport.
3. With a mocked/local 429 and `Retry-After: 65`, request an account email.
   Expect “1 min 5 sec”, a disabled button and no further POSTs. After expiry,
   the button enables; no POST occurs until clicked. Do not generate real email
   requests to test limits. Reload resets the display, not the server limit.

## Rollback and review boundary

Review the source and matching final committed `frontend_build` together. Revert
this UI package and rebuild together if needed; no database rollback is needed.
Existing root AGENTS changes, lockfile, coverage data, Git configuration and stash
were preserved. Stop here for review; publishing/deployment requires authorization.


</details>

<a id="record-ui-polish-phase-c-review"></a>

<details>
<summary>UI_POLISH_PHASE_C_REVIEW.md — historical package evidence</summary>

Original SHA-256: `732da68e6615e811f5810205586a38c894d229d0264b2f4d2c43007dcd1836fe`.

# Phase C UI polish and download names

19 October 2026. C3, local only; no deployment or schema change.

The existing empty-skills branch now uses the exact text "Add skills to see
matches". True zero scores remain visible when skills exist; failed/unknown
profiles do not imply no skills. FormErrors maps known keys to readable labels,
capitalizes fallback labels, spaces field groups and displays each message as its
own list item. Existing field error IDs/associations remain unchanged.

## Download naming decision implemented

Previous behavior mixed Ajiri_CV.docx, generic browser fallbacks and private UUID
storage filenames in application response headers. Browser code already honored
Content-Disposition; new regressions verify plain and UTF-8 headers and fallback.

New headers use all name parts: Name_CV.docx, Name_CV_Company.docx and
Name_Cover_Letter_Company.docx. Personal name comes from the approved contact
snapshot. Application name comes from the current account, with current company
last. Components use Unicode NFKC, remove controls/unsafe punctuation/path
separators, normalize whitespace to underscores and cap each at 60 characters.
Empty names/company become Applicant/Company. Windows device-name components are
disambiguated. Django safely encodes Unicode Content-Disposition.

Existing uploaded CVs use neutral Uploaded_CV.pdf/.doc/.docx, preserving the
supported file extension; unexpected legacy extensions use .bin safely. Storage
names, ownership, bytes and approval hashes are unchanged. Application labels may
change after account/company edits; that does not rewrite their documents. No
storage IDs are needed in visible download labels. Filename metadata is not a
historical provenance guarantee. Duplicate human names may cause the browser to
add its ordinary local duplicate suffix.

## Verification and manual review

Focused backend: three tests passed (0.542s); focused/full frontend run: 71 tests
passed. Full package check/drift/Django/npm ci/lint/test/build results are recorded
in CHECKPOINT4_PHASE_C_REVIEW.md. Real phone/browser visual layout is UNVERIFIED.

1. In local Ajiri, clear skills and save. Job cards offer the profile link; add a
   nonmatching skill and confirm the genuine zero score returns.
2. Submit registration with several server errors. Verify Password/Email labels,
   readable spacing, every message, keyboard focus and input associations. Repeat
   with a nested CV entry error; entered content must remain intact.
3. Download a personal approved CV with a multi-part name. Confirm company-last
   names for both application documents and a neutral label for an uploaded PDF.
4. Change the account name and download an existing application again: its label
   may change, but Get-FileHash against the earlier download must match.
5. Check a Unicode name, punctuation-only company, narrow screen and light/dark
   modes. Never put real personal document contents into the review report.

Rollback paired server/client/build. Retain all files, approvals and newer writes;
no database rollback is needed. Reverting headers reintroduces old naming only.


</details>

<a id="record-certificates-decisions"></a>

<details>
<summary>CERTIFICATES_DECISIONS.md — historical package evidence</summary>

Original SHA-256: `aba342706d59f159041432fb55bf7967a756ffaf648e1bfbda96c728f21fc415`.

# Certificate upload decisions

Historical design matrix from 19 October. AJ-79 subsequently gained an inactive
implementation on `codex/backend-inactive-20261031`; "not implemented" and approval
cells below are the original snapshot, not the current code inventory. Use
[open decisions](../DECISIONS_PENDING.md) for genuine remaining capacity/scanner/
retention facts and [next actions](../docs/ROADMAP_NEXT_ACTIONS.md) before rebuilding.

19 October 2026. D2 document only; no upload API, schema, migration, scanner,
retention job or employer sharing implemented. Read with CERTIFICATE_UPLOAD_DESIGN.md.
Each default below is a PROPOSED design assumption, not approval to build or release.
Michael must approve the choices before implementation; a changed choice requires
its impact on storage/schema/privacy to be reviewed again.

## Approval matrix

| Choice | Options | Recommendation and proposed default | Approval |
|---|---|---|---|
| Formats | PDF only; PDF plus JPEG/PNG; office documents | PDF only initially; images/office formats deferred | Pending |
| Per-file size | 1 MiB; 5 MiB; 10 MiB | 5 MiB (5*1024*1024 bytes), bounded while reading | Pending |
| PDF content validation | Extension/MIME; bounded signature/structure validation; sanitizer/scanner | Reuse reviewed PDF content validation, require PDF extension and content, reject empty/spoofed/oversized/truncated files; MIME alone never sufficient | Pending |
| Malware handling | Content checks only; local scanner/sanitizer; external service | Private pilot only with explicit content-check limitation, attachment-only download; no external transfer or scanner dependency | Pending; public release needs risk review |
| Owner quota | Unlimited; five files/20 MiB; stricter two-file pilot | Five active files and 20 MiB per owner, one file per certification; shared account disk quota reviewed before release | Pending |
| Private storage | Existing private MEDIA_ROOT; public media; third-party bucket | Existing private storage, UUID paths, no original filename, no public mapping | Pending |
| Ownership | Profile owner only; share links; employer access | Authenticated owner only; cross-owner/unknown returns 404, anonymous denied | Pending |
| Upload trigger | Automatic on selection; explicit Upload | Save certification text first, then explicit Upload; file selection alone transmits nothing | Pending |
| Meaning | Verified qualification; unverified supporting evidence | Explicitly unverified evidence; no OCR, qualification inference or URL fetching | Pending |
| Download | Inline PDF; private attachment | Attachment-only, no-store, nosniff, neutral certificate.pdf; integrity checked | Pending |
| Replacement | Overwrite in-place; atomic pointer swap | Validate new UUID file, swap DB reference atomically, remove old bytes after commit | Pending |
| Explicit removal | Immediate silent removal; confirmation | Confirm loss of active private evidence; delete metadata atomically and bytes after commit | Pending |
| Certification removal | Keep orphan; remove silently; confirm and remove together | Warn before draft save and remove associated evidence atomically with entry removal | Pending |
| Account deletion | Retain active evidence; cascade ownership | Cascade metadata and remove active files after commit; backup limits disclosed | Pending |
| Backups | Exclude certificates; include private media | Include in paused-writer media backups and isolated restore rehearsal | Pending |
| Backup retention | Immediate erasure everywhere; approved expiry; current draft policy | Existing 30-day DRAFT, report-only candidates; no automated pruning or promise of immediate backup erasure | Pending privacy/retention decision |
| Employer sharing | Automatically attach; share link; separately select later | Upload never authorizes sharing; no embedding/public link/bundling in CV or application, no email attachment now | Pending; prohibition retained by default |
| Schema | Embed in CV JSON; additive evidence table | Separate additive CertificateEvidence table described below; no User change or backfill | Pending exact schema |
| Concurrency | Last write wins; checked version and atomic quota | Expected workspace revision plus expected evidence ID/hash for replacement; serialize quota checks per owner | Pending |
| Crash/orphan cleanup | Automatic delete sweep; report-only reconciliation | Report-only; remove only request-owned uncommitted files on ordinary failure | Pending |
| Rollback | Reverse populated schema; retain data and roll code back | Retain table/files/newer writes; disable feature and roll reviewed client/server pair back | Pending |

Quotas concern active evidence, not backup/restore copies or immutable CV approvals.
Five files do not guarantee total hosting capacity: PythonAnywhere's recorded account
quota is small. Check account quota and projected users/backup space privately before
release. Do not use shared filesystem free space as account quota evidence. Lower
pilot limits may be chosen; never silently increase them to solve an error.

## Additive schema for explicit approval

Propose profiles.CertificateEvidence: UUID primary key (uuid4), non-null Profile FK
CASCADE, non-null certification_id UUID with no default, non-null private document
FileField max_length=100, SHA-256 CharField(64), positive size_bytes integer, and
created_at timestamp. Unique (profile, certification_id); size constrained to
1..5 MiB. Existing certification entry UUIDs must validate and belong to the saved
owner draft. No original name, verified flag, extracted text or historical backfill.
Existing accounts/documents gain no evidence records automatically. Existing CV
JSON and immutable approval snapshots stay unchanged.

The new table is additive and old code ignores it. Exact migration and deletion
hooks require separate review; Phase C creates none. Reversing a populated table
would destroy evidence, so it is not routine rollback. Keep schema and files while
disabling new routes/UI; retain newer database writes. Removal from active storage
is irreversible after commit and must be clearly confirmed, not framed as trash.

## Storage and API rules for the later package

Proposed owner-scoped list/upload/replace/download/remove routes under
/api/profiles/me/ require current auth, existing throttling and private/no-store
responses. Return safe evidence ID/size/status metadata, never physical paths or
public URLs. Selecting a file is local only; cancellation must preserve draft text.
Wrong owner receives no existence disclosure.

Check bounded content and quotas, then conditionally lock the owner's existing
CVWorkspace in a transaction, recheck certification membership/revision and sum
active evidence bytes/count. SQLite requires a real conditional write; do not rely
on select_for_update alone. Competing last-slot uploads must not exceed quotas.
Stage new bytes under a fresh UUID before the swap. Rollback cleans only that
request's new file; on_commit removes replaced/deleted active bytes. Reconcile GET
metadata/hash after an uncertain response; never automatically replay a mutation.

PDF content checks do not prove a PDF safe to open or free of active content.
Attachment-only delivery limits browser rendering, not malware risk in a viewer.
No dependency or external scanner is approved; propose any additional validation
capability before adding it. Scanner/sanitizer services would require separate
hosting, cost, data-transfer and privacy approval.

## Acceptance and tests before release

Test owner/anonymous/cross-owner access; no path disclosure; valid, HTML/executable
spoof, empty, truncated and oversized PDFs; path/control filename input; quota and
simultaneous last-slot uploads; stale replacement/removal races; DB/file failure,
rollback and on-commit cleanup; crash reconciliation; no automatic retries; download
hash; no changes to approval bytes/revision; no email/application attachment.
Rehearse backup/restore with evidence and confirm quota accounting after restore.

Manual checks: narrow phone layout, touch file picker, cancel, explicit upload,
progress, retry guidance, replace/remove confirmation and retained unsaved text.
Review longer-term retention/deletion/privacy and acceptable malware risk before
public availability. None of these design defaults enables certificate uploads.


</details>

<a id="record-dependency-advisories"></a>

<details>
<summary>DEPENDENCY_ADVISORIES.md — historical package evidence</summary>

Original SHA-256: `7537e1a97e363ffb51506230d0b6649a37b182c36263bf4eb5100d8f8747bdd8`.

# WP16 dependency advisory reconciliation

Historical 16 October scan and source assessment, not a current vulnerability
clearance or deployment pin. Later local evidence recorded five npm advisories;
the 1 November offline install did not perform a new audit. Recheck current
advisories in an authorized maintenance package; do not downgrade to this old SHA.

16 October 2026. Deployment base stays c4b93647f65618e8d13f9baa47ded6d22a28f0fb.
No requirements file changed: Dependabot commit 91ce77f already upgraded runtime
and dev pins consistently. Scanner pip-audit 2.10.1 ran against BOTH requirement
files, not just installed packages. Exact commands/output are in
audit-evidence/2026-10-16/{production,development}.txt. Both exit 0 with
`No known vulnerabilities found`. This is an advisory snapshot, not proof of safety.

The original local venv still held Django 6.1/PyJWT 2.13.0. It was preserved;
tests use a new isolated Python 3.12 environment with Django 6.1.2,
PyJWT 2.15.1 and SimpleJWT 5.5.1 from the existing requirements. `pip check` reports
`No broken requirements found.` Scanner resolution and installed-runtime scans
are different inputs; never infer one from the other.

## All 15 historical findings

Original scan reported Django 6.1 and PyJWT 2.13.0. The table gives the current
primary advisory's fix metadata, not a claim that every reported issue was reachable.
Read each record at https://api.osv.dev/v1/vulns/ID (replace ID with its table ID),
backed by https://github.com/pypa/advisory-database .

| ID | Old package | Fix metadata | Ajiri applicability at the old pins |
|---|---|---|---|
| PYSEC-2026-3717 | Django 6.1 | Current record: 5.2.17 / 6.0.8 | GeoDjango deeply nested geometry denial of service; no GIS app/fields in Ajiri. Historical scanner also listed 6.1.1, absent from current record: metadata discrepancy retained, not silently asserted fixed by that version. |
| PYSEC-2026-4140 | PyJWT 2.13.0 | 2.14.0 | Unknown-kid JWKS request amplification; Ajiri uses symmetric HS256, no JWK_URL. Not an observed path. |
| PYSEC-2026-4141 | PyJWT 2.13.0 | 2.15.0 | Recursive pre-verification payload parsing; no app-level unverified/JWKS parsing found. Dependency path reviewed; no exploit asserted. |
| PYSEC-2026-4142 | PyJWT 2.13.0 | 2.14.0 | Deep token headers can enter JWT validation from public requests; relevant defensive upgrade. |
| PYSEC-2026-4143 | PyJWT 2.13.0 | 2.14.0 | Empty JWK HMAC keys; no JWK configuration in this app. |
| PYSEC-2026-4144 | PyJWT 2.13.0 | 2.14.0 | JWKS redirect following; no remote JWKS configured. |
| PYSEC-2026-4145 | PyJWT 2.13.0 | 2.14.0 | Mutated asymmetric PEM treated as HMAC; server-controlled symmetric key, not applicant-supplied PEM. |
| PYSEC-2026-4146 | PyJWT 2.13.0 | No explicit fixed event; last_affected=2.13.0 | Reused mutable verification options; no shared app options switching from unverified to verified found. 2.15.1 outside reported affected range; do not invent a fix version. |
| PYSEC-2026-4147 | PyJWT 2.13.0 | 2.14.0 | Noncanonical signatures versus raw-token revocation; relevant to authentication review, but SimpleJWT blacklists jti, not a raw-token string list. Keep replay tests. |
| PYSEC-2026-4148 | PyJWT 2.13.0 | 2.14.0 | PEM-format regex resource exhaustion; key is controlled configuration, no public key input. |
| PYSEC-2026-4149 | PyJWT 2.13.0 | 2.14.0 | DER public key used as HMAC secret; no DER-key authentication configured. |
| PYSEC-2026-4150 | PyJWT 2.13.0 | 2.14.0 | BOM/key-format bypass; server-controlled symmetric key limits the identified key-input path. |
| PYSEC-2026-4151 | PyJWT 2.13.0 | 2.14.0 | Public JWK container accepted as HMAC secret; no JWK containers accepted by Ajiri. |
| PYSEC-2026-4152 | PyJWT 2.13.0 | 2.14.0 | Malformed RSA JWK aborts JWK set; no remote JWK set configured. |
| PYSEC-2026-4183 | PyJWT 2.13.0 | 2.15.0 | Mismatched OKP private/public JWK material; no proof-header/private-JWK import flow in Ajiri. |

Evidence: config/settings.py SIMPLE_JWT has no algorithm override or JWK_URL;
installed SimpleJWT TokenBackend defaults HS256 and passes its own decode options.
No app-level jwt.decode/options/JWK imports were found. This is static applicability
assessment, not penetration testing or a waiver to retain vulnerable versions.

## Why results differ

The recorded 15-finding snapshot used older pins, while today's requirements resolve
the already-merged patch/minor upgrades. Current OSV metadata also differs for the
Django record. Do not attribute the change solely to new publication dates. A prior
claimed clean Python scan without saved commands/output is UNVERIFIED; the older
audit's npm clean result and pip check result were not Python vulnerability scans.
No major upgrade, auth logic change, ignore list or automatic audit fix was needed.

Deployment-stage reminder: this local evidence does not establish which versions
Michael has installed on production. He owns c4b9364 deployment; no silent SHA change.

## Executed WP16 gates

Python 3.12.6, Django 6.1.2, PyJWT 2.15.1: pip check/check/migration check pass;
90 tests run, 89 pass, one Windows symlink skip. Production-like check --deploy
retains only intentional W005/W021 (no subdomains/preload). Node 24.19: npm ci,
lint, 25 component tests and build pass. No frontend package regeneration.


</details>

<a id="record-migration-design-3b1"></a>

<details>
<summary>MIGRATION_DESIGN_3B1.md — historical package evidence</summary>

Original SHA-256: `6c2e872d3452034ac6e857c6e1dccaa86078e4cdd7165d959062a12298a32c5c`.

# Checkpoint 3B1 migration design — decisions recorded; implementation gated

16 October 2026. Proposal only: no model field, migration or Phase B feature was
implemented. Approval of this document is a separate gate before schema work.
No AUTH_USER_MODEL definition or migration-history edits. All proposed tables and
columns are additive; no historical consent, verification or delivery backfill.

## 1. Account verification: prefer Profile, no User change

| Proposed field / location | Type | Null / default | Existing rows / purpose |
|---|---|---|---|
| profiles.Profile.email_verified_at | DateTimeField | null=True, blank=True, default=None | Every existing profile remains explicitly unverified; never infer ownership from past login or preferences |
| profiles.Profile.verified_email | EmailField(max_length=254) | null=False, blank=True, default='' | Empty for existing profiles; bind proof to the normalized email actually verified, so changing email never inherits old proof |

Verification is true only if timestamp exists AND verified_email matches the current
account email under the same normalization used by registration. A timestamp alone
must not survive an email-address change as proof. No new required registration
field, forced reset or is_active backfill is proposed. Existing accounts can log in,
browse, edit profiles and draft; real outbound application email is gated on proven
mailbox control in Phase B, as approved for the design. This does not certify legal consent.

Alternative without migration: an expiring signed session/cookie proves only that
browser's recent verification and does not provide durable cross-device/admin state.
An external verification store adds operational dependencies. Prefer the two Profile
fields; no per-account database token is necessary.

Reversibility: adding nullable/defaulted columns is compatible with old code. Old
code ignores them on rollback; LEAVE columns/data in place. A reverse migration
could drop proof, is destructive, and is not a routine rollback. No row rewritten
except future user-initiated verification. Missing Profile must fail safely until
the existing profile-creation flow is repaired; do not auto-mark verified.

## 2. Password reset: no reset-token table

Recommend Django's PasswordResetTokenGenerator, finite PASSWORD_RESET_TIMEOUT
(approved design: 30 minutes), owner mailbox delivery and anti-enumerating request responses.
Token derives from existing account state; store/send no raw token in DB/logs.
Password change invalidates previously issued reset tokens. Endpoint limits must
use existing throttling and independent delivery budgets. Tests must cover weak
password validation, expiry, replay and generic responses for unknown addresses.

The reset endpoint is NOT implemented in Phase A. A successful reset should
blacklist that user's outstanding refresh tokens through the existing blacklist
models, not a migration or new token lifetime. Already-issued access tokens can
remain valid for their existing 15-minute lifetime. Immediate access-token revocation
would need an explicitly approved additional mechanism; do not claim it for free.
No account-wide resets, historical password changes or auth-model edits.

Verification token proposal: Django timestamp signing with a separate purpose salt,
bounded age (approved design: 24 hours), account ID, normalized candidate email, and fingerprint
of verification state. Do not reuse reset tokens for verification. Recheck the account's
current email and atomically update Profile only if the previously signed state still
matches. Repeated verified clicks are a safe no-op; changed/expired state requires a
fresh link. Token material is a credential: never log it or place it in analytics.

Stored-token alternative: a purpose-bound hash, expiry, used_at and user FK would
allow explicit per-link revocation but adds sensitive state, cleanup and migration
complexity. Recommend no stored-token table at launch. Expiry defaults and reset access-token grace are design-approved; exact client/API
contracts and implementation still require the separate Phase B build prompt.

## 3. SMTP/API delivery ledger and shared quotas: jobs app

Use new tables instead of modifying Application.status or Notification history.
This retains the current application state choices while recording uncertainty.

### jobs.DeliveryAttempt (proposed)

| Field | Type / constraints | Null / default |
|---|---|---|
| id | UUID primary key | non-null; uuid4 for new rows |
| user | FK existing user, SET_NULL | null=True; None |
| application | FK jobs.Application, SET_NULL | null=True; None |
| notification | FK jobs.Notification, SET_NULL | null=True; None |
| channel | CharField(24), application/alert/email_verification/password_reset | non-null; no database default; explicitly provided on creation |
| state | CharField(24), reserved/accepted/definite_failure/unknown | non-null; 'reserved' |
| idempotency_key | UUID unique | non-null; uuid4 |
| recipient_digest | CharField(64), normalized-address keyed digest | non-null; no default, supplied by sending service |
| provider_message_id | CharField(255) | non-null; '' |
| failure_category | CharField(32), allowlisted category only | non-null; '' |
| created_at | DateTimeField(auto_now_add=True) | non-null; creation time for new rows |
| resolved_at | DateTimeField | null=True; None |

No body, subject, CV bytes, raw provider response, token or credentials. The digest
is pseudonymous personal data, not anonymization; key rotation and metadata retention
need legal/operations review. Use the application/notification link plus provider
receipt for reconciliation. No original recipient address is duplicated in this
ledger. If future operational needs require it, request approval first.

Proposed creation rules: application delivery has an application link; alert delivery
has a notification link; email_verification/password_reset have a user link and
neither application nor notification. Later SET_NULL erasure is allowed. Never store
verification/reset links or tokens in the ledger. Exact database/service constraints
for nullable historical links require review before generating migrations.
A partial uniqueness constraint permits at most one reserved/unknown attempt per
application or notification. Unknown outcomes must be reconciled before creating a
new attempt; a definite failure may retry with a new attempt. Accepted application
attempts plus existing Application.status prevent repeat send. For alerts, correct
only future sent_email flags after acceptance; no resend/relabel of historical rows.

### jobs.DeliveryDailyBudget (proposed)

| Field | Type / constraints | Null / default |
|---|---|---|
| id | BigAutoField primary key | non-null; automatic |
| scope | CharField(64): global or user:<id> | non-null; no default |
| day | DateField, Africa/Nairobi calendar date | non-null; explicitly supplied |
| application_reserved | PositiveIntegerField | non-null; 0 |
| alert_reserved | PositiveIntegerField | non-null; 0 |
| account_reserved | PositiveIntegerField, shared verification/reset allocation | non-null; 0 |

Unique(scope, day), nonnegative counters and indexes supporting that key. New empty
tables have no impact on existing rows. Do NOT prepopulate rows or derive past send
counts from sent/status history: console-only success was not real delivery.

Reserve global/application capacity and user capacity atomically with conditional
updates in one short DB transaction; create the attempt in that transaction. Enforce
10 applications/user/day and 200 total attempts/day: 150 applications, 30 account
emails and 20 alerts. Use Africa/Nairobi calendar days; no automatic borrowing
from another allocation. Account requests also require per-user throttling. At caps,
preserve application drafts and show availability guidance; reset requests retain
generic anti-enumeration responses. Network I/O occurs after
commit, never while holding SQLite locks. Accepted/unknown outcomes consume capacity. Michael approved the clarification: for an attempts-based cap, count
definite provider failures once a network attempt is made too; release only
reservations cancelled before any send attempt. This supersedes the earlier failure-refund proposal; retries cannot evade the provider allowance. No automatic unknown retry or midnight refund
of an old unresolved attempt. Bounded alert retries only after definite failure.
DRF file-cache counters are not the hard quota and cannot replace these tables.

Delivery metadata retention is approved at 30 days, subject to privacy review.
This covers attempts and daily budget metadata, not payloads or authentication tokens.
Unresolved outcomes at expiry need a reviewed minimization/reconciliation policy so
purging a ledger cannot unlock duplicate delivery. No purge command is authorized. Do not delete
attempts/budgets under WP22 backup retention: that command never prunes anything.
No hourly table is proposed; existing request throttles remain independent of daily
accepted/uncertain delivery quotas. If a hard rolling-hour quota becomes required,
design it separately before implementing rather than approximating it silently.

Alternative without migration: disable real delivery and retain manual owner-only
pilot controls. File/memory caches and provider daily caps cannot reliably enforce
shared user/global reservations or reconcile unknown outcomes. Provider idempotency
is useful if supported, but acceptance is not inbox delivery or exactly-once proof.

## 4. Deployment and rollback compatibility

1. Michael reviews exact schema/constraints and policy first. Future migrations add
   only these columns/tables; makemigrations is forbidden in this Phase A design work.
2. Back up, stage migration source, pause sending/sweeps, apply migrations, then
   activate reviewed Phase B code. Old code bypasses quotas/verification, so do not
   run old and new senders concurrently. No destructive data migration/backfill.
3. Keep real delivery operator-disabled until provider connectivity, sender/domain,
   global cap, application/alert allocation and account verification are approved.
4. Rollback: stop real sending first, preserve ledgers/proof, restore previous reviewed
   code/config without reversing additive schema. Do not return to old console code
   while presenting a false real-delivery success claim. Reconcile unknown attempts
   before resuming. Never roll back DB over newer writes.

Mechanically reversing the new tables/columns would lose evidence and is destructive;
separate explicit approval and an export/recovery policy would be required. Privacy
deletion later must cover ledger linkability/retention and backups under legal review.

## 5. Decision record — 16 October 2026

Michael approved, in this chat, DESIGN ONLY:

- The two Profile verification fields; all historical users remain unverified.
- Reset expiry 30 minutes, existing outstanding refresh tokens blacklisted after
  reset, existing access tokens retaining their up-to-15-minute grace.
- Purpose-bound signed verification links, 24-hour expiry, no token table.
- Unverified users can log in/browse/edit/draft but cannot send real applications.
- Delivery ledger, shared quotas, uncertainty counting and no automatic unknown retry.
- Ten applications per user/day; 200 global attempts/day with fixed 150/30/20
  application/account/alert allocation; cap UX and 30-day metadata retention subject
  to privacy review. Verification/reset categories and account budget extension
  explicitly approved afterwards. No actual migrations authorized by these answers.

Read-only provider evidence: a credential-free curl from Michael's PythonAnywhere
console returned HTTP 401 at https://api.brevo.com/v3/ on 16 October. DNS/TLS/HTTPS
reachability works; this does NOT prove authenticated API sending or account approval.
Brevo UI showed a 300-email daily allowance and one verified freemail sender, with
freemail compliance warning. Domains page had no configured sending domain. No keys
were opened, no email sent and no provider configuration changed.

The website remains https://mathenge.pythonanywhere.com. It is not a DNS-controlled
sending identity for this project. Michael will obtain domain/DNS control later;
no assumption of ajiri.co.ke ownership. Public email activation is blocked pending
sender authentication. Owner-only pilot allowlisting is recommended but NOT yet
explicitly approved; do not interpret 'continue' as delivery/credential authorization.
Console backend remains unchanged.

## 6. Remaining design details and build gate

- Review exact creation/partial uniqueness constraints for account-message attempts,
  repeated requests, null links after deletion, and concurrency; account messages
  must not reuse application/notification-only constraints.
- Select per-user account-email request limits and retry/backoff bounds. No new
  numeric default is approved by this document.
- Confirm metadata expiry handling for unresolved attempts, digest key rotation,
  provider receipt reconciliation, bounce/complaint handling and legal retention.
- Obtain controlled sending domain verification and explicit owner-only pilot policy
  before real delivery. Michael configures all credentials privately.
- Future tests: old rows remain unverified, migration/rollback compatibility,
  reset/verification expiry/replay/email change, overlapping budgets and Nairobi day
  rollover, fixed category capacity, repeated account requests, definite/ambiguous
  failures, alert opt-in, retention and erasure.

Phase B remains STOPPED until Michael sends a separate implementation prompt and
approves exact migrations. Domain setup can proceed independently; no production,
model, migration, auth, SMTP or provider-setting change is made in this update.

## 7. Subsequent schema-only build authorization

Michael explicitly authorized implementing the verification and delivery-budget
migrations with tests, keeping console email unchanged, no push/deployment, and
stopping after the package. This supersedes the earlier implementation gate only
for these additive fields/tables, not transport/accounts endpoints or sending.
See CHECKPOINT3B_SCHEMA_REVIEW.md for implemented constraints and remaining service
policy decisions. michaelmathenge.dev was confirmed active in the signed-in
Namecheap account, with Namecheap BasicDNS; DNS authentication in Brevo is pending.
No DNS/provider writes or secret access were performed.

## 8. Subsequent dormant transport/service authorization

After approving the schema review, Michael approved the isolated transport and quota
service package and confirmed that definite failed provider attempts count against
capacity. This does not authorize endpoints/tasks integration, real sending, provider
credentials, DNS changes, push or deployment. See CHECKPOINT3B_DELIVERY_REVIEW.md.

## 9. Accounts flow and approved reset-revocation extension

Michael approved reset/verification implementation with real delivery disabled, then
explicitly approved the discovered revocation fix: nullable Profile.password_reset_at,
password-bound new refresh claims and rejecting legacy refresh tokens after reset.
profiles/0004 adds DateTimeField(null=True, blank=True, default=None), no historical
backfill. New reset writes the marker; old rows otherwise stay None. No User change.
New auth code must follow migration. Rollback after resets MUST preserve the marker
and refresh guard: old code would ignore the marker and accept legacy untracked
refresh tokens. Dropping the marker loses revocation evidence and is destructive,
so code rollback is limited to retaining the guard or a separately reviewed session
invalidation plan. Existing access tokens keep their approved 15-minute grace.
See CHECKPOINT3B_ACCOUNTS_REVIEW.md for implementation, tests and activation gates.


</details>
