# Job keyword search

AJ-39 adds the optional `q` parameter to job lists. It searches title, company,
location, description and requirements. All terms must match; prefixes allow
partial words. Title matches carry the greatest weight, followed by company and
requirements. BM25 relevance is followed by date/id for stable pagination.
The existing title substring, location, type and skill filters remain compatible
and combine with keyword search. Active/non-scam and authentication guards remain.
Match scores are independent skill overlap; relevance does not change eligibility.

Input is capped at255 characters,12 words and64 characters per word. Unicode
letters/digits are normalized and quoted as literal terms. OR/NOT/NEAR are words,
not operators. Punctuation-only input produces no matches. SQL uses parameters.
This is prefix keyword search, not semantic understanding or a claim of suitability.

## Index and release

Additive jobs.0011_job_full_text_search creates an external-content SQLite FTS5
index and insert/update/delete triggers, then indexes existing rows. Job data is
not rewritten. Bulk updates use the same triggers. Only the five listed job text
fields are indexed; account/profile/application/private-file data is excluded.
Production SQLite3.37.2 reports ENABLE_FTS5=1 (read-only capability check,21Oct2026).
No new library or ingestion-endpoint change is needed. PostgreSQL needs a separate
reviewed migration strategy; this migration explicitly refuses other engines.

Deploy only after consistent verified off-server backup. Pause writers, stage
reviewed source, check expected migration plan, apply only0011 and reload. Never
activate code against an unindexed database. Roll back source while retaining
the additive index and newer job writes. If explicitly reversing0011, only derived
index/triggers are removed; original jobs remain and a later reapply rebuilds it.
Retain normal private backup/restore verification; no automatic pruning.

## Verification

```powershell
cd C:\dev\ajiri\ajiri-backend
python manage.py test jobs.test_search --noinput
python manage.py benchmark_job_search --runs 20
```

The benchmark is read-only. It emits counts, timings and known-title recall only;
no job text, account information or private data. Four fixed generic queries use
20 runs; report median/p95 latency for a20-row page and exact-title recall in the
top5 for up to12 recent distinct titles. This is a bounded relevance smoke check,
not human validation of all job suitability. Record actual production figures
before declaring real-data acceptance. Working target: p95 below200ms at the
current free-tier corpus, and known-title recall inspected for regressions.

Tests cover title weighting, all-field/prefix search, independent filters, Unicode,
literal operators, punctuation, bounds, SQL safety, bulk create/update/delete,
index query plan,1,001-listing stable pagination and data-preserving rollback/rebuild.
Client regressions cover keyword submission and old title links. OpenAPI is
regenerated for q; existing API contract CI detects drift.
