# Backend continuation — 31 October 2026

Work is on codex/backend-inactive-20261031, isolated from the dirty original
checkout. This is a progress record, not a completed-roadmap or deployment claim.
All new switches default off. No production migration, deployment, live mail,
Daraja call, charging or real-account export/erasure occurred.

| Scope | Current evidence |
|---|---|
| Account email prerequisite | ec57336: separate general verification/reset gate and shared ledger; 475 backend tests passed, one existing platform skip. |
| AJ-26 | baf8829: real inactive match transport and bounded command; 480 backend tests passed, one skip; consent/mailbox/freshness/70% threshold and receipt rechecks. Jira comment 10131 recorded progress, status retained In Progress. |
| AJ-17 | c497c9e: exact immutable-authorized general application transport; 484 backend tests passed, one skip. Jira comment 10132 recorded progress, status retained In Progress. |
| AJ-43 | 6338c83: real inactive saved-search transport with durable daily/weekly windows and overlapping receipt deduplication; 488 backend tests passed, one skip. |
| AJ-42/AJ-53 | Existing public/employer review implementation reconciled; general account onboarding prerequisite added. Genuine organisation/authority/current-vacancy evidence remains external. No source/freshness rule weakened. |
| AJ-79 | Additive profiles.0008/private API, quarantine, concurrent count/byte quotas, explicit removal, integrity-checked downloads and export/erasure inventory integration passed the corrected 502-test full run (one existing skip). Actual scanner/hosting activation remains pending; no qualification verification or employer sharing. |
| AJ-47/AJ-48/AJ-51/AJ-52 | Existing test/lab contracts are not live service completion. Durable integration and operational prerequisites remain open. |
| AJ-44/AJ-45/AJ-46 | Merchant/product/commercial/legal facts remain unresolved; no payment or paid-entitlement activation. |
| AJ-80 | 623064c: proposal mapped all 23 generic Update comments to existing story topics; original AJ-54–AJ-76 issues unchanged. |

Exact Node 24.19 locked installation/lint/build passed for each completed email
package, and all 38 generated build files matched. Optional pinned Ruff/OpenAPI
tools were added only to local .tooling; those checks passed. The preserved local
Python 3.12.6 environment reports Django 6.1; the repo pins 6.1.2, so these local
runs do not establish an exact pinned dependency environment. GitHub CI for pushed
c497c9e passed all six checks on its dependency installation. Draft PR71 remains
unmerged: https://github.com/michael-mathenge/ajiri/pull/71. Later heads need their
own CI evidence. The online locked frontend audit reported five advisories; an
offline install's zero summary is not a fresh vulnerability clearance.

DECISIONS_PENDING.md consolidates reversible defaults. Per-feature prerequisites,
switches and data-preserving rollback are in docs/BACKEND_ACTIVATION_CHECKLIST.md.
No issue was marked Done from local implementation alone.

The sync script was not run, in accordance with AGENTS.md section 13. The pending
JSON contains only new unsynchronized progress; AJ-17/AJ-26 updates already posted
through the connector are excluded to avoid replaying them. Review from this
worktree and run the supplied dry-run/apply commands only in your own terminal.
