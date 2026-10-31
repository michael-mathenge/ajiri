# Backend handback — 31 October 2026

Branch codex/backend-inactive-20261031, isolated at
C:\dev\ajiri\.worktrees\backend-inactive-20261031. Original dirty checkout,
lockfile, stash and Git configuration were preserved. Draft PR:
https://github.com/michael-mathenge/ajiri/pull/71 (unmerged).

No deployment, production migration, runtime flag change, live mail, Daraja call,
charging or real-account export/erasure occurred. All new features default off.
The roadmap is NOT wholly complete: the boundaries below remain explicit.

| Story | Status | Source/tests and remaining boundary |
|---|---|---|
| Account email prerequisite | code-complete but inactive | ec57336; 475 full local tests passed, one existing skip; shared general security-mail transport. Controlled provider/inbox activation pending. |
| AJ-17 | code-complete but inactive | c497c9e; 484 full local tests passed, one skip; immutable authorization and document rechecks. All six CI checks passed. |
| AJ-26 | code-complete but inactive | baf8829; 480 full local tests passed, one skip; consent/freshness/70% alert threshold and shared receipts. CI41195023043 all six passed. |
| AJ-42 | blocked | Existing public vacancy path reconciled; genuine current listing/source evidence and final publication approval still required. No fabricated jobs or weaker freshness. |
| AJ-43 | code-complete but inactive | 6338c83; 488 full local tests passed, one skip; durable daily/weekly window delivery and shared receipts. Later certificate CI includes this source. |
| AJ-44 | blocked | 2a9fc62; merchant/product/offer/privacy/tax/refund/retention facts unresolved. Requirements and safe defaults documented; no invented prices/agreements. |
| AJ-45 | blocked | 2a9fc62; real sandbox OAuth/Express/query, durable claims and bounded callback hints. 14 focused payment/alias tests passed3.285s; CI41202823539 all six passed. Actual merchant sandbox acceptance and authenticated full settlement/reversal mapping remain missing; no production transport or verified settlement writer. |
| AJ-46 | blocked | 5bdafb7; real additive settlement/grant tables, atomic fixed-term projection, concurrent deduplication, terminal reversal and Free fallback. Eight final focused tests passed0.427s. Actual provider evidence writer and exact commercial capability/action enforcement remain missing; final full CI is unverified. |
| AJ-47 | blocked | 4b2f540; seven actual-filesystem copy/isolated restore/recovery tests passed1.048s; CI41202056856 all six passed. Actual private object-store target/driver acceptance and PostgreSQL bootstrap/search parity unresolved: historical jobs.0011 explicitly rejects non-SQLite. No history faked. |
| AJ-48 | blocked | 5a724e0; durable UUID-only Celery publication, leases/recovery and shared receipts; ten queue/alias tests passed3.388s; CI41200587491 all six passed. Actual durable worker/broker/shared-store host, scheduler/monitoring and new crash/lost-ledger acceptance remain external. |
| AJ-51 | code-complete but inactive | 8b2dfc7; durable separate versioned choice/withdrawal and identity-free daily counters; six focused tests passed0.403s; CI41199055095 all six passed. Actual purpose/legal/notice/retention/report-access decisions pending; no collection or external SDK. |
| AJ-52 | blocked | b1bb30b; real bounded local ClamD protocol and fail-closed quarantine; 27 focused scanner/certificate/upload tests passed3.052s; CI41198355067 all six passed. Actual supported private scanner host/signature/capacity and engine acceptance remain external. |
| AJ-53 | blocked | Existing independent employer/vacancy review path reconciled; normal account-mail prerequisite added. Genuine organisation, authority and current vacancy evidence still required. No fake employer/review. |
| Certificates AJ-79 | code-complete but inactive | Existing ticket reused before implementation; be8b0c7; additive private owner PDF/quarantine API, count/byte quotas and integrity. Corrected full502 tests passed367.411s, one skip; CI41197654431 all six passed. Real scanner/host/notice activation pending. |
| Cleanup proposal AJ-80 | done (proposal only) | 623064c mapped all23 generic Update entries AJ-54–AJ-76 to existing topics; original tickets/history/statuses were preserved. This is not approval to perform the proposed cleanup. |

AJ-17/AJ-26/AJ-79 progress was already recorded through Jira (comments10132,
10131,10133 respectively; AJ-79 moved to In Progress). Pending JSON excludes
those earlier updates and contains only new unsynchronized evidenced progress.
No inactive story was marked Done from local implementation alone.

## Verification and limitations

Each earlier code package passed all six required CI gates before the next story
started, through payment head2a9fc62. Full backend matrix uses repository-pinned
requirements. Preserved local Python3.12.6 reports Django6.1 rather than pinned
6.1.2; local runs do not prove exact dependency parity. Final entitlement full
local suite result will be appended below; its GitHub CI remains unverified.

Exact Node24.19 locked offline npm ci, lint and build passed for the final
entitlement package (build2.18s), as for earlier packages. Existing CI frontend
job still uses Node22; quality/browser use24.19. CI configuration was preserved.
No frontend source changed. Existing five online-audit advisories remain disclosed;
offline npm's zero summary is not a current vulnerability clearance.

GitHub browser refresh was blocked by automatic approval review due to its usage
limit after entitlement push. It did not determine the action unsafe, but final
CI inspection and PR title/body editing were not performed. The draft PR still
has its earlier narrower description; a replacement is saved in reports/PR71_BODY.md.
No alternate browser path was used to bypass that gate.

DECISIONS_PENDING.md records item/options/default/impact. Per-feature flags,
prerequisites and data-preserving rollback are in docs/BACKEND_ACTIVATION_CHECKLIST.md.
New additive migrations are profiles.0008 and jobs.0017–0021. None ran in production.
Never reverse populated financial/private-file tables or restore stale ledgers
across uncertain handoffs. Actual provider/host/merchant/legal acceptance is not
inferred from fixtures, local commits or merged historical source.

## Jira dry-run handback

The sync script was NOT executed: AGENTS.md section13 forbids running it even
without --apply. JSON validation is not script execution or actual dry-run output.
The prepared input is reports/status_updates.json in this isolated worktree.
From the original repository root, Michael can run:

```powershell
Set-Location C:\dev\ajiri
python tools/jira_sync.py --file .worktrees/backend-inactive-20261031/reports/status_updates.json
python tools/jira_sync.py --file .worktrees/backend-inactive-20261031/reports/status_updates.json --apply
```

Expected: dry-run reviews the proposed In Progress comments; apply only after
review. No simulated provider or synthetic data is represented as deployed acceptance.

## Final local result

Implementation head5bdafb7 passed the full local backend suite: 551 tests in
339.967 seconds, OK with one existing platform skip. Command (backend directory):
PYTHON_DOTENV_DISABLED=1, DEBUG=True, REAL_EMAIL_ENABLED=False, preserved Python
3.12.6 environment, manage.py test --noinput. Sanitized negative-case error events
were expected test outcomes, not passing production probes. Full repository Ruff,
OpenAPI consistency and exact Node24.19 frontend gates/build bytes also passed.
Remote CI for the final entitlement head remains unverified; the package is not
claimed production-ready or fully verified against pinned dependencies.
