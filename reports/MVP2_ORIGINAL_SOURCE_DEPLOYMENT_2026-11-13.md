# MVP2 original-source release: 13 November 2026

Production was activated at reviewed main `93cf55e5299e8eb5adab60da215b5fbe1e82d1b4`
after [release PR94](https://github.com/michael-mathenge/ajiri/pull/94).
Previous runtime was `d5f2f6871276434569df10ffb153cb8591a9a7df`.
All six exact release-head checks and all six fresh merged-main checks passed:
frontend, quality, browser and backend Python 3.12/3.13/3.14.

## Delivered scope and branches

- AJ87: `codex/mvp2-aj87-security`, source `f1f7d25`,
  [PR91](https://github.com/michael-mathenge/ajiri/pull/91), MVP2 merge `00ce84f`.
  Scoped compatible minimatch 11.0.5 overrides, real ESLint-glob regressions and
  fresh complete npm audit with zero vulnerabilities. GitHub alert 32 reports fixed.
- AJ85: `codex/mvp2-aj85-recovery`, source `067cf8c`,
  [PR92](https://github.com/michael-mathenge/ajiri/pull/92), MVP2 merge `fbd8834`.
  Read-only measured peak-space planning for a private snapshot and transfer copy.
- AJ82: `codex/mvp2-aj82-original-source`, source `7ce4c1e`, generated build last
  `19cf7bd`, [PR93](https://github.com/michael-mathenge/ajiri/pull/93),
  MVP2 merge `e3682bf`. Original employer publishing uses independent review,
  stable Ajiri identity/provenance and owner-scoped submission retry keys.
  Michael's original-source direction replaces the proposed three-feed requirement.

Every feature PR passed six checks before merging into MVP2. Nothing was committed
directly to main. This release does not complete the entire MVP2 backlog.

Final application-package local results:555 Django tests passed 261.722s, one
existing platform skip; 161 components/28 files passed 24.31s; five tooling tests
passed 3.990s. Check, migration drift, Ruff, strict offline schema, Node 24.19 npm ci,
Oxlint, ESLint and Vite build 1.62s passed. New migration tests preserved legacy
draft/review/job relationships and all three search triggers through forward/reverse
operations on disposable data. CI's employer journey exercised server-accepted,
lost-response retry without creating a duplicate. See the three individual reports
for focused tests, earlier failures and exact package commands.

## Approved capacity recovery

Michael explicitly approved deletion of only `mvp2-20261111-recovery.zip` and
`runtime-rollback.tar.gz` inside `backup-20261111T202211225524Z-44e595ea`.
Their 64,442,246 bytes were independently checksum-verified both off-server and
on-server immediately before removal. The old server manifest/database/media
snapshot and all off-server copies remain. No other backup was pruned; no future
deletion policy was authorized. Post-cleanup home usage was 386,004 KiB.

## Fresh private recovery gate

Both GitHub writer workflows were disabled and all five active/queued/waiting
status queries were empty. PythonAnywhere web requests were disabled before:

```bash
manage.py backup_private_data --destination /home/Mathenge/ajiri-private-backups --include-media --writers-paused
manage.py verify_private_backup --backup "$BACKUP_DIR"
```

Completed snapshot: `backup-20261113T134617405732Z-46a6f54d`, source `d5f2f68`.
The existing web runtime and writer workflows were restored during download.
The completed immutable snapshot alone was packaged into a 0600 private ZIP;
no environment file, credentials or runtime directory was added.

Download size: 10,993,453 bytes; SHA256:
`4b77a0a06dcc35bf080472dbd7c1393d297a8369afa7512502d2b6d984fcb334`.
Manifest SHA256:
`cb433e1c81b0fc18f3ad6d83ddbe5353735ee158673383f9ad767bbc264909cf`.
The independent off-server verifier checked exact members, size bounds, hashes,
manifest completion/source, retained a private second copy and ran
`verify_private_backup --restore-to` in an isolated directory. Database integrity
and all 16 private media files / 335,905 bytes passed. No erasure ledger existed;
none was invented. Private recovery receipt remains off-server with the snapshot.
This was a manual paused-writer fallback, not evidence that a scheduler ran.

## Migration, preservation and activation

Writers and web requests were paused again. All 43 existing database tables and
all 16 media files still matched the snapshot verified off-server. No stale data
was restored to production. Exact clean source 93cf55e was staged while paused.
`release_preflight.py` confirmed unchanged runtime requirements and only expected
`jobs.0018_original_employer_submission`. Django check and migration drift passed;
the actual migrate plan contained only that operation. Migration0018 applied OK.

All existing table values, all three SQLite search-trigger definitions and all
private media bytes then matched the preactivation proof. The first strict
comparison flagged SQLite bookkeeping: migration counter 55 became 56, and SQLite's
empty-table rebuild added `jobs_employerjobdraft` sequence 0. These two exact
differences were inspected and accounted for before the complete comparison passed.
Existing submission IDs remain null; no employer draft, review or vacancy was made.

All 33 production pins matched the repository in the existing Python 3.12 virtualenv;
no install or hosting configuration change occurred. Fresh measured home usage plus
a conservative 1 MiB margin was 435,482,624 bytes against 536,870,912 quota. The next
snapshot-plus-transfer plan needs 73,744,437 additional bytes including 16,777,216
reserve, leaving 27,643,851 bytes beyond that plan. This is bounded next-backup
headroom, not unlimited retention or an actual subsequent backup.

Authenticated read-only server-view checks using the existing owner passed:
jobs 200/count 0, CV draft 200, employer drafts 200, existing private approved CV 200
with matching stored document SHA256 and private/no-store caching. Anonymous
download 401. These are actual production view checks, not a fresh network login,
second-owner check or manual phone journey. No production test account or listing
was created and no email was sent.

PythonAnywhere web was re-enabled and explicitly reloaded; its control returned
ready. Public HTTPS health 200/HSTS `max-age=604800` and all 38 exact frontend-file
hashes passed. Live index SHA256:
`6df14d428ab319f2882bdd890931abf03bb31932011237c54613f53f257a92f3`.
Ingest and sweep workflows were restored to active; no additional manual ingestion
or sweep was dispatched. The earlier single manual-ingestion approval was not reused.

## Flags, remaining acceptance and rollback

Freshness remains true. Employer posting, public jobs, application email and alert
email remain false. Existing account-security email remains true. No service
permission, consent, staff access or broader sending was inferred from this release.

Live original-source diagnostics report 0 eligible roles, 0 genuine participating
employers, 0 publication records and no pending intake. Targets remain 50 roles / 10
employers. AJ82 and AJ53 therefore retain their real employer participation,
independent review and pilot acceptance gaps. AJ83's first explanation slice is
already deployed; normalized mobile filters/preferences/dismissals and its consented
pilot remain unfinished. Scanner, actual durable infrastructure, broader permitted
mail, privacy analytics and commercial/Daraja prerequisites remain separate gates.

Rollback code to d5f2f68 only while requests/writers are paused, retaining the
additive 0018 schema and any new records. Runtime dependencies did not change.
Do not routinely restore the older database or media, reverse migration history,
disable freshness, or broaden publication/sending. Preserve independently recorded
erasure journals on any exceptional recovery.

## Remaining Jira work after this release

Fresh complete Jira query found17 unfinished non-Epic entries. AJ80 historical
cleanup and AJ81/AJ85/AJ87 are Done. These17 remain open:

| Issues | Remaining scope or actual prerequisite |
|---|---|
| AJ53, AJ82 | Genuine original employer intake, independent review and live inventory/pilot targets. |
| AJ52 | Actual scanner host/signatures and private quarantine integration. |
| AJ83 | Normalized mobile filters, preferences/dismissals and consented matching pilot; explanation slice is already live. |
| AJ17, AJ26, AJ43 | Controlled broader application/alert/saved-search delivery and its actual permission, frequency and inbox gates. |
| AJ42 | Public publication activation with genuinely eligible inventory. |
| AJ84 | Saved-job shortlist and transparent manual application follow-up. |
| AJ86 | Consented participant acceptance, manual mobile accessibility and product disclosures. |
| AJ79 | Certificate uploads with actual scanner/quarantine and measured storage controls. |
| AJ47, AJ48 | Production PostgreSQL/object storage and durable hosted queue; local rehearsals are not live services. |
| AJ51 | Defined privacy-analytics purpose, legal/retention/consent and actual permitted activation. |
| AJ44, AJ45, AJ46 | Merchant/sandbox/commercial prerequisites and Daraja/entitlement work, last in roadmap order. |

Some remaining implementation can proceed independently; this report does not
describe all17 as external blockers or completed work. No pilot participation,
legal approval, credentials, storage purchase or publication permission is invented.

## Documentation package validation

Branch `codex/mvp2-release-evidence-20261113` was created from fetched reviewed
MVP2 e3682bf in its own worktree. Check and migration drift passed. The first full
backend run executed555 tests in267.252s with three errors/one skip: Windows's
restricted sandbox denied the existing disposable hard-link relocation operations
(WinError5). It was not a passing gate. The complete suite was rerun outside that
filesystem restriction:555 tests passed240.467s, one existing platform skip.
No implementation/test was changed or skipped to make that pass.

Node24.19 npm ci installed358 packages with zero audit vulnerabilities. Oxlint,
ESLint, build1.48s and all five tooling tests3.315s passed. All38 regenerated
frontend files exactly match the existing committed build; this documentation-only
package therefore changes no build artifact or runtime code. `git diff --check`
passed. Production remains93cf55e; merging newer documentation will not establish
a newer runtime activation.
