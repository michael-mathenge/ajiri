# Open decisions — 1 November 2026

Only genuinely unresolved inputs are listed here. The implementation and live
verification steps are in [next actions](docs/ROADMAP_NEXT_ACTIONS.md).
Completed checkpoint choices, account implementation and owner inbox pilots are
not repeated approval requests. The old list is [archived](maintenance/HISTORY.md#record-decisions-pending-2026-10-31).

Dependency choices recorded11November under the current authorized maintenance
task (reversible defaults,not additional approval checkpoints):

| Item | Options | Default chosen | Impact |
|---|---|---|---|
| dateutil/Celery compatibility | Force dateutil3; retain older Celery; use updated compatible graph | Celery5.7 with its required dateutil2.9.0.post0 | PR67 deferred; no dependency bypass or dateutil3 timezone behaviour introduced. |
| Residual development-tool advisory | Force minimatch11 override; downgrade ESLint; wait for supported compatibility | Keep compatible graph and track AJ87 | Production-only audit0; three moderate development nodes remain openly recorded. |

| Decision/input | Who supplies it | Why it is still needed |
| --- | --- | --- |
| Feed-release authorization and timing | Michael | Local display code is ready for review; the explicit no-push/no-merge/no-production limit remains until changed. |
| Normal sending acceptance AJ-17/26/43 | Michael/operator plus agent review | Confirm actual provider/privacy facts, genuine eligible vacancy and independently consented recipient for the normal paths; completed synthetic pilot evidence is retained. |
| Genuine employer/public vacancy AJ-53/42 | Employer/account owner and independent reviewer | Identity, authority, source and deadline cannot be inferred from a feed or synthetic fixture. |
| Capacity and backup retention | Michael/operator | One-time keep-four/delete17 server cleanup completed after explicit confirmation; dashboard now 228.7/512 MB. Measure feature headroom; ongoing retention remains report-only pending its own policy. |
| Certificates AJ-79 | Michael/operator | PDF/quota defaults are implemented on an inactive branch; confirm final file/retention policy, scanner and capacity before activation. |
| Scanner/storage/worker hosting AJ-52/47/48 | Michael/operator | Actual engine/target/host eligibility, durable private recovery and resource limits need real evidence; private credentials are entered outside chat. |
| Analytics AJ-51 | Product/privacy owner | Actual purpose, choice wording, lawful basis, retention, cohort/report access and processing destination remain factual decisions. |
| Commerce AJ-44/45/46 | Merchant/product/privacy owner | Merchant/product eligibility, actual sandbox mapping and final price/term/refund/tax facts are unresolved. No live charge or paid enforcement is implied. |
| Jira cleanup AJ-80 | Michael | Approve exact descriptive historical titles/relates-to mapping before editing those 23 original entries; retain history. |

No repeated approval is needed for already approved designs or routine local
implementation within scope. This document grants no new production, purchase,
legal-consent, credential or irreversible user-data authority.
