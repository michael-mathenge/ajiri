# Verified production deployment - 20 November 2026

Production is running `03cc9ffb86985c9a48d9e147f457a64ab66aa7a6` (release
[PR129](https://github.com/michael-mathenge/ajiri/pull/129)). All six checks passed
on both the reviewed release head and merged main. Activation and public checks
completed at 19:48 UTC (22:48 Africa/Nairobi). This supersedes the earlier candidate
report's pending deployment status; its historical test failures remain evidence.

## Recovery and capacity

The authenticated PythonAnywhere API used the privately saved Windows credential.
No browser control or foreground window was required. Hosting expiry was read as
16 December 2026. Python 3.12 and Django 6.1.3 were verified on the actual host.

The initial conservative account reading was insufficient by 13,825,916 bytes.
Only 2,427 verified regenerable source-backed Python cache files were removed,
freeing 33,017,856 allocated bytes. Git compaction preserved all 4,586 objects,
refs, configuration and reflogs before removing redundant packs/loose copies.
No production backup, source, private file or user work was deleted.

Web and both previously active writer workflows were paused and all ten queried
active workflow-state counts were zero. The consistent private snapshot completed
at 19:37:21 UTC. Web and writers were restored before downloading the raw database,
media archive and manifest through bounded authenticated API reads. Independent
hashes matched; the ZIP was created locally, never on the server.

The protected off-server recovery folder contains the original raw files, local
recovery ZIP and isolated restoration receipt. The ZIP has 13,596,913 bytes and
SHA-256 `5bd762c65455ff23c63680fce8736c1719ea982087802d828b4bf3ecf91a8941`.
All 46 persisted table fingerprints, schema, sequences and 16 private files
(335,905 bytes) matched the consistent snapshot; SQLite integrity and FK checks
passed. Recovery archives and personal rows remain outside Git.

After activation, 69,959,680 bytes were available. The following API-direct
snapshot budget was 59,720,954 bytes, including the 16 MiB reserve and 8 MiB cache
allowance, leaving 10,238,726 bytes. The older server-transfer-ZIP plan would fail
by 15,984,508 bytes: do not use that plan without resolving capacity. Recalculate
for every run. Retention remains report-only. This was a consistent release
fallback, not evidence that the scheduled desktop automation executed today.

## Activation and verification

Writers/web were paused again only after the independent restoration completed.
The exact reviewed source was staged. Fresh processes passed backend check,
migration drift and an empty migration plan; zero migrations were applied and
production requirements were unchanged. All existing database fingerprints,
private file bytes, configuration hashes and feature-switch states were preserved.
Source rollback would retain live data and erasure journals.

Existing-owner jobs/applications/profile reads passed. Five existing private
document downloads matched their bytes and had no-store handling; four anonymous
private requests returned 401. Disabled certificate/saved-search access remained
404/403. These were authenticated internal acceptance reads, not a new browser
login, access grant or inbox-delivery pilot.

HTTPS health GET/HEAD passed, HSTS was `max-age=604800`, and all 47 public files
matched the checked build. Source was clean at the deployed revision. Web and both
writer workflows were restored. One ordinary ingestion workflow then completed
[successfully](https://github.com/michael-mathenge/ajiri/actions/runs/44805939385)
on that revision. No manual sweep or provider sending was triggered.

Normal application/alert/saved-search sending, saved searches, employer posting,
public vacancies, certificate evidence, scanning and delivery queue remain off.
Freshness stays on. Existing account-security mail remains enabled in
`account_security` mode; this release does not claim normal delivery acceptance.

## Remaining work

The separate outbox, private-storage and PostgreSQL bootstrap rehearsals passed.
Combined fresh database/object/broker/worker recovery and interrupted-cutover
acceptance remain unfinished. Production stays on SQLite/local private media.
The 16 stories retain participant, infrastructure, delivery or commercial gates;
no story is completed from this deployment alone.
