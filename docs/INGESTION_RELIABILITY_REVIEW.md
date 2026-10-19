# Ingestion failure investigation — 17 October 2026

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

Branch `codex/ingestion-reliability`, based on reviewed CV batch `948eafa`.
Suggested estimate: 2 points. Local change only; no push, merge, deployment,
credential change, workflow dispatch or notification change.

## Verified evidence

- [Scheduled run #36](https://github.com/michael-mathenge/ajiri/actions/runs/39002307699):
  feed download passed; Send the feed to Ajiri failed with curl exit 22 / HTTP 404.
  Its response was PythonAnywhere's “Coming Soon” placeholder page rather than
  Ajiri's JSON API response.
- [Scheduled run #35](https://github.com/michael-mathenge/ajiri/actions/runs/38982100501):
  the same posting step returned the same host placeholder.
- [Manual run #37](https://github.com/michael-mathenge/ajiri/actions/runs/39023366845)
  and [scheduled run #38](https://github.com/michael-mathenge/ajiri/actions/runs/39025797298)
  succeeded later on the same main revision `3309803`. #38 was scheduled at
  13:40 Nairobi on 17 October and completed successfully in 9 seconds.

This identifies a host availability/routing response, not a demonstrated feed
parser defect or invalid-key response. The precise reason the host served its
placeholder (disabled app, routing, expiry or another host condition) is
**UNVERIFIED**. Later success establishes recovery at those run times, not a
guarantee that the host condition cannot recur. No failed run was rerun merely to
clear its red badge. Earlier failures outside the two inspected runs are not
claimed to share this cause.

## Local fix

The workflow checks out its reviewed code with read-only repository permission
and no persisted Git credential. Feed downloading retains bounded retries and
adds a retry-time budget. The job timeout is eight minutes to accommodate download,
readiness checks and the single bounded POST without the old retry budget overrun.

The dependency-free helper validates private configuration without logging it,
then probes `/api/health/` up to three times (10-second timeouts, 5-second waits).
Only HTTP 200 with the exact healthy JSON permits delivery. Persistent 404/HTML or
other unhealthy responses produce a short actionable error before any feed POST.

POST is attempted once, with the existing X-Ingest-Key/XML contract. HTTP 403,
HTTP 404 and uncertain network/server/invalid-response outcomes have distinct safe
messages. No redirects, raw HTML, exception details or secret values are logged.
Success prints only validated nonnegative integer created/skipped/flagged/notified
counters. Backend endpoints, parser, authentication, matching, alerts and schedules
are unchanged. The separate sweep workflow is unchanged; do not infer its health
from this ingestion investigation.

This improves resilience/diagnosis and avoids replaying ambiguous side effects;
it cannot repair an unavailable PythonAnywhere web app. Failures still alert you.

## Verification

- `python -B -m unittest discover -s .github/scripts -p 'test_post_feed.py'`:
  nine tests passed, with mocked network requests only. Cases include persistent
  and transient host failures, successful JSON validation, no uncertain POST replay,
  invalid configuration, secret-free output, 403/404 and redirect refusal.
- Backend `check`: no issues; migration drift check: no changes; full suite:
  202 tests, OK, one existing Windows symlink skip, 134.401 seconds. Real email
  disabled and dotenv disabled; no application backend files changed here.
- Frontend locked install, lint, 59 component tests and production build passed
  on bundled Node 24.19.0. Output matches the reviewed committed frontend_build;
  no frontend source/artifact change is needed for this workflow-only package.
- `git diff --check` passed. Workflow indentation/structure reviewed manually;
  no YAML/actionlint tool is installed, so that validator is **UNVERIFIED**.
- New helper not run against production, and new workflow not run on GitHub:
  **UNVERIFIED until the reviewed batch is merged**. Existing scheduled recovery
  was observed independently; no production repair is claimed from this local fix.

## Activation and operational checks

Held for the batch release. This workflow change takes effect only after review
and merge into the default branch. No PythonAnywhere code deployment, dependency
install or migration is needed for this helper itself. The CV batch separately
requires its reviewed migration before code activation.

After merge, inspect one normal scheduled ingestion run. Expect the helper tests
to pass, readiness to pass, and exactly one POST with the four integer counters.
Do not run local helper code with production secrets to test it.

If host 404s recur:

1. Open PythonAnywhere → Web. Confirm the existing app is enabled, expiry is in
   the future and its configured hostname is the intended Ajiri hostname.
2. Check the public `/api/health/` response and private platform error log. A host
   placeholder is not an instruction to create another app or rotate credentials.
3. Compare the repository's configured base URL privately; never paste secret
   values or environment content into chat or logs.
4. For planned maintenance, pause both ingestion and sweep writers, then resume
   after verification. Use the existing documented backup/deployment procedure.
5. After an uncertain POST, reconcile database/job counters and logs before
   manually dispatching again; a timeout does not prove nothing was processed.

Rollback is a reviewed revert of this workflow/helper pair. The old workflow
replays some POST failures and dumps raw response bodies, so prefer a forward fix.
No database rollback or history rewrite is needed.

## Development continuation

The personal CV builder is reviewed and retained in this local batch. The next
application package should explicitly select an owner-approved CV version, copy
its verified bytes into the application's existing private snapshot, and preserve
separate letter/email review before sending. It must never regenerate or silently
rewrite an approved CV. Real sending and automatic alerts remain separate gates;
neither is enabled by this workflow fix.
