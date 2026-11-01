# Checkout housekeeping

Fourteen clean completed checkouts were unregistered on 1 November 2026 after
checking that their source was included in reviewed main. See the bounded inventory
and removal results in `evidence/`. Their source remains recoverable in Git.

Keep these unfinished or locally needed checkouts until their purpose is resolved:

| Checkout under `.worktrees/` | Why retained | Next action |
| --- | --- | --- |
| `backend-inactive-20261031` | Broader inactive roadmap, draft PR71 and pinned local runtimes | Review focused stages; do not merge the full reference branch into MVP1. |
| `review-02-release` | Draft PR73, normal application/alert/search acceptance | Finish its bounded review and operational acceptance separately. |
| `job-trust` | Unique source and saved documentation | Reconcile with retained roadmap before removing. |
| `jira-roadmap` | Private ignored configuration and coverage | Michael determines whether configuration is still needed; do not inspect or delete it during generic cleanup. |
| `job-feed-display` | Current release package | Remove only after merge/deployment, a clean checkout and preservation of any local evidence. |

The external npm-update checkout is outside this cleanup scope. Existing stashes,
including original-checkout, delivery-concurrency and job-trust work, are preserved.
Stashes are recovery material, not branches to delete.

Eight removed checkouts each left one Windows-locked native dependency file. They
are isolated under `.worktrees/.locked-remnants/`, with no remaining tracked source.
They are reproducible caches, not eight unfinished projects. A shared Node runtime
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
