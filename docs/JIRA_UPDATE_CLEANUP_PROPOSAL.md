# Proposal: reconcile generic Update issues

Tracked by AJ-80. Read-only review on 31 October 2026 found AJ-54–AJ-76 each
had one comment dated 25 October, no description and no issue links. Their generic
Done status does not establish new product or deployment acceptance. The table
maps comment topics to existing story titles; it proposes relationships, not
automatic duplication/deletion. Michael decides whether to rename and relate them
as historical evidence records. Preserve original comments, authors and history.

| Entry | Comment topic | Proposed related existing story | Qualification |
|---|---|---|---|
| AJ-54 | Privacy notice/registration consent | AJ-24 | Draft legal wording is not legal approval. |
| AJ-55 | Account deletion/export | AJ-25 | Implementation is not permission to act on real accounts. |
| AJ-56 | Manual backup and isolated restoration | AJ-23 | Manual evidence does not establish automated scheduler execution. |
| AJ-57 | Health endpoint and structured logging | AJ-22 | Preserve original deployment evidence date. |
| AJ-58 | Hosting renewal expiry | AJ-21 | Recorded 19 November expiry needs actual renewal recheck. |
| AJ-59 | Registration verification | AJ-20 | General delivery remained constrained by owner-only pilot. |
| AJ-60 | Password reset | AJ-19 | Separate flow implementation from general inbox acceptance. |
| AJ-61 | Implemented cookie CSRF mitigation | AJ-18 | Implementation topic, distinct from design AJ-13. |
| AJ-62 | Production hardening | AJ-12 | Historical host evidence, no current config changes proposed. |
| AJ-63 | Content/size validation | AJ-11 | Content validation is not malware scanning AJ-52. |
| AJ-64 | DRF throttling | AJ-10 | Preserve actual proxy/client identity test evidence. |
| AJ-65 | Password validation | AJ-9 | Registration validators, not reset-only validation. |
| AJ-66 | GitHub protection/dependency/security hygiene | AJ-8 | No changes to protection or Git configuration proposed. |
| AJ-67 | Modernisation/checkpoint planning | AJ-16 | Historical planning evidence. |
| AJ-68 | Off-server backups/renewal reminders | AJ-15 | Distinct from scheduler execution evidence AJ-23. |
| AJ-69 | Vulnerability scan/coverage baseline | AJ-14 | Historical scan is not current dependency clearance. |
| AJ-70 | Cookie CSRF design | AJ-13 | Design, not implementation AJ-18. |
| AJ-71 | Public-job/SEO spike | AJ-38 | Spike does not complete publication AJ-42. |
| AJ-72 | Dismissed snapshot restoration | AJ-37 | Preserve original snapshot acceptance evidence. |
| AJ-73 | Staging decision/setup | AJ-36 | Staging is not a production storage/worker migration. |
| AJ-74 | Environment example/deployment runbook | AJ-35 | No secret files inspected or changed. |
| AJ-75 | Committed build/line-ending strategy | AJ-31 | Strategy differs from each package's build verification. |
| AJ-76 | Swahili/i18n assessment | AJ-41 | Assessment does not establish translated product UI. |

Recommended action after final approval: descriptive historical titles plus
non-destructive relates-to links to the mapped stories. Do not merge comments
without retaining their source IDs/date; do not change source issue statuses from
these comments alone. No original entry was renamed, transitioned or deleted.
