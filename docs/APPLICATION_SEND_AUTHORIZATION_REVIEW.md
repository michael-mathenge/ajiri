# P4 design handback

20 October 2026. Branch `codex/application-send-authorization-design`, from reviewed
P3 `9f08327`. Michael approved proceeding to the separately gated P4 design review.
This package changes documentation only. No migration/code/provider/configuration,
push, deployment, DNS or real sending action is included.

Read APPLICATION_SEND_AUTHORIZATION_DESIGN.md for the exact proposal, including:

- separate document approval, one-application authorization and explicit dispatch;
- two additive tables and their field types/defaults/nullability/constraints,
  ownership validation, retry associations, retention and data-preserving rollback;
- SQLite reservation/handoff cutoff, cancellation race semantics, immutable plan,
  safe unknown outcomes and shared accounting without changing account-pilot scope;
- primary-only sending, copies OFF, separate attachment/provider/pilot/privacy gates;
- tests and staged P4a/P4b/P4c implementation, each stopped for review with real
  transport disabled. A design approval is not an application-pilot-send approval.

## Decisions awaiting review

| Choice | Proposed default | Approval status |
|---|---|---|
| Authorization wording/purpose | Explicit per job/package/recipient; distinct Send button | Pending |
| Lifetime | 24 hours; changes require a new plan and authorization | Pending |
| Schema | Authorization plus attempt-link tables, no backfill; PROTECT evidence | Pending migration design review |
| Withdrawal cutoff | Atomic dispatch handoff; no promise of recall afterward | Pending |
| Retries | One explicit retry after a definite failure; none after unknown/accepted | Pending |
| Copies | OFF; no CC/BCC or copy-role schema in first implementation | Pending |
| Attachments | Exactly two saved DOCX, 2 MiB each / 4 MiB raw total | Pending separate attachment-policy approval |
| Pilot application cap | One attempt per Nairobi day within existing shared five-message cap | Pending; activation not included |
| Provider payload ceiling | Verify current official limit and approve conservative ceiling | Unverified; activation blocker |
| Changed destination | Fail closed; no silent retarget or arbitrary-recipient editor | Pending limited-scope decision |
| Broad launch | Secure suppression/events, consent and privacy review first | Not approved |

No proposed default is described as an existing user choice. Certificate/alert
defaults and broad employer/alert delivery remain separate backlog decisions.

## Verification commands

Read-only corroboration: jobs/models.py, jobs/application_packages.py,
jobs/package_review.py, jobs/delivery_service.py, jobs/brevo_transport.py,
accounts/pilot.py, OWNER_EMAIL_PILOT.md and APPLICATION_ALERT_SENDING_DESIGN.md.
No current provider or production claim is inferred from these local files.

Required repository gates were run for this documentation package, using existing
Python 3.12 and explicit Node v24.19.0, with environment-only DEBUG=True,
PYTHON_DOTENV_DISABLED=1 and REAL_EMAIL_ENABLED=False:

```powershell
$python = 'C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend\.venv\Scripts\python.exe'
$node = 'C:\Users\micha\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$npm = 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js'
$env:PATH = (Split-Path $node) + ';' + $env:PATH
# From this worktree's ajiri-backend:
& $python manage.py check
& $python manage.py makemigrations --check --dry-run
& $python manage.py test --noinput --failfast
# From this worktree's ajiri-frontend:
& $node --version
& $node $npm ci
& $node $npm run lint
& $node $npm run test -- --run
& $node $npm run build
```

Actual results and generated-build comparison are appended after completion.
No new runtime behavior is claimed or tested as implemented; future P4 tests above
remain proposed. Existing suite results verify the unchanged implementation only.

## Handback and next boundary

Suggested design slice: **2 points**, within P4's originally suggested 5-point
package; implementation should be re-estimated after this review rather than
pretending schema/consent/provider work is included in two points. Jira-ready:
**Review exact application send authorization and ledger design | AC: consent,
schema, withdrawal cutoff, immutable plan, limits, retry/unknown behavior and
data-preserving rollback documented; implementation and activation remain gated.**

Next requested decision is approval/amendment of this exact design. If approved,
start **P4a additive schema and migration tests only**, disabled real sending, then
stop for its review. Do not start P4b/c or P5 from that schema-only approval.

## Final results — 20 October 2026

- Backend check: no issues. Migration drift: no changes. Full existing suite:
  **247 tests run in 143.398 seconds, OK with one existing Windows symlink skip**.
- Node **v24.19.0**, npm ci: 180 packages installed / 181 audited, zero reported
  vulnerabilities. Lint passed without warnings; Vitest **86 passed across 14 files
  in 14.28 seconds**; build passed in 1.28 seconds.
- All **21 generated files match** the committed P3 frontend_build after normalizing
  index.html line endings. No generated files or frontend/runtime code changed.
- No new tests were added for unimplemented proposals. No ordinary development or
  production database was migrated, no provider limits/production state were
  inspected, and no email was sent. The original checkout/Docker lesson remain intact.
- Final diff is documentation only; git diff --check passed. Before commit the branch
  is checked; the non-empty 9f08327..HEAD author/committer range is verified against
  the configured noreply identity at handback. No push or deployment.
