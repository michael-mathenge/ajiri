# Pending work — 1 November 2026

This is the single current action list. Completed work belongs in
[JIRA_ROADMAP_PROGRESS.md](JIRA_ROADMAP_PROGRESS.md), not in a new to-do list.
Read-only Jira reconciliation on 1 November returned 14 open non-Epic issues:
13 In Progress and AJ-80 To Do, with no next page. No Jira edits were made.

## Baseline: do not rebuild or repeat

- MVP1 source `3408565930b7e6fb5cefe6b620d88ebdc8f25a0e` (PR72) was deployed on
  1 November with zero migrations. Account-security mail was configured; employer
  posting, saved searches, application/alert mail and public vacancies were off;
  freshness was on. This is recorded release evidence, not a new live inspection.
- The showcase, CV workflow, account recovery code, freshness, employer review,
  public-page implementation and owner saved-search implementation already exist.
  Feature implementation is distinct from enabled production acceptance.
- Owner application inbox/content and earlier alert/unsubscribe pilots completed.
  Michael reconfirmed owner inbox delivery on 1 November; AJ-17 comment 10171
  records it. Do not request another copy of those completed pilots or infer
  acceptance of additional sending paths from that confirmation.
- The 26 October scheduled backup and isolated 17-file restore completed. A fresh
  MVP1 off-server recovery copy was also verified. Later scheduled runs still need
  their own receipts; this is not a missing first-run task.
- Last recorded hosting expiry: **30 November 2026**, superseding 19 November.
  Post-cleanup dashboard quota: **228.7/512 MB (45%)**. On 1 November, 17 older
  on-server snapshots were explicitly approved and deleted, retaining four verified
  newest snapshots and all off-server copies. Venv backup/seven restore folders
  were already absent. Recheck quota/expiry before the next release; routine
  retention remains report-only beyond this one-time cleanup.

Evidence for the MVP1 source/flags/quota/expiry and PR73 CI is in
`reports/MVP1_RELEASE_EXECUTION_2026-11-01.md` and the progress ledger on branch
`codex/backend-inactive-20261031`. That broader branch and its report are not
merged into this checkout. Completed feed-release and recovery results are in this checkout's ledger.

## 1. Privately evaluate and activate feed discovery

**State:** implemented, merged in PR74 and deployed as application release
`2a4dfdf05f5371e61e13e7a68b3009993fdd0a2a`. All six checks passed on both
PR head and merged main. The documentation closeout retains the identical application
and generated build. `JOB_FEED_DISPLAY_ENABLED=False` was verified after reload;
freshness stayed on and all existing sending/public/employer exclusions stayed off.
No new Jira key was assigned and no migration was introduced.

1. Michael runs the SELECT-only counts command below privately in the production
   virtualenv. Counts were deliberately not run by the agent.
2. Review the [display options](JOB_FEED_DISPLAY_OPTIONS.md), then privately enable
   only `JOB_FEED_DISPLAY_ENABLED` and reload if desired. Leave eligibility and
   sending gates unchanged.
3. Verify signed-in warning/date/source rendering and absent apply, CV selection,
   cover-letter and send controls. Scams and known closed listings stay hidden.
   Disable this switch to roll back visibility.

Local PowerShell (using an existing configured database):

```powershell
Set-Location C:\dev\ajiri\ajiri-backend
python manage.py job_feed_display_counts
```

Private production Bash: `workon ajiri`, then
`cd /home/Mathenge/ajiri/ajiri-backend` and the same management command.
Expected: aggregate JSON for one evaluation time, with eligible, supplemental,
display-off/on and 14-day counts. No ingestion, archiving, notification or transport.

## 2. Complete normal sending acceptance — AJ-17, AJ-26, AJ-43

**State:** all In Progress. Owner pilots are complete. Stage2 implementation exists
on `codex/review-02-application-alert-search`; draft PR73 head `38bf953` has recorded
all-six-check CI success. It is not merged, deployed or live-accepted. Do not rebuild
that implementation or merge the whole broader PR71 to obtain it.

1. Review PR73's exact code, tests and acceptance against current main. Confirm
   genuine eligible vacancies, verified mailboxes, explicit alert/search consent,
   immutable application authorization and approved provider/privacy facts.
2. Finish any missing bounded callers/scheduling and operational handling, preserving
   shared budgets, unsubscribe, window deduplication and unknown-handoff blockers.
   Do not infer a production scheduler from a test integration.
3. Under separate sending/release authorization, deploy the focused stage and run
   bounded normal-transport acceptance. Verify the appropriate inbox and attachment
   evidence, failed/unknown behavior and disabled-switch rollback; record per-channel
   results. An old synthetic owner pilot does not replace normal-path acceptance.

## 3. Verify genuine employer and public publication — AJ-53, AJ-42

**State:** implementations exist; production switches were off at MVP1 release.

1. Verify general account-mail onboarding and a real organisation's identity,
   authority to advertise, original listing and future deadline.
2. Have an independent staff reviewer assess the organisation and vacancy, including
   absence of applicant fees; retain review and withdrawal evidence.
3. When authorized, enable only the reviewed posting/publication scope. Verify
   owner boundaries, source/date disclosures, expiry, sitemap/metadata and switch-off
   behavior. Display-only feed listings remain excluded from public JobPosting pages.

## 4. Capacity, recovery and hosting operations

**Owner:** Michael/operator; agent can inspect receipts and prepare local checks.

1. Recheck actual disk quota and renewal date; confirm the latest scheduled backup
   receipt, private off-server copy, hashes and isolated restoration. Reuse completed
   evidence where valid instead of repeating an unchanged backup or creating extra
   on-server archives without capacity.
2. Measure required release/transient/certificate storage against available headroom.
   Choose a suitable capacity remedy before adding storage-heavy services. Backup
   retention remains report-only until a concrete pruning policy is authorized.
3. Renew before the displayed expiry and record the new date. Keep the desktop
   scheduler availability limitation explicit; an always-on scheduler requires an
   eligible host and private access before claiming unattended availability.

## 5. Finish broader inactive features without rebuilding them

**State:** these issues remain In Progress. Broader implementations and rehearsals
exist on `codex/backend-inactive-20261031` / draft PR71. Review that evidence before
writing replacement code; none is accepted as live by the MVP1 deployment.

| Work | Actions, in order | Completion evidence still needed |
| --- | --- | --- |
| AJ-52 scanning | 1. Select the actual engine/host and processing destination. 2. Resolve signature freshness, private quarantine, legacy files and resource limits. 3. Verify fail-closed behavior and recovery on the chosen host. | Real host/engine/signature evidence; no claim that existing uploads are scanned. |
| AJ-79 certificates | 1. Review the existing inactive upload implementation against Jira. 2. Confirm PDF/quotas, capacity, scanner and retention choices. 3. Isolate its additive schema, run ownership/quota/replacement/export/backup tests, then seek its separately required activation approval. | Capacity, private restore, scanner integration and deployed acceptance; text CV certifications alone are insufficient. |
| AJ-47 storage | 1. Select an eligible actual target. 2. Complete historical PostgreSQL bootstrap/search and private object-store verification. 3. Rehearse interruption/recovery and a single-writer cutover before proposing production migration. | Canonical row/file/ownership checks on actual target and a data-preserving rollback; no stale SQLite fallback. |
| AJ-48 queue | 1. Select a durable broker/worker host. 2. Verify host/disk loss, leases, dead letters and receipt reconciliation. 3. Validate deployment and operator recovery before enabling workers. | Actual hosting/durability and unknown-outcome handling; never repeat uncertain provider IO. |
| AJ-51 analytics | 1. Confirm purpose, lawful basis/wording, retention, cohort/access and processing facts. 2. Review inactive durable consent/collector work. 3. Verify withdrawal and minimized events before activation. | Independent versioned choice and reviewed operational/privacy acceptance; no collection inferred from registration or email consent. |

## 6. Payments last — AJ-44, AJ-45, AJ-46

**State:** all In Progress; synthetic contracts and inactive durable work exist.

1. Michael supplies genuine merchant/product eligibility, private sandbox access and
   the commercial offer, refund/cancellation/tax/privacy facts. Never put credentials
   in these documents or treat preview prices as approved offers.
2. Review existing adapters and durable receipt/entitlement work; finish the actual
   authenticated status/reversal mapping and any missing paid-action enforcement.
3. Verify sandbox failure/cancel/duplicate/out-of-order/unknown outcomes and entitlement
   expiry/refunds/Free fallback. Propose live charging only after separate operational
   acceptance. Browsing, applying and existing documents remain free.

## 7. Jira history cleanup — AJ-80

**State:** To Do. Document housekeeping does not authorize deleting Jira history.

1. Read the existing 23-entry mapping proposal on `codex/backend-inactive-20261031`
   (`docs/JIRA_UPDATE_CLEANUP_PROPOSAL.md`) and confirm each original comment/link.
2. Present exact descriptive titles and non-destructive relates-to links for the
   AJ-54–AJ-76 historical entries, preserving comments/authors/dates/status history.
3. Apply only the separately approved ticket edits and verify the resulting links.
   Do not run `tools/jira_sync.py` or mark live acceptance from old Done comments.

## Order and ownership

Agent work can proceed on local review, tests, missing bounded code and focused
release preparation. Michael supplies private access, genuine employer/provider/
commercial facts and consequential service/activation decisions. Work blocked on
those inputs does not prevent independent local work. Use the latest release receipt for exact merged/deployed revisions. The feed
switch remains default-off for Michael to enable privately.
