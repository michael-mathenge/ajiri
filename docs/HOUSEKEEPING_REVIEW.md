# Housekeeping evidence

20 October 2026. Cleanup is limited to verified redundant material and recoverable
tracked changes. It does not authorize deletion of databases, private documents,
backups, environments, stash, Git configuration or uncommitted work in the original
checkout.

- Replaced the stale Checkpoint-1 README/setup instructions with short current
  entry points, the user journey guide and links to operator evidence. Historical
  reviews remain available; their content is not discarded as unused merely
  because it is old. CLAUDE.md is referenced by existing documentation and retained.
- Removed `ajiri-frontend/public/icons.svg` (5,031 bytes), an unused social-icon
  sprite. Repository searches for its filename and fragment references found no
  consumers in source, HTML, public assets, backend or documentation. The active
  favicon remains; its HTML reference was verified. The next generated frontend
  build removes the redundant copied sprite too.
- Added ignores for `.verification/` and `.worktrees/` so local test installations
  and isolated checkouts cannot be accidentally committed. The original Docker
  learning files, lockfile changes and coverage data remain preserved.
- Generated hashed frontend assets are replaced only from a verified build;
  superseded bundles are recoverable in Git. No private backup pruning occurs.
- A Windows-locked native Tailwind binary was left intact. Tests/build are being
  verified in a fresh isolated installation instead of killing unrelated processes
  or forcibly deleting a potentially in-use directory.

No broad “delete all untracked files” or Git clean/reset operation is appropriate
for this workspace. Future candidates require a reference/use check and explicit
identification in this report before removal.
