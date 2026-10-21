# Form validation

AJ-33 migrates the nine existing forms: registration, login, account recovery
(including verification), profile fields, private CV upload, CV drafting, job
filters, email alert choice and application package editing.

React Hook Form 7.90.0 stores values in memory. Zod 4.6.7 uses the tree-shakable
Mini API with explicit plain-language messages. The shared resolver validates
on submit and renders every issue; corrected input can be submitted again.
Server errors remain authoritative and retain existing IDs and associations.
No password trimming or local/session storage of form values is introduced.

Incomplete CVs can be saved; partial dates must be completed or cleared. Approval
remains a separate explicit action bound to saved content. Alert choices preserve
the existing decision replay key. No consent is preselected by this migration.
Upload checks only inspect browser metadata; server content checks remain essential.
An immediate submit guard prevents parallel validation/mutations, and recovery
cooldowns are checked before queuing validation so requests never send on expiry.

Public-page budgets remain unchanged. Dialog primitives are imported directly by
the job/application screens instead of the shared public UI bundle. Toast controls
load when a notification is first shown, preserving accessible dismissal.

Verification: see JIRA_ROADMAP_PROGRESS.md for actual commands/results. Smoke tests
should use synthetic local data: submit blank registration, correct each field,
keep agreement unchecked until personally chosen; save an incomplete CV; reject a
partial date; confirm the saved revision before approving; inspect all server
errors. Do not send real applications as a form test.

Sources: https://github.com/react-hook-form/react-hook-form and
https://zod.dev/packages/mini . No schema or database migration is required.
Rollback restores prior frontend source/build while retaining data and preferences.
