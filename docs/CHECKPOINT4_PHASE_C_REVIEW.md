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
