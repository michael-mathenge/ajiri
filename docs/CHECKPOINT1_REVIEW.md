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

- [Desktop plans](screenshots/checkpoint1-plans-desktop.jpg)
- [Profile at 375px](screenshots/checkpoint1-profile-375.jpg)
- [Multiple registration errors at 375px](screenshots/checkpoint1-registration-errors-375.jpg)

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
