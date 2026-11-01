# Backend activation checklist

1 November reconciliation: this table separates source defaults from remaining
activation gates. MVP1 PR72 is recorded deployed at `3408565`: account-security
mail configured; employer posting, saved searches, application/alert mail and
public vacancies off; freshness on. Do not disable existing account service merely
because its code default is False. See [next actions](ROADMAP_NEXT_ACTIONS.md) for
the current ordered work and branch-specific implementation evidence.

No item below authorizes activation. Preserve currently deployed configuration;
new feature switches default off in source. Never reverse populated migrations
as routine rollback or discard newer writes. Back up before migration, apply
additive schema before serving new code, and verify isolated restoration first.

| Feature | Switch / state | Prerequisites before approval | Rollback |
|---|---|---|---|
| Account verification/reset | Configured in MVP1; source switches default off, account_security mode required | Retain completed owner-inbox confirmation and per-path evidence. Monitor the configured service; general employer onboarding acceptance remains separate from the completed owner test. | Disable account-security switch only for an authorized rollback; retain ledger/budgets and account data. No schema reversal. |
| Display-only feed browsing | JOB_FEED_DISPLAY_ENABLED=False; PR74 code deployed, optional browse-only activation remains private | Owner reviews eligible/supplemental/browse-on counts using the ajiri Python 3.12 virtualenv, then privately enables and reloads. Label every supplemental row; offer no application/document/send action. | Disable display switch; keep freshness and all eligibility gates unchanged. No migration. |
| Employer posting AJ-53 | Existing posting controls; no runtime change | General onboarding acceptance; genuine employer/authority and independent staff review; future deadline/no applicant fee | Disable posting, retain freshness/audit and historical applications. |
| Public vacancies AJ-42 | PUBLIC_JOBS_ENABLED stays off | Genuine eligible listing, public metadata/source checks and expiry verification | Disable publication; preserve current availability rules. |
| Application email AJ-17 | APPLICATION_EMAIL_ENABLED stays off | Production transport code review, exact immutable approval/authorization, current recipient/attachment/privacy policy and controlled pilot explicitly approved | Disable sending; retain receipts/unknown blockers, documents and authorizations. |
| Match email AJ-26 | ALERT_EMAIL_ENABLED stays off | Explicit independent consent, verified current mailbox, fresh job, shared budgets, unsubscribe and transport acceptance | Disable sending; preserve opt-outs and receipts. |
| Saved-search email AJ-43 | Existing captured contract only, no activation | Real transport implementation and consent-window/deduplication acceptance | Disable email worker/caller, preserve windows and receipts. |
| Certificates AJ-79 | Not implemented in this package | Additive schema/API, quotas/concurrency, quarantine/download integrity, scanner and real capacity/backup evidence | Disable routes, retain files/table/newer writes. |
| Storage AJ-47 | No production switch | Target credentials privately entered, private object storage and historical schema/search rehearsal, interrupted recovery and one-writer cutover | Before new target writes only: restore original writer; after new writes require reconciled reverse migration, never stale SQLite fallback. |
| Queue AJ-48 | No hosted worker activation | Durable host/broker, lease/dead-letter operations and crash/redelivery acceptance against shared ledger | Stop workers, reconcile reserved/unknown receipts before any replay. |
| Analytics AJ-51 | No collection activation | Durable versioned choice, purpose/legal facts, retention/cohort/access rules and aggregate collector implementation | Disable collection, preserve withdrawals; pruning requires policy approval. |
| Scanner AJ-52 | No claim of actual scanning | Real engine/host, private quarantine, signature freshness, resource limits and fail-closed integration | Disable uploads, never bypass quarantine to restore availability. |
| Daraja AJ-44/45 | No live calls | Genuine merchant/product facts, durable adapter/reconciliation, private sandbox access and verified sandbox evidence, commercial/legal decisions | Disable initiation; reconcile pending/unknown outcomes without retrying initiation. |
| Entitlements AJ-46 | No charging/enforcement activation | Exact offers/refund/expiry decisions and durable authoritative payment evidence | Disable paid capabilities with Free fallback; preserve verified receipts and free applying/documents. |
