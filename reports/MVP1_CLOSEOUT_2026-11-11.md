# MVP1 closeout and MVP2 handoff — 11 November 2026

## Source and production distinction

Local main was fast-forwarded from12878e1 to reviewed origin/main
e682cac4299102f963c1193d580979ecdefa219f. This is the latest available recorded
production source (PR81,4November), not a fresh11November runtime assertion.
The private original untracked reports/tools/test.md were preserved.
The original five stash tips remain unchanged. No worktree directories, ignored
configuration, private data, dependency caches or backups were removed.

Original reports/PR81_DEPLOYMENT_2026-11-04.md and
reports/POST_ACTIVATION_AUDIT_2026-11-04.md remain untracked original-checkout
evidence; they were read for reconciliation, not copied wholesale into Git.
Recorded post-activation state: supplemental browsing on, strict application/
alert/public eligibility unchanged, zero eligible roles; bounded unverified
discovery is not proof of a closing date. Recorded quota330/512MB and HSTS604800
supersede earlier historical values; no fresh production check was performed here.

## Recoverable branch cleanup

The exact27 tip mappings are in BRANCH_ARCHIVE_2026-11-11.json:
20 local branch tips and7 remote development tips. Local tags were verified before
local deletion. All7 remote tags were pushed and read back before atomic branch
deletion with expected-old-SHA leases. All stale worktrees were clean and detached
at their existing commits; their files remain available. No history was rewritten.

Remote baseline tag: `mvp1-source-20261111-e682cac`.
Remote recovery prefix: `archive/mvp1-20261111/remote/`.
Local recovery prefix: `archive/mvp1-20261111/local/`.
Local-only historical/private histories were not newly published.

An owner/SYSTEM/Administrators-only Git recovery bundle retained all pre-cleanup
refs and full history, including local-only work and stash:
`C:\dev\ajiri\.recovery\mvp1-20261111\ajiri-before-branch-cleanup.bundle`.
Git bundle verify passed; SHA256:
`d110a38a3d89ec84b804d26a5ec48178dd6b08b60432483e937cfea7afa4ece4`.
The bundle is private recovery material and must never be committed or uploaded.

PR71 and73 were closed with archive/carryover notes after their heads were preserved;
their discussions/code/CI history remain intact. Neither was merged. Four active
Dependabot reviews67/82/83/84 and their branches were retained. They are unfinished
dependency work, not stale branches to erase. The temporary planning branch is
removed only after its reviewed documentation is merged.

### Recover or start work (PowerShell)

```powershell
Set-Location C:\dev\ajiri
git fetch origin --prune --tags
# Start implementation from main; choose a new focused branch name.
git switch main
git pull --ff-only
git switch -c codex/mvp2-aj53-inventory
# Inspect preserved reference source without changing this checkout.
git show archive/mvp1-20261111/remote/codex/review-02-application-alert-search
# Recover an old local tip into an explicitly named reference branch if necessary.
git branch codex/recovered-reference archive/mvp1-20261111/local/codex/backend-inactive-20261031
# Independently verify the private bundle before using it for recovery.
git bundle verify C:\dev\ajiri\.recovery\mvp1-20261111\ajiri-before-branch-cleanup.bundle
```

Expected: new feature branch starts at current main; archive references resolve to
manifest SHAs; bundle reports complete history/okay. Recovered reference source is
not automatically safe to merge. In particular, archived jobs.0017 conflicts with
released browsing settings0017; preserve deployed migration history.

## Jira reconciliation and product proposal

The existing34 Done stories were assigned released MVP1 without changing their
Done status. Thirteen unfinished stories were assigned unreleased MVP2 and moved
to the backlog with In Progress preserved. Each received a concrete remaining-gate
comment. No code-only result was upgraded to deployed acceptance. AJ17's obsolete
SMTP summary was reconciled to the approved shared Brevo direction.
AJ53 was linked to discovery epicAJ5, and AJ79 to privacy epicAJ3.

AJ80 and the23 generic Update entries retain their history. No issue was deleted
or renamed to invent provenance. New MVP2 feature suggestions are explicitly
proposals, not implemented behaviour or approved scope commitments.
See docs/MVP2_PROPOSAL.md for current primary-source market benchmarking, suggested
goals, core/conditional scope and target definitions. No sprint was started or
release date invented. The expired active Sprint4 was closed after current board
metrics showed all6remaining issues Done; their membership/history was preserved.
Other dated future sprint plans were retained without changing their dates or
inventing an execution history. Six unfinished epics now read In Progress; AJ7
reads Done because all five defined frontend/API foundation children are Done.

New To Do items: AJ81 dependency readiness, AJ82 inventory quality, AJ83 mobile
matching, AJ84 shortlist/follow-up, AJ85 baseline/recovery readiness and AJ86 pilot/
disclosures. MVP2 contains20backlog items:13carryover stories,AJ80 and6new proposals.

GitHub alert31 reports high-severity follow-redirects GHSA-mrwp-f3q8-3g9p /
CVE-2026-116689, versions1.16.0–1.16.1, patched1.16.2; existing PR82 is retained.
This is a readiness item, not evidence that Ajiri was exploited. The advisory notes
the exact Axios1.20.0 reproduction did not trigger the issue; that is not grounds
to silently dismiss the dependency alert. No lockfile was changed in this closeout.

## Verification and rollback

Pinned Python3.12/Django6.1.2 check and migration-drift checks passed;529backend
tests passed in387.531s with one existing skip and zero socket/DNS/SMTP audit
attempts. Node24.19 locked offline npm ci,lint,155tests/27files (19.54s),and build
(1.35s) passed. All38generated files matched committed frontend_build. Ruff and
reviewed OpenAPI validation passed. Offline npm output is not a current security
scan and does not clear the observed GitHub advisory. Remote CI is pending until
the documentation PR runs. Branch/main ancestry,
tag SHAs, bundle integrity and unchanged stash identities were checked directly.
No deployment, flag change, production migration, live mail, charging, personal
export/erasure or backup retention change occurred.

Rollback for documentation is a reviewed revert PR. Branch cleanup is recoverable
using the tag manifest/bundle; never replace current main with an archived feature
stack, and never restore an old production database for a code-reference recovery.
