# CV save feedback fix

17 October 2026. Branch `codex/cv-save-feedback`. Suggested estimate: 1 point.

The live CV form submitted successfully, but the server rejected incomplete added
entries. The summary appeared above the long editor and flattened nested errors
into repeated section-level messages. Read-only inspection confirmed this cause;
no production CV fields were changed or submitted by the agent.

The editor now focuses and scrolls to validation errors, preserving section, row
number and field label. Successful saves focus the saved preview. Unsaved values,
revision checks, approval rules and request retry behavior remain unchanged. No
backend behavior, dependencies, migrations, auth or production configuration changed.

## Verification

- Node 24.19.0: locked `npm ci`, lint, 64 component tests across 10 files and build
  passed. The regression covers repeated errors, exact entry/field labels, focus,
  scrolling, retained input and explicit resubmission. Existing preview test checks
  that focus moves to its heading.
- Initial restricted npm install failed with Windows EPERM; normal-permission
  install passed without lockfile changes. A test initially checked focus before
  the second rejected save finished; corrected to await the rendered feedback.
- Backend check: no issues. Migration drift: no changes.
- Full Django suite: 209 tests, OK (one existing Windows symlink skip), 108.858s.
  Initial restricted run produced filesystem errors and was stopped;
  normal-permission rerun passed.
- Committed frontend build regenerated from the verified build, index LF-normalized.
- Live browser testing of this new fix and screen-reader announcement remain
  unverified; the production page retains the previous release.

## Manual verification after a reviewed release

1. Keep any current unsaved edits on the open production page; do not reload it
   merely to inspect this local fix. Complete missing required fields or remove
   unused entries before saving the current draft.
2. In a test CV with two work entries, leave the second Role/Employer empty. Save
   from the bottom of the editor. Expect focus and scroll at the error summary,
   with “Work experience 2” and each missing field named. Values remain intact.
3. Correct the fields and save. Expect focus at “Review revision …”, with exact
   saved preview content. Approval still requires explicit review consent.
4. Try an invalid date pair, a stale revision and a network failure. Expect useful
   visible feedback and no automatic mutation retry or lost input.

Push and deployment are pending review. Roll back the matching frontend build and
source together; this fix has no schema or data rollback requirement.
