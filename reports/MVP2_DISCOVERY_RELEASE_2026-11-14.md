# MVP2 discovery and private follow-up release

## Verified activation — 14 November 2026 Nairobi

Production now runs exact checked main
`9676fc4c89b7aef04461c2ba0bbc9eed060ade45` (release PR99). PR100 subsequently
merged only the earlier checkpoint evidence into MVP2 as396913c after all six
checks; neither that merge nor this documentation follow-up changes the runtime.

Michael explicitly approved the three named old server snapshot deletions at
action time. Before removal, the script resolved the exact directory, rejected
symlinks and verified each exact size/SHA256 below. Only `db.sqlite3`,
`manifest.json` and `private-media.tar.gz` were unlinked, total27,006,264bytes.
The complete before/after directory inventory proved every other entry unchanged.
All private off-server copies and both newer server snapshots remain. No future
pruning policy was inferred. The fresh planner at21:32:07UTC passed with
89,333,760bytes available,73,744,437required and15,589,323beyond its reserve.

Ingest377395490 and Sweep377395493 were observed active, disabled and drained;
all five active/queued/requested/waiting/pending run queries returned empty.
Web requests were disabled before staging. The paused current database's43 tables,
all three triggers and16 private files exactly matched completed recovery
backup-20261113T211254131961Z-19b403ac; no current records/files were replaced.

Clean source93cf55e was fetched and detached at exact reviewed9676fc4. Actual
`scripts/release_preflight.py --revision 9676fc4c89b7aef04461c2ba0bbc9eed060ade45
--previous 93cf55e5299e8eb5adab60da215b5fbe1e82d1b4` with the three explicit
`--expected-migration` arguments passed; requirements-prod did not change.
`manage.py check`, `makemigrations --check --dry-run` and actual `migrate --plan`
passed. MigrationExecutor independently asserted that the entire pending forward
plan contained only jobs0019/0020/0021; `migrate` then applied all three successfully.

The first strict preservation comparison stopped on additive `auth_permission`
metadata. Read-only differences were inspected rather than hidden: exactly two
new content types (recommendationchoice/savedjob), eight model permission
definitions and the corresponding counters; no removed metadata. The final
comparison explicitly verified those exact additions and counter increments
(migrations+3, content types+2, permissions+8), then proved all prior43 tables'
old-column rows unchanged. This includes existing user/group permission
assignments; no staff access was granted. All three triggers and all16 file hashes
matched. New choice/shortlist tables were empty, all newly added fields null and
all observed safety flags unchanged.

Read-only authenticated production view checks used APIRequestFactory with the
existing active owner; these are in-process API checks, not a new browser login.
Jobs/CV draft/employer drafts returned200. Suggestions/dismissed choices/shortlist
returned200 with honest empty lists; application-list returned200 with one existing
record. Their responses were private/no-store and anonymous equivalents returned401.
The existing approved private CV download returned200 with bytes matching its
stored SHA256 and private/no-store; anonymous download401. After reload, an
additional read confirmed the existing application's `follow_up_at` is present
and null. No personal save/dismiss/date/update or real sending was performed.

Saved searches were actually **False** before staging and remain False: their
authenticated403 is the expected disabled-state evidence. Historical True reports
do not override the observed flag. Freshness remains True; posting/public jobs,
application email and alert email remain False. Existing owner-only account mail
flag REAL_EMAIL_ENABLED remains True. The additionally inspected
SUPPLEMENTAL_JOBS_ENABLED setting was absent (null), not proof of a separate
supplemental-browsing switch. All33 runtime dependency pins match requirements-prod.
A separate fresh process loaded the unchanged active PythonAnywhere WSGI file;
all seven configured safety/mail/saved-search flags agreed with these observations.

At21:38:36UTC the post-migration planner passed:448,638,976bytes used including
1MiB margin,88,231,936available and14,487,499remaining beyond the planned next
snapshot/ZIP and16MiB reserve. This is bounded headroom, not an unattended run or
unlimited retention. The actual readiness diagnostic still reports0original roles,
0employers and0pending submissions; the50-role/10-employer target is unmet.

Web re-enable and explicit reload completed. External verification returned
health200, `Strict-Transport-Security: max-age=604800`, and byte-for-byte hashes
matching all42 committed frontend files. Index SHA256:
`6abe168da627e6a9b9c5480c7ff7958234ff79b97cb2d0cb97d0c909aa7191e4`.
Both writer workflows were restored and independently observed active. No new
manual ingestion was dispatched under the already-used earlier one-time approval;
a successful current scheduled ingestion is not claimed by this receipt.

Rollback remains code-only to93cf55e with the additive schema, all new records and
private bytes retained. The completed private recovery below remains available;
do not routinely restore old production data. AJ84's bounded shortlist/manual-date
implementation is verified deployed; AJ83's consented participant pilot and genuine
inventory remain unfinished. No whole-MVP2 completion is claimed.

## Activation-evidence validation

The activation-evidence follow-up uses isolated
`codex/mvp2-discovery-activation-evidence` from reviewed MVP2/PR100 merge396913c.
Actual local mandatory gates passed: system check; no migration drift; full591
Django tests in289.769s (one existing platform skip), with Windows hardlink tests
executed outside the filesystem restriction. Explicit Node24.19 locked npmci
installed358packages/audit0; lint and build1.61s passed. Independent hashes matched
all42 regenerated files to committed frontend_build; no generated/source change.
Whitespace and branch/author/committer checks precede the focused evidence commit.
Its required PR checks must pass before merge; this is documentation, not another
runtime activation. The following checkpoint is retained as historical evidence.

## Earlier checkpoint — before the specific cleanup approval

Status at 14 November 2026 (Nairobi): release PR99 merged into main as
`9676fc4c89b7aef04461c2ba0bbc9eed060ade45`; production activation remains pending
the measured recovery-capacity gate. Production is still verified at
`93cf55e5299e8eb5adab60da215b5fbe1e82d1b4`. A merge is not deployment evidence.

## Checked feature packages

| Package | Source/build commits | MVP2 merge | Required CI |
| --- | --- | --- | --- |
| AJ83 normalized facts and filters, PR96 | `07968c2`, `f3079e3` | `9db23ab` | All six passed |
| AJ83 reversible owner choices, PR97 | `85a94bc`, `0f95c2d` | `e31ef17` | All six passed |
| AJ84 private shortlist/manual follow-up, PR98 | `c31fd73`, `3ec4af0` | `c983bed` | All six passed |

Release PR99's exact head `c983bedf51c6a81f0d073278d4495fa0f1b250b5` also passed
all six checks before merge. All six merged-main checks also passed before
activation; the remaining gate is recovery capacity, not CI.
Feature reports retain actual commands, failures, corrections and local results.
The latest package passed591 Django tests in286.935s (one existing platform skip),
171components, five tooling tests and two actual Chromium journeys in21.978s.
The browser journeys verify real saved-search navigation, save/remove/focus and
manual follow-up date/reload. They do not establish genuine participant acceptance.

## Fresh recovery and capacity

Both GitHub writer workflows were active before the snapshot pause; they were
disabled and drained, and the PythonAnywhere web app was disabled. At21:12UTC
the current source was verified clean at93cf55e. The quota plan measured
435,499,008bytes used with a1MiB margin and sufficient simultaneous snapshot/ZIP
headroom, including a16MiB reserve. No source staging preceded the snapshot.

Completed snapshot: `backup-20261113T211254131961Z-19b403ac`. The existing web app
and both writers were restored immediately after the snapshot; external
`GET /api/health/` returned200 with `{"status":"ok"}`. The immutable snapshot
was then packaged and downloaded privately through PythonAnywhere Files.

- Transfer ZIP:10,993,724bytes, SHA256
  `ebd04dbc0aa5d9401c12ca151b7ecc28f9445414a57e29d684fe1120b9b80dc6`.
- Manifest SHA256:
  `1afa5c8fb4e6c1fb20efae88ed31050ee6aba324db5b63419c9b60acf4961e81`.
- Private off-server recovery directory:
  `C:\Users\micha\AjiriBackups\release-discovery-backup-20261113T211254131961Z-19b403ac`.
- The downloaded size/checksums, complete manifest/source, exact ZIP members,
  SQLite integrity and all16 private files/335,905bytes passed. The isolated
  `verify_private_backup` restore completed with a retained aggregate receipt.
  This is a consistent manual release fallback, not an unattended scheduler run.

The following-backup plan at21:17:48UTC measured474,554,368bytes used with margin:
62,316,544available versus73,744,437required, a11,427,893byte deficit. The command
correctly failed closed with `Insufficient account-quota reserve`. Production
remains active and unchanged while this gate is resolved.

A one-time request identifies only the old server snapshot's `db.sqlite3`,
`manifest.json` and `private-media.tar.gz`, total27,006,264bytes, in
`backup-20261111T202211225524Z-44e595ea`. This request has not been treated as
approval. The earlier approval covered two different archives, already removed.
All other files and directories in that old snapshot must remain; in particular
the unreviewed file/directory and runtime metadata have not been approved.

The corresponding old off-server raw files were rehashed independently:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| db.sqlite3 |26750976|`913db2d416e7d20efb9fe69920f8147b8a9fc72d2d4f7cd341f6b0bfdd6724e8`|
| manifest.json |605|`5325d37af95f02f08f78a5c95c380cfcf8f6caa1c5f717e897b79ecc06f9f7b8`|
| private-media.tar.gz |254683|`d5314fb41056e677c9aa64f4d74e8038f794f459a7598951dd8c73b44b0e7ae8`|

Their retained recovery ZIP also rehashed to
`fc41e5bf94732cc30293076c1553898a7b2c07e62349ed5c633afcc030d47328`.
There is no recurring pruning authorization or claim of unlimited free-tier
retention. Capacity must be measured again after any approved cleanup and release.

## Deployment and rollback contract

Only jobs.0019_normalized_vacancy_filters,
jobs.0020_owner_recommendation_choices and jobs.0021_saved_jobs_and_follow_up
are expected. Requirements-prod is unchanged. Before staging, pause/drain writers
and web again and compare current database rows, triggers and private media with
the completed recovery. If they changed, obtain fresh consistent recovery rather
than restoring old production data. Stage the exact checked main revision;
run release preflight, system/drift and actual migration plan; apply only the three
reviewed additive migrations while requests remain paused, then activate.

Verify all prior table values through their old columns, all three search triggers,
private bytes and unchanged safety flags. Explicitly account for only the new
migration records/SQLite sequence bookkeeping. Existing unknown facts and manual
follow-up dates must remain null; the new owner-choice/shortlist tables start empty.
Read-only authenticated smoke checks must include suggestions, dismissed choices,
shortlist, saved searches, CV draft, employer drafts, application-list and an
existing approved private CV download; anonymous private access must fail.
Verify public health/HSTS and all42 committed frontend files externally.
Restore the existing writer states after activation.

Rollback code to93cf55e with additive schema and all new writes retained. Do not
restore an old database/media snapshot as routine rollback, disable freshness,
activate posting/publication/sending or overwrite current user data.

## Documentation-package gates

The isolated `codex/mvp2-discovery-release-evidence` branch starts at reviewed
MVP2 c983bed. Actual local checks for this evidence-only package:

- Shared pinned Python3.13.17: `manage.py check` passed;
  `manage.py makemigrations --check --dry-run` reported no changes;
  `manage.py test --noinput` passed591tests in272.096s, one existing platform skip.
  The complete suite ran outside the Windows filesystem restriction so existing
  hardlink tests were actually executed. CI supplies the required3.12–3.14 matrix.
- Explicit Node24.19.0: `npm ci --cache C:/dev/ajiri/.npm-cache` installed358
  packages with zero audit findings; `npm run lint` and `npm run build` passed
  (build1.62s). Independent SHA256 inventory comparison matched all42 committed
  `frontend_build` files; there is no frontend source/build change in this package.
- `git diff --check` passed. Before commit, branch and author/committer were
  checked; both use Michael's configured noreply address. No secrets or private
  records are included. This earlier documentation package passed all six PR100
  checks and merged into MVP2 as396913c. It did not change the activated runtime.

## Remaining acceptance

The post-activation Jira query returned16 unfinished non-Epic items. AJ84 is Done
for its documented bounded deployed scope. AJ83 remains In Progress:8/10 consented
participants finding a current relevant role within five minutes is unverified.
Genuine original roles/employers remain AJ53/AJ82 work, not synthetic fixtures.
Broader sending (AJ17/26/43), public vacancies (AJ42), live scanner/quarantine and
certificate activation (AJ52/79), hosted storage/queue (AJ47/48), analytics activation
(AJ51), consented pilot/disclosures (AJ86) and commercial Daraja prerequisites
(AJ44/45/46, last) remain unfinished. Archived implementations and synthetic
rehearsals are retained; no live-service or participant acceptance is invented.
