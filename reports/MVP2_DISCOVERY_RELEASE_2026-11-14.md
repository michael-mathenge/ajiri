# MVP2 discovery and private follow-up release

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
  records are included. Required PR checks remain pending until actually observed.

## Remaining acceptance

AJ83 remains In Progress:8/10 consented participants finding a current relevant
role within five minutes is unverified. Genuine original roles/employers remain
AJ53/AJ82 work, not synthetic fixtures. Broader sending, public vacancies, live
scanner/quarantine, hosted storage/queue, analytics activation and commercial
Daraja prerequisites remain unfinished. AJ84 is not represented as deployed yet.
