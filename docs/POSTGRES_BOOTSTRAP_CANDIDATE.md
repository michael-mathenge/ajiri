# PostgreSQL bootstrap and search candidate

AJ-47,20November2026. Production remains the last verified SQLite/local-media
release e3e8f74. This is a synthetic target candidate, not a selected host or a
production migration-history replacement. No original migration is edited,
removed, copied into a production recorder or silently marked applied.

## Alternate graph

The historical jobs0011 operation deliberately rejects non-SQLite databases.
The new lab generates alternate accounts/profiles/jobs migration modules into a
new disposable package, using current Django model state and the existing built-in
graphs. It checks that the generated state has no differences from current models.
Original migration hashes and the source SQLite migration records must remain exact.
The native graph-generation test performs no database IO and passes independently
of Docker. This alone does not establish PostgreSQL schema compatibility.

In the isolated PostgreSQL target, the lab applies that alternate graph normally,
then a target-only search schema migration. It never uses --fake, syncdb or raw
model-table creation as a substitute for migration execution. A subsequent normal
AddField migration probes forward compatibility on populated data, then reverses
only that disposable test column. The actual target recorder names and generated
graph must be retained as evidence; they are not the original SQLite history.

Any eventual production bootstrap must separately review the graph, its pinned
model/schema state, permission catalogues and the future migration maintenance
route. A lab graph cannot be copied into a real deployment merely because its
synthetic test passed. AUTH_USER_MODEL and existing user/group assignments remain
unchanged by the implementation.

## Dormant search route

SQLite keeps its existing FTS5 join, ranking and three synchronisation triggers.
Only an actual PostgreSQL queryset selects the new native tsvector/tsquery path;
no production database, routing or hosting setting is changed. User terms remain
bounded literal Unicode words and prefixes, passed as SQL parameters.

The candidate uses the simple dictionary, weighted fields and a functional GIN
index, with stable date/PK tie-breaking. It folds decomposable Latin accents but
preserves literal ligatures/stroked letters. Generic unaccent expansion would
change SQLite membership for strings such as AE ligatures and is deliberately
avoided. Fixed tokenizer rules are part of the index contract; changing them
requires an explicitly reviewed rebuild.

The synthetic corpus covers27 cases: empty/punctuation, prefixes, multiword terms,
SQL-like text, English/Kiswahili, accents, decomposed characters, fullwidth digits,
CJK, version punctuation, apostrophes and literal ligatures/stroked letters.
The lab requires matching SQLite/PostgreSQL membership and repeatable ordering
within each backend. Ranking differences are counted, not disguised as BM25
equivalence. It also checks eligibility/filters, pagination and update/delete
synchronisation. Passing a bounded corpus is not a universal Unicode proof.

## Data, private files and recovery

The source is a normally migrated synthetic SQLite database with explicit owner
consent, immutable CV/application approvals, certificate quarantine, an outbox task,
an accepted synthetic receipt/link and its shared reservation. No provider is called.
Full datetime precision, UUID/PK/FK identities, JSON values and through rows are
compared across all managed models. The target's newly generated metadata rows
are emptied before importing the canonical synthetic source, while retaining its
actual alternate migration recorder. This is confined to a new empty lab target.

An exception after ten import writes must roll back all fixture rows. Exact retry,
FK enforcement, sequence reset and alias-safe profile signals are checked. A media
copy interrupted after one complete file must resume by hash verification; private
owner downloads must match and other owners must receive404. No account erasure,
real document transfer, worker activation or live sending occurs.

## Reproduction and current verification

```powershell
python scripts/prepare_postgres_bootstrap_rehearsal.py
docker build -t ajiri-postgres-bootstrap:synthetic <printed-context>
docker run -d --name ajiri-bootstrap-postgres --label ajiri.lab=postgres-bootstrap --network none --tmpfs /var/lib/postgresql/data:rw,nosuid,size=192m -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17.12-bookworm -c listen_addresses=127.0.0.1
docker run --name ajiri-bootstrap-run --label ajiri.lab=postgres-bootstrap --network container:ajiri-bootstrap-postgres --read-only --tmpfs /tmp:rw,nosuid,size=192m ajiri-postgres-bootstrap:synthetic
```

Use unused dedicated names; wait for the isolated database readiness before the
second run. The trust setting is confined to a disposable network-none namespace,
with no published port, host mount or real credentials. It is not a production
authentication configuration. Preserve existing Docker images/containers and
verify created IDs/labels before removing only this lab's disposable resources.

Current local evidence: the alternate graph/model-state test, bound-query contract,
literal folding and SQLite regressions pass. Actual PostgreSQL execution, search
membership/timings and combined fresh-resource recovery are still UNVERIFIED while
the workstation's VirtualMachinePlatform restart is pending. Do not report the
older raw-model PostgreSQL rehearsal as proof of this alternate graph.

The successful lab must emit AJIRI_POSTGRES_BOOTSTRAP_RESULT with measured counts,
canonical checksum, search timings/differences and exact private-file results.
Any assertion failure is failed evidence. Keep the full result private if future
fixture contents change; Jira/public documentation use aggregate outcomes only.

Rollback of this source package leaves original SQLite history/data and search
unchanged. No runtime dependency or production schema migration is introduced.
The existing lab-only psycopg pin remains confined to its Docker image.

References: [alternate Django migration modules](https://docs.djangoproject.com/en/6.1/ref/settings/#migration-modules),
[PostgreSQL text search](https://www.postgresql.org/docs/17/textsearch-controls.html).

## Actual isolated integration -20November2026

The corrected candidate passed on PostgreSQL17.12 (Debian17.12-1.pgdg12+1),
image digest837bed18782820fe967067cb5328b02b0d9992c1be9a37ee0c9c492cfc03af3b.
Forty managed models/628 canonical rows, certificate/outbox/receipt identities,
full timestamps, constraints/sequences and five private files were retained.
All27 search cases had equal result membership; seven had ranking differences,
with stable ordering within each backend. Interrupted import rolled back, copying
resumed, private downloads matched, foreign owners received404, and the subsequent
additive migration/reversal passed. Original SQLite history remained unchanged.

On this tiny synthetic corpus the SQLite median was1.519ms (maximum2.559ms),
while PostgreSQL median was52.595ms (maximum108.174ms). These are cold bounded lab
measurements, not a production benchmark or a PostgreSQL performance improvement.
Index-plan/representative-load tuning remains a provider/cutover prerequisite.

Integration exposed and corrected PostgreSQL rank weights outside its0..1 range;
the1:1:3:8 ratio is now normalized. Regression coverage asserts the normalized SQL.
The lab also now checks identity of its injected import error (Django adds fixture
context), respects protected publication rows in a rolled-back delete probe, and
catches the exact controlled-copy interruption. Failed receipts remain in private
local verification logs. This proves a bootstrap candidate, not a production
migration-history mapping, actual provider acceptance or combined host-loss restore.
