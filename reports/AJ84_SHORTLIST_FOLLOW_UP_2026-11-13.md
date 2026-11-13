# AJ84 private shortlist and personal follow-up

Branch `codex/mvp2-aj84-saved-jobs` starts from reviewed MVP2
e31ef172a2d83243242a9a906712862a658ec7a5 (PR97).

## Resulting behaviour

Candidates can save a visible role from its detail page and manage a private,
paginated Saved jobs list. Idempotent PUT and unique(owner, job) keep one reference
and its original save time across a retry, including after the role expires.
Removing a reference affects only that owner; repeated DELETE is harmless.
New saves still require visibility under the existing browse rules. A saved
supplemental reference remains explicitly unverified and cannot enter preparation,
alerts or saved-search matches through saving. An expired owned reference remains
labelled Reference only; its validated source link is separate from current-job
preparation. Saving never creates an Application or contacts an employer.

Personal follow-up extends AJ50's existing stage/note/revision editor. The optional
local picker becomes an explicit timestamp and is displayed in My applications.
It is a manual planning aid, not an email/device reminder service or employer
outcome. A blank submitted picker explicitly clears the date; omission by older
clients preserves it. Dates retain the same optimistic owner boundary and cannot
clear an unknown provider receipt, change sending authority or alter approved
CV/letter bytes. Existing email/external-link actions and receipt wording remain.

Private export includes owned saved references and job context, with follow-up
dates included in existing application records. Verified-request erasure removes
only the owner's private choices/applications while preserving shared roles and
other owners' dates/references. Prepared signed-journal requirements remain intact.
No real account was erased, exported or assigned a planning date.

## Migration and release order

jobs.0021_saved_jobs_and_follow_up adds SavedJob and a nullable Application date.
No old migration, auth/cookie/interceptor/CORS, ingestion/key endpoint, CI or hosting
setting changed. Disposable forward/reverse rehearsal retains old application
notes/document paths, shared job metadata and all three SQLite search triggers.
The actual document regression also updates a personal date and confirms unchanged
approved CV/letter bytes and hashes. Production order remains private backup,
off-server integrity/isolated restore, paused writers/web, reviewed additive
migrations, preservation checks, then activation. Keep schema additions/new writes
on code rollback; do not routinely restore old data or reverse personal records.

## Executed checks

- Initial focused11 API/date tests passed4.336s. Expanded14 API/schema/privacy
  tests passed9.540s, covering owner isolation, idempotence, expiry, unverified
  references, legacy omission/clear, uncertain receipts and export/erasure.
- Complete backend suite:591 tests passed286.935s; one existing platform skip.
  Local interpreter is the available Python3.13.17 test environment; required CI
  still verifies the production3.12 version alongside3.13/3.14 before merge.
- Check, migration drift and Ruff0.17.4 across backend/scripts passed. Initial
  OpenAPI generation rejected the raw empty-body schema annotation. Reading the
  installed generator showed it expects a media-type mapping; corrected that
  annotation and strict generation/comparison passed without warning suppression.
- Node24.19 locked npm ci installed358 packages with zero audit vulnerabilities.
  Oxlint/ESLint passed; focused initial8 UI tests passed6.64s. Final full171
  components/30 files passed27.34s after a small success-state reset correction
  before local date validation. An earlier full171 run31.86s also passed.
- Five tooling tests passed3.992s. Final Vite build passed2.34s; safe synchronization
  verified all old files against HEAD and copied42 generated files. Unexpected
  generated files would stop synchronization rather than be discarded.
- Actual isolated Chromium employer/review/filter/dismissal/save/remove/focus and
  personal-date/save/reload journeys: two tests passed21.978s. They verified real
  destination headings, current source links, keyboard focus after removal and
  preserved application status/receipts, with provider mocked and uncalled.
  These are disposable acceptance journeys, not manual Android/iOS pilot evidence.
- `git diff --check` passed. Source and generated build are separate commits,
  generated build last. No secrets, environment files or personal records included.

## Pending production acceptance

This package has not yet been activated. Exact-head checks, release PR, a fresh
private recovery gate and production migration/read/asset verification remain.
Runtime remains93cf55e. Employer participation, original vacancy inventory and
consented-person MVP2 pilot gates are separate unfinished work, not proof supplied
by synthetic tests. Server recovery capacity must be remeasured for this release;
only the two previously named archive deletions were authorized, not future pruning.
