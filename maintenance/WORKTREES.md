# Checkout housekeeping

Fifteen clean completed checkouts were unregistered on 1 November 2026 after
checking that their source was included in reviewed main. See the bounded inventory
and removal results in `evidence/`. Their source remains recoverable in Git.

The merged/deployed feed checkout was also retired. Keep these unfinished or locally needed checkouts until their purpose is resolved:

| Checkout under `.worktrees/` | Why retained | Next action |
| --- | --- | --- |
| `backend-inactive-20261031` | Broader inactive roadmap, draft PR71 and pinned local runtimes | Review focused stages; do not merge the full reference branch into MVP1. |
| `review-02-release` | Draft PR73, normal application/alert/search acceptance | Finish its bounded review and operational acceptance separately. |
| `job-trust` | Unique source and saved documentation | Reconcile with retained roadmap before removing. |
| `jira-roadmap` | Private ignored configuration and coverage | Michael determines whether configuration is still needed; do not inspect or delete it during generic cleanup. |

The external npm-update checkout is outside this cleanup scope. Existing stashes,
including original-checkout, delivery-concurrency and job-trust work, are preserved.
Stashes are recovery material, not branches to delete.

Nine removed checkouts each left one Windows-locked native dependency file. They
are isolated under `.worktrees/.locked-remnants/`, with no remaining tracked source.
They are reproducible caches, not nine unfinished projects. A shared Node runtime
still owns the DLLs, so it was not terminated during cleanup. After closing the
owning sessions or restarting Windows, inspect this exact directory, verify it still
contains only those cache remnants and delete it using native PowerShell. Do not
delete the enclosing `.worktrees/` folder or use a wildcard cleanup of all checkouts.

For future cleanup, first run:

```powershell
Set-Location C:\dev\ajiri
git worktree list
git status --short
git branch --merged main
git stash list
```

Verify open PR heads and unique commits before deleting a branch. Remove clean
completed checkouts with `git worktree remove <exact-path>` before deleting their
branch. Preserve all open PRs, unfinished stages and unique user work. Main must
only advance through reviewed changes with the required checks.

Branch cleanup removed 99 local and 47 remote stale/duplicate refs. The first
96/46 tips were ancestors of reviewed main; the deployed feed branch was removed
after merge, and two aliases had the exact tip of retained job-trust. Open PRs
65/66/67/71/73, stages 03–06, unique source, backup refs and all five stashes remain.
Six unique historical branches still need reconciliation before deletion: account-email,
launch-prompt-refinements, shared-throttle-cache, sprint-3-evidence and checkpoint-3/3b.
