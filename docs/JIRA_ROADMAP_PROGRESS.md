# Jira roadmap execution

20 October 2026. Source: [AJ board 34](https://michaelmathenge.atlassian.net/jira/software/projects/AJ/boards/34/backlog).
Baseline: remote main and recorded deployed release
`647449851c98f5b22e0419db673f2500c86d1e86`.
Working branch: `codex/jira-roadmap`, isolated checkout `.worktrees/jira-roadmap`.

Michael approved implementation, tests, documentation, push, merge and deployment
of the defined backlog. For provisional AJ-42 through AJ-52, he selected concrete
requirements and test integrations first. Do not represent those as live services.
The complete Jira project query returned 52 issues with `isLast=true`.

## Current local work

- AGENTS.md now links the backlog and records the current authorization and backup
  guideline. The original checkout's other uncommitted files remain untouched.
- AJ-37: owner-only dismissed-application restoration preserves original files and
  text, blocks missing files and unresolved/accepted delivery, and supersedes old
  sending authorization. Added an explicit client action and regressions.
- AJ-37 source is ready for its local commit; no push, merge or deployment of this batch has occurred.

## Actual verification

Using the existing Python 3.12 virtualenv, with `DEBUG=True`,
`PYTHON_DOTENV_DISABLED=1`, `REAL_EMAIL_ENABLED=False`:

```text
python manage.py check                         passed
python manage.py makemigrations --check --dry-run   no changes
python manage.py test jobs.test_lifecycle --noinput  14 passed
python manage.py test --noinput                281 run, OK, 1 Windows skip
```

Resume verification: both additional authorization/ambiguous-delivery restoration
regressions passed. Full suite rerun: **283 tests, OK, one Windows skip**, 192.020s.
The first focused attempt exposed a synthetic fixture without original application
files; the fixture now supplies them, preserving the production missing-file guard.

Explicit Node 24.19, locked npm installation: 180 packages installed, zero audit
findings; `npm run lint`, `npm run test -- --run` (99 tests), and `npm run build`
passed. The generated build has NOT yet been copied into committed frontend_build.
Commit source/review evidence first, then the generated frontend build last.

## AJ-12 platform response supplied by Michael

PythonAnywhere confirms standard Django/WSGI receives native
`wsgi.url_scheme='https'` for HTTPS. Client-supplied X-Forwarded-Proto headers,
including duplicates and comma-separated values, are stripped. Keep
`SECURE_PROXY_SSL_HEADER=None`; do not enable proxy-header trust.

Before activation, verify a real HTTPS request reports secure through the actual
WSGI application. Then activate:

```text
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=300
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
```

Keep host Force HTTPS enabled. Verify no loop, HTTPS HSTS header, ordinary
authentication/profile/download use and spoofed-header behavior. Roll back only
the changed redirect/HSTS settings and reload if verification fails; never restore
the database for a configuration rollback. This response resolves platform
assurance, but live verification and activation remain pending.

## Remaining execution

Continue defined AJ-17 and AJ-24 through AJ-41; reconcile existing functionality
against each actual criterion. AJ-8–AJ-11, AJ-13–AJ-16 and AJ-18–AJ-23 are currently
Done in Jira; AJ-12 and AJ-17 are In Progress. Existing account emails do not
complete application/alert sending. Renewed expiry is recorded as 19 November 2026.

Implement and verify automated private backups with off-server recovery; document
machine availability and platform constraints honestly. Retention remains report
only. Simplify developer/user onboarding after feature changes settle. Housekeeping
must inspect references and preserve private data, backups, stash, Docker lesson
files, coverage and original checkout changes. No cleanup has yet been performed.

## Resumed execution results

AJ-37 committed locally as 7382c79 (source) and bb3c4b2 (build). All 283 backend
tests passed (one Windows skip); 99 frontend tests passed. Not yet merged/deployed.

AJ-24: explicit draft-policy agreement, additive profiles.0006_privacy_notice,
owner-visible read-only evidence, public draft notice and UI. Focused 16 backend
tests passed; full suite 286 passed with one Windows skip (426.804s) after isolating
a historical migration regression to its fixed target instead of future leaf nodes.
No production privacy migration has been applied yet. New frontend gate: 100 tests,
lint and repeated build passed using explicit Node 24.19. The final locked install
passed in .verification/frontend; original worktree reinstall hit a Windows-locked
native Tailwind binary, which was preserved. Lint used the original source path
explicitly because the verification folder is Git-ignored. The CV focus regression
now awaits the animation-frame effect rather than asserting synchronously.
Tailwind scanning is explicitly limited to src so nested checkout/build folders
cannot add unrelated CSS; repeated verification builds matched their asset names.

A newly published npm advisory affected transitive follow-redirects 1.16.0
(GHSA-q3jh-wrc6-jgq8 / GHSA-8r9p-f939-6h3c). Patched only its version, resolved URL
and integrity to 1.16.1, preserving other lockfile entries/platform metadata.
After patch, npm audit reported zero findings; this is advisory matching, not proof
that browser Ajiri credentials were exploitable through a Node-only redirect path.

AJ-12 completed in production on unchanged source 6474498: native secure recognition
verified, original WSGI restored, Django redirect True and HSTS 300 activated without
proxy trust/subdomains/preload. Live header/loop/spoof checks passed; owner reads
and private download passed. Only deliberate check --deploy W005/W021 remain.
Jira Done status was reread and confirmed. See HTTPS_ACTIVATION_20261020.md.

Backup automation verify-and-copy-ajiri-daily-backup created ACTIVE for 10:00 Nairobi
daily, using the documented private snapshot/off-server/restore procedure and
failure reporting. Its first scheduled run remains UNVERIFIED. No always-on
PythonAnywhere scheduler or disk-encryption guarantee is claimed.

README/SETUP simplified; USER_GUIDE and operator backup guidelines added. Verified
unused social sprite removed; no private/user data or original Docker lesson
removed. See HOUSEKEEPING_REVIEW.md. AJ-31/38/41 decisions recorded in
ROADMAP_SPIKE_DECISIONS.md; local staging setup/verification is in progress.

## Release #27 completed (overnight 20–21 October Nairobi)

PR #27 head 1afa17d61ff0baf06ba6a456f84e137ef964ab99 passed all four checks, then
merged as cc731976de13a5b5d561739def8dd93a26f70bff. All four merge checks passed too.
That exact release is now deployed. Fresh paused-writer snapshot:
backup-20261020T205514252995Z-8ba8d533; server and independent private local restore
verified (12 media files, 212184 bytes). Only profiles.0006_privacy_notice applied;
every pre-existing row value and unset historical consent was preserved. No runtime
requirements changed and no pip install was required. Web app and both previously
active workflows resumed and reread active. Live asset bytes match the release;
health/login/register/privacy/applications 200 with HSTS300. Live invalid registration
400, anonymous restore401 and missing-CSRF refresh403; owner profile read200.
Normal ingestion succeeded: https://github.com/michael-mathenge/ajiri/actions/runs/39497734521
Private rollout/rollback receipt is alongside the off-server backup. No real
production account/document/authorization was created for QA. Browser registration
agreement verified unchecked after an old tab reload. The obsolete lazy-chunk blank
page observed before that reload has a regression/recovery boundary in the next batch.

Jira AJ-12/24/37/31/38/41 are Done and statuses were reread. AJ-31/38/41 are decision
spikes, not claims of live public SEO or Swahili. Remaining defined features stay open.

## Operations batch deployed — 21 October 2026

PR #28 passed all four required checks and merged as
`93da1161f4a955ab0d3a3f9d5468e24a2bf5d31a`. Production is verified at that
revision. Fresh paused-writer backup `backup-20261020T213134403490Z-4c4cdc48`
passed server and independent private off-server restoration:12 files/212184 bytes.
No requirements delta, pip install or migrations. System check, migration drift
and empty migration plan passed before activation. Live health/login/register/privacy
returned200/HSTS300; served index/assets match pinned bytes; authenticated profile,
jobs and applications reads200. App and both previously active workflows resumed.
Rollback: stage cc731976 and reload, retaining current database/media/configuration.
No database restoration is required for this code-only rollback.

Read-only release planner passed on the clean c2d5b48 checkout: no pending source
migrations or production requirements change. The final generated build was committed
last. The following records describe the package's actual verification.

Branch codex/jira-operations starts at deployed cc731976. Isolated staging image
builds, fresh-volume migrations and localhost:8001 health passed. UID10001,
/data/db.sqlite3, no baked .env, real mail off and empty ingestion credential verified;
original localhost:8000 learning container preserved. Full Linux suite reached
296 tests OK, with no Windows symlink skip. Final allowlisted image also passed all 296 tests (79.426s), no skips.
See OPERATIONS_ROADMAP_REVIEW.md. Native focused backup/preflight tests:20 passed. Repaired
concurrency scenario was run five separate times successfully; an initial repeated
label command was deduplicated by Django and is not counted as five runs.

The SQLite last-slot test now accepts only documented no-handoff busy exhaustion,
then reconciles the same losing key after workers finish and still proves exactly
one provider call/attempt/quota claim. Added deterministic exhausted-lock regression.
No automatic provider retries or delivery-service policy changes.

Reusable verify_private_backup validates completion, hashes, SQLite and bounded safe
archive inventory, and optionally restores into a new private folder only. Its
actual independent local restore of the private release snapshot passed:12 files.
Container path guards now recognize a packaged /app without treating its parent /
as all application data; missing Git provenance explicitly records unverified.
Fresh .env example fixes blank mail backend and local trusted-origin setup.
Read-only release_preflight validates clean exact SHA, reviewed migration delta and
build references; actual clean-checkout execution occurs after its package commit.
No fetch/install/migration/activation is performed by that planner.

Frontend locked install/lint/102 tests/build passed in the isolated Node24.19 runner.
New render boundary offers explicit reload for obsolete lazy chunks, without echoing
exception text, clearing authentication or retrying mutations. The final build is committed
as the last package commit (c2d5b48). Historical Checkpoint2 checklist is archived, not deleted.
Provisional AJ-42–AJ-52 requirements prepared; test integrations and live services are
not claimed complete. Daily backup scheduling is active; first scheduled run pending.

## Account export package — local, 21 October 2026

Branch codex/jira-account-privacy from93da116 adds the operator-only
export_account_data command, not a public endpoint or account erasure. Six focused
tests pass; full native Django suite302 OK with one Windows symlink skip (173.220s).
System check and migration drift passed. Explicit Node24.19 locked installation,
lint,102 component tests and verification build passed; no frontend source changed.
No production user export, deletion or real email was performed. See
ACCOUNT_DATA_OPERATIONS.md. AJ-25 remains unfinished until erasure, partial-file
failure/retry and restore-ledger replay are implemented/tested.

PR28 post-merge CI and normal ingestion both succeeded. Ingestion evidence:
https://github.com/michael-mathenge/ajiri/actions/runs/39501474386
AJ-35 and AJ-36 were marked Done and reread after deployed evidence.


## Alert consent package — local, 21 October 2026

Continues codex/jira-account-privacy. Adds explicit choice evidence and confirmation
UI, a purpose-bound30-day confirmed unsubscribe, authoritative ledger reservation
checks and new-profile email-OFF default. Existing values are not backfilled.
Legacy profile email payloads fail with an actionable field400 instead of silently
claiming consent. In-app remains independent. Console matching no longer marks
emails sent; live alert transport stays disconnected pending its owner pilot.
See ALERT_CONSENT_OPERATIONS.md for server order and rollback constraints.

Focused backend45 tests passed before final migration/late-revocation additions.
Initial frontend regressions exposed obsolete profile fixtures; corrected mocks and
separate-choice assertions then passed11 focused tests. Final locked Node24.19
install/lint/all105 component tests/build passed. Final Linux suite310 tests passed
in80.766s, no skips. System check and migration drift passed again. The earlier
native308-test run failed the obsolete profile-preference journey payload; the
updated fixture and all new tests are included in the successful Linux310 run.
No production consent was inferred or recorded and no real alert email sent.


## PR29 deployed — 21 October2026

Merged/deployed4fa75b5541b6998767b90d97e5e6dfe659840280 after all four PR and
post-merge CI checks passed. Fresh backup085718Z-d9b17894 passed server/off-server
isolated restore:12 files/212184 bytes. Only profiles.0007 applied; no pip install.
SQLite reordered profile columns; positional comparison was replaced with explicit
column-name comparison. Every historical row value was preserved; only one model
content type/four permissions plus migration history were added. No inferred consent.
Live health/login/unsubscribe200/HSTS300 and exact index/assets passed; owner
profile/jobs/applications reads200 and legacy consent status false. App and both
prior-active workflows resumed and reread active. Normal ingestion succeeded:
https://github.com/michael-mathenge/ajiri/actions/runs/39573917686
No production consent, export, erasure or email was created for QA.

## Verified erasure package — in progress locally

Branch codex/jira-account-erasure from4fa75b5. Dry-run-first verified requests,
signed private prepared/completed journal, dependency-ordered row cleanup,
explicit session/JWT removal, resumable private-file cleanup and old-snapshot
replay. Shared jobs/skills/global quotas remain. Actual owner erasure/legal checks
remain per-request prerequisites, not broad feature authorization.

Focused28 backend tests passed after correcting synthetic destination/sender
fixtures and explicitly handling SimpleJWT's retained OutstandingToken rows.
Backup automatically includes a bounded erasure-ledger.zip when its configured
private directory exists; verifier checks hashes/members and isolated extraction.
No keys/environment files are copied. Daily automation prompt updated conditionally;
no actual user erasure or production ledger was created. Full Linux321 tests passed
(107.867s), no skips; system check/migration drift passed. Explicit Node24.19
locked install/lint/105 component tests/build passed; generated bytes exactly match
the committed build. No new dependency or migration. AJ-25/26 are In Progress;
AJ-26 still requires gated real transport/pilot and unsubscribe footer integration.


## PR30 deployed — 21 October2026

Required PR/postmerge CI checks passed; deployed9efd1f0fb99b7d8b66180c1e4b6ed6ac8705501b.
Fresh snapshot092614Z-bb36a5ed passed server/offserver isolated restore12 files212184
bytes. No migrations/dependency install. Live health/login/unsubscribe200/HSTS300,
index exact; owner profile/jobs/applications/alert-preferences reads200. Backup and
erasure inventory dry runs passed with no journal/account mutation. Writers restored
to prior active states and verified. Normal ingestion succeeded:
https://github.com/michael-mathenge/ajiri/actions/runs/39577369558
AJ-25 completed from implementation/test/deployment evidence; actual user erasure
still requires a specific verified request and legal/recovery prerequisites.

## Owner alert pilot — local, not activated

Branch codex/jira-alert-delivery from9efd1f0. Default-off synthetic owner-only
Brevo bridge with shared budgets, stable per-notification receipt, signed unsubscribe
footer and final consent/configuration recheck. Hidden inactive synthetic fixtures;
normal ingestion cannot send. Profile UI distinguishes saved consent from disabled
mail delivery. No production fixture, consent or email created. See OWNER_ALERT_PILOT.md.
Focused13 tests passed before the final late-revocation regression. Final Node24.19
locked install/lint/106 component tests/build passed. Full Linux328 tests passed
(115.572s), no skips; system check and migration drift passed. No new dependencies
or migrations. Owner consent and actual inbox/unsubscribe evidence remain pending.

## PR31 deployed and owner alert pilot — 21 October 2026

Deployed40c1ea0507b8c39fff604dc2601eb8fd48ea9b0e after four required PR checks
passed. Snapshot094933Z-aee31c01 passed server/off-server isolated restore,
12 media files/212184 bytes. No migration or dependency install. The owner personally
saved current verified-address consent. One hidden synthetic notification was
handed to Brevo once; provider acceptance and subsequent owner inbox confirmation
were recorded separately. Owner confirmed successful unsubscribe; production
read-only checks verified the unsubscribe event, preference/eligibility false and
ALERT_EMAIL_ENABLED=False. No real job/employer message was sent. Link-preview
no-effect behavior has automated coverage but no independent live observation.
AJ-17/AJ-26 remain In Progress: normal alert/application sending is disconnected.

## AJ-27 browser acceptance package — in progress

Branch codex/jira-browser-journey from40c1ea0. Optional pinned Playwright runner
drives the committed React client and disposable Django live server at a mobile
viewport. Covers registration/login, profile, explicit CV approval/selection,
private downloads, application preparation/review and no provider/ledger effects.
Managed sending remains untested/unavailable; AJ-27 is not complete.

21 October commands: native `manage.py check` and `makemigrations --check --dry-run`
passed; `manage.py test --noinput`:328 tests OK in221.061s, one Windows symlink skip.
Node24.19 `npm ci --offline`, lint,106 component tests and build passed; hash comparison
found zero committed-build mismatches. No frontend bytes changed. Browser dependency
installation stalled downloading the official38.7MB Windows wheel; explicit browser
run is UNVERIFIED locally until installation succeeds. The ordinary suite deliberately
does not discover the optional module. Michael separately approved the additive
isolated browser CI job; existing four required checks remain unchanged. CI result
must be recorded before merge. No runtime dependency, migration or sending change.

First Linux browser run reached the job selection step and exposed an incorrect
test assumption: the approved current CV is intentionally displayed by default.
The test now clears that selection, verifies preparation is disabled, then selects
the displayed approved version and submits explicitly. Product behavior is unchanged.
The corrected browser job passed on Linux at b02d2b7 in run39599872379. AJ-27 stays
In Progress because successful managed sending is not implemented/covered. Local
Windows browser execution remains UNVERIFIED; CI evidence is recorded separately.

## PR32 merged — browser acceptance

Merged0fa07d58b59069881903c9e160cdb6accf122fe8 after all five checks passed on
final head a6ae1ac. Post-merge run39600606759 also passed all five checks. This
test/documentation-only package needs no production reload; production source
remains40c1ea0 pending a functional release. AJ-27 stays In Progress for managed
sending coverage. The first failed browser notification was superseded by the
corrected green runs, not ignored or bypassed.

## AJ-28/AJ-30 quality baseline — in progress locally

Branch codex/jira-quality-baseline from0fa07d5. Adds optional pinned development
requirements, Ruff correctness scope, ESLint, changed-file Prettier hooks (opt-in,
no Git hook/config installation), branch coverage and an explicitly nonblocking
legacy mypy report. Unexpected checker failure still fails; three wrapper regression
tests passed. One Node hook-safety test passed (bad syntax/formatting/outside path,
no automatic file rewriting). Node24.19 locked install/Oxlint/ESLint/106 component
tests/build passed; build bytes and runtime lock versions are unchanged. Ruff
passed across backend and tooling. CI quality job separately approved by Michael.

First full native coverage run:328 tests, one failure and one Windows skip in268.778s.
The failing concurrency test used mutable helper preflight during concurrent dispatch
and wrongly required immediate success despite the service's documented bounded
SQLite no-send busy response. Workers now use the same frozen service request;
only the exact busy response is permitted, only with one durable receipt/provider
call/quota reservation. Reconciliation after workers finish must read that same
receipt without another handoff. Both concurrency regressions passed in five
independent coverage runs. Full coverage rerun/report pending. DeliveryService,
auth, sending eligibility, runtime dependencies and production were not changed.
The full rerun passed328 tests in252.999s with one Windows symlink skip; report/XML
were generated in the ignored verification directory. Initial combined coverage
was88.85%; final reporting excludes the synthetic cv_test_helpers fixture and is88.82%.
No production code was excluded to raise the result. Native mypy/pre-commit remain
UNVERIFIED while their large tool downloads finish; the approved CI job must verify
them and retain reports before merge. New author/committer identity will be checked.

Subsequent verification: native pre-commit config validation passed; mypy ran and
reported199 legacy findings (nonblocking, not clean). All six PR33 jobs passed at
ab48abc in run39614901653, including the new quality job. Linux coverage88.96%,
197 legacy type findings. API verified the finalized quality-reports artifact
ID12351314400,14469 bytes, expiry28 October2026. Ruff/ESLint/changed-file hooks and
all safety regressions passed in CI. No hook installation/Git configuration mutation.
The temporary Linux download helper was stopped; Docker lesson/user data preserved.

## PR33 post-merge verification

Merged20939e35f9d9a47494868056b728027318bd7fed. All six post-merge checks
passed; AJ-28 and AJ-30 updated to Done from this evidence. Development tooling
only; recorded production remains40c1ea0, with no unnecessary reload.

## AJ-29 accessibility and performance — in progress

Branch codex/jira-accessibility-budgets from20939e3. Michael explicitly approved
extending the existing browser CI job, locked Node test tools and sanitized
seven-day reports. Adds axe rules on the synthetic application journey and public
light/dark pages; no production account, mail or private document audit. Lighthouse
uses three mobile runs per public page and checks each median against measured
initial budgets. Raw Lighthouse reports stay local; only numeric summaries upload.

Actual local commands: system check and makemigrations --check --dry-run passed.
Node24.19 npm ci passed (360 packages, audit zero vulnerabilities); Oxlint, ESLint,
one hook-safety test,106 component tests and build passed. Rebuilt bytes match
committed frontend_build; no generated change exists to commit. Ruff passed.
Three malformed-report/budget regressions passed. Measurement-only Lighthouse
reported a skip; the subsequent enforcing test passed in91.159 seconds. Login and
register median performance81/81, LCP3673/3714ms; this is a regression baseline,
not a good-vitals claim. Local axe remains UNVERIFIED without its optional Python
browser SDK; approved Linux CI must execute it before merge.

The first full backend attempt hit Windows sandbox temp-directory permission
errors (confirmed with a focused export test); it was stopped. The full synthetic
suite is rerunning with normal filesystem access. No runtime dependencies,
production configuration, database migrations or sending activation are changed.
Full backend rerun passed331 tests in259.710s, one known Windows symlink skip.
Pre-commit configuration and changed package JSON formatting also passed.

## First browser CI findings and local repairs

Run39619837635 correctly failed on brand/job-link accessible names that omitted
visible words and inline links distinguishable only by colour. Accessible names
now include those visible words, the brand text has an actual word separator,
and ordinary inline links are underlined. Axe rules are unchanged. The complete
local browser suite subsequently passed (two tests,20.841s), including14 axe scans
and the full synthetic register/CV/application review journey. This supersedes the
earlier unavailable local-browser result. No sending occurred.

The same Linux run failed to execute Lighthouse before reporting a measurement;
it is NOT a budget pass. Sanitized execution diagnostics now strip URLs and paths
before logs; a regression verifies that stripping. Raw reports remain local.
The backend rerun passed332 tests in262.432s, one known Windows skip. Linux
Lighthouse execution remains unresolved until the next CI result.
Final frontend rerun passed108 component tests, Oxlint, ESLint and the hook-safety
test. System check/migration drift and Ruff passed after the fixes. The frontend
build now changes for the demonstrated accessibility repairs and will be committed
last, replacing only verified generated assets. No runtime library versions changed.

## AJ-29 merged and CI acceptance complete

PR34 merged8d84a2e85caea3d032f88bd860be9e43f6e2906a after all six checks
passed on f623f05. Post-merge all six also passed. Linux browser suite:three tests
OK in80.821s; sanitized artifact12354702670,1004 bytes, SHA256
34beca13d94528fe029b118c5edd158cbbbedb64e5281559b1e94d27dd8b75e8,
expiry28 October2026. Initial Lighthouse launch failure did not recur on final or
post-merge runs; its cause is unknown. No budget was relaxed. Local enforcing
Lighthouse after the UI repairs also passed in101.407s. AJ-29 is Done for its CI
acceptance; accompanying label/link fixes await production release. Production
remains40c1ea0. Rebuilt final client bytes were independently reproduced exactly.

## AJ-32 query data layer — local verification in progress

Branch codex/jira-query-data-layer from8d84a2e. TanStack Query5.104.5 replaces the
custom read hook on six existing page types. API paths key shared/cancelable reads;
cache is memory-only,30s fresh/five-minute inactive expiry. Writes invalidate reads;
no automatic mutation retry. Same/cross-tab account changes discard cached private
data. Axios auth interceptors/cookies and sending authorization semantics unchanged.
On-demand document review/reconciliation remains explicitly fresh.

Locked Node24.19 npm ci passed362 packages/audit zero. Oxlint/ESLint,113 component
tests (including five cache isolation/retry regressions), hook safety and build
passed. Added a further user-facing skill-save/match refresh regression; final
component rerun pending. An initial component run caught invalidation hooks in the
wrong review/send wrapper scope; corrected in the actual session components and
all existing review/send regressions then passed. Backend system check/migration
drift passed; full suite and real-browser/axe/Lighthouse gates are running.
Full backend suite passed332 tests in272.260s with one known Windows skip.
Final component suite passed114 tests, including actual skill-save/match refresh.
The browser journey's two tests/14 axe scans passed, but its combined run failed
on Lighthouse NO_NAVSTART trace recording (not a budget result). Added one explicitly
recorded fresh-browser retry for that upstream recording error only, bounded once
per suite. Regression assertions reject further retries, successful results and
other error codes; no performance limits or app-mutation retry rules changed.
The focused guards and enforcing performance rerun are in progress.
Focused report/trace guards plus enforcing mobile performance passed five tests
in104.908s. Exactly one NO_NAVSTART trace retry occurred and was recorded; all
three valid measurements per page still met unchanged budgets. No other errors
or metric failures are retried. The complete browser journey/axe portion had
already passed in the combined attempt; its performance failure was explicit.

## PR35 deployed — 21 October 2026

Merged46c7ea7c41ddad6831d5399af289385bc7d38da8 after all six checks passed
on2d36957; all six post-merge checks also passed. GitHub's required Python3.12
status briefly lagged successful job completion; one rerun was requested and the
actual required status became green before merge. Official GitHub status reported
a concurrent pull-request/webhook delay incident; no gate was bypassed.

Private snapshot backup-20261021T152829703338Z-5ad371d9 from40c1ea0 completed with
writers paused; both workflow states and the enabled web app were promptly restored
before download. Server and independent local verification checked hashes, SQLite
integrity, safe archive inventory and isolated restoration:13 media files/224960bytes.
The off-server copy and sanitized receipt are retained under the owner's private
AjiriBackups directory. Bundle SHA256:
6766aa886e20dbce7c2ab8a2597fa6b35a5069f897bcbc60c9f69d56be369895.
No retained data was pruned; erasure ledger was not present in this snapshot.

A second short writer pause staged exactly46c7ea7 after source-clean/ancestor guards.
The first staging attempt safely stopped outside the Git repository; explicit cd
and workon corrected the console context before any checkout. release_preflight:
no expected migrations, pip_install_required=false. Production system check passed,
no migration drift, no planned operations. Native HTTPS/proxy-header-None/HSTS300/
subdomains-off/preload-off and alert flag OFF were asserted. Reloaded web app;
live health returned200, and login HTML plus referenced assets matched release
bytes exactly. Original enabled web app and active ingest/sweep workflows restored.

Public browser smoke shows the new Ajiri Kenya accessible home label and login
screen. After the owner signed in, jobs, profile, CV builder and applications
loaded successfully. Uploaded and approved CV downloads were nonempty valid DOCX
archives. No profile edits, approvals or sending actions were performed. Ingest
and sweep workflows were independently confirmed active. AJ-32 moved to Done.
No password was requested in chat. Rollback: pause writers, return source to40c1ea0, check/reload and
restore prior writer states; retain live data and existing private configuration.
No migration reversal or routine old-database restoration is needed.

## AJ-33 forms � local verification in progress

Branch codex/jira-forms-validation from deployed/fetched46c7ea7. All nine form
elements now use React Hook Form7.90.0 and Zod4.6.7 Mini through a shared resolver.
Incomplete CV drafts, explicit approvals, alert choice replay and all server
messages are retained. Native-validation replacement exposed a partial-date gap;
schema date validation and its regression corrected it. Async validation exposed
a cooldown timing race; an immediate recovery guard plus shared duplicate-submit
lock prevents delayed/duplicate requests. Login pending-state test now awaits
validation before asserting its disabled state. Initial full component run failed
three tests, then a second caught the date issue; focused CV/schema19 tests pass.
Final full gates running. Backend check and migration drift pass; no migrations.
Dialog primitives moved into private screen chunks to retain unchanged mobile
performance budgets. No production activation or live email for this package yet.

AJ-33 final gates: system check passed; no migration drift; full Django332 tests
OK/one known Windows skip,275.562s. Explicit Node24.19 locked npmci364 audited
packages/zero vulnerabilities. Oxlint against real source, ESLint, hook safety,
Prettier changed-file checks and123 component tests pass. Ruff and hook config
validation pass. Public bundle first failed transfer budget at516410/513498bytes;
dialog splitting alone was insufficient. On-demand toast primitives corrected the
actual cause without changing limits; notification display/dismissal regression
passes. Final three Chromium/axe/performance tests pass; login/register medians:
79/77performance,4005.551/4029.118ms LCP,137/185.5ms TBT,CLS0,483000/480088bytes,
zero trace retries. Subsequent build matches exact committed-target bytes.
No schema migrations, server dependencies, auth-interceptor, ingestion or CI edits.

## AJ-34 API contract � local implementation

Separate branch codex/jira-api-schema from46c7ea7 while PR36 runs CI. Additive
/api/v1 aliases reuse exact existing callbacks; ingestion/sweep stay legacy-only.
Reviewed static JSON is published at /api/schema; drf-spectacular0.30.0 and pinned
support libraries are offline-only extras, not production dependencies. Strict
generation first exposed six annotation warnings; offline model/field/operation
annotations resolved all without runtime view edits. Generation uses an isolated
in-memory database and fails on warnings/drift. Four focused compatibility tests
pass, including real-CSRF cross-version login/refresh and anonymous denial.
An initial full-suite command from the repository root discovered zero tests;
that is not a passing full suite. Correct backend-directory run is in progress.
CI edit was separately approved by Michael and adds strict generation/drift checking
to the existing quality job; all six check names remain unchanged.

AJ-34 base fast-forwarded to the CI-verified PR36 merge925cff9; no history rewrite.
Saved API documentation additions were retained while Git restored native line
endings for the fast-forward. No stash or original-checkout changes. Full Django
suite336 tests passed/one known Windows skip in296.448s. System/migration-drift
checks pass. Strict schema generation and independent byte-drift check pass against
an empty in-memory database. Four new compatibility tests passed; aliases reuse
every legacy callback and protect private data. Node24.19 lockednpmci364 audited
packages/zero vulnerabilities, lint,123 component tests and build pass. Canonical
source hashes match the isolated runner; generated build matches committed bytes.
No frontend changes in this package. Ruff and hook configuration validation pass.
No migrations or production dependency changes. Source-only contract contains no
user records; custom response-object typing limits are explicitly documented.
