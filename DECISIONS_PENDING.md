# Decisions pending — 31 October 2026

Implementation choices below are reversible defaults, not activation approval.
No deployment, production migration, runtime flag changes, live recipient mail,
Daraja calls, charging, real-account export/erasure or retention pruning is authorized.

| Item | Options | Default chosen | Impact / final decision |
|---|---|---|---|
| Account security mail | Owner pilot only; general transactional security mail | Separate default-off ACCOUNT_SECURITY_EMAIL_ENABLED and account_security delivery mode | Existing pilot preserved. General verification/reset uses current active mailbox and existing 30-account/200-total Nairobi-day budgets; provider/legal/operational activation remains pending. |
| Employer/public vacancy path AJ-53/AJ-42 | Publish synthetic vacancies; require genuine reviewed source | Retain independent review and strict current-evidence checks | Genuine organisation/listing evidence remains external; no fabricated inventory or freshness relaxation. |
| Certificates AJ-79 | PDF; images; office formats | PDF, 5 MiB/file, five files/20 MiB, owner only, quarantine required | Existing AJ-79 reused rather than duplicate ticket. No automatic employer sharing; scanner/capacity/retention activation pending. |
| AJ-17/26/43 delivery | Direct backend bypass; shared ledger | Shared ledger, consent and immutable application authorization | Unknown handoffs cannot auto-retry; no real inbox acceptance claimed. |
| General match alerts AJ-26 | Automatically enable on ingest; separate bounded dispatcher | GENERAL_ALERT_EMAIL_ENABLED=False; requires general account transport and existing ALERT_EMAIL_ENABLED, freshness on, consent before notification | New operator command only; no scheduler installed or activated. Any existing receipt blocks another handoff, including definite failures pending a separately scoped explicit-retry policy. Old notifications cannot become eligible through a later opt-in. |
| AJ-51 analytics | External SDK; first-party aggregate collection | Default-off first-party allowlisted aggregates, no identifiers in events | Purpose, choice wording, lawful basis and retention require final factual decisions. |
| AJ-52 scanner | External upload service; self-hosted ClamAV | Private fail-closed scanner boundary | Hosting/signature freshness/resource capacity need real evidence; content validation is not malware scanning. |
| AJ-47/48 infrastructure | Production switch now; inactive durable integration | No storage/broker switch | Actual target access, isolated restore and host durability remain prerequisites. |
| AJ-44/45/46 commerce | Invent prices/merchant terms; hold pending | No charging or paid entitlement activation | Merchant/product/legal facts cannot be inferred. Free browsing/applying/existing documents preserved. |
| 23 Update tickets AJ-54–AJ-76 | Delete; rename/resolve after provenance review | Proposal only, preserve all issue history/statuses | Inspect comments/links before suggesting specific merges or replacements. |
| Jira dry run | Execute sync; prepare reviewable inputs | Do not execute tools/jira_sync.py per AGENTS.md section 13 | Provide commands and validated JSON; no fabricated dry-run execution output. |
