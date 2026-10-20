# P4b application authorization and mocked dispatch review

20 October 2026. Branch `codex/application-send-workflow`, based on P4a `d6b7b1e`.
Michael approved completing P4b, P4c and P5 readiness as one local batch with final
review. This supersedes intermediate stop instructions in historical P4 notes.
Recorded production is `894d1eb`; it was not inspected or changed in this batch.

## Behavior

- Private owner-only no-store send-plan, authorization create/lookup/history/detail,
  withdrawal and dispatch-reconciliation APIs. Strict types/unknown-field rejection.
  GET/HEAD never create authorizations, quotas, files or messages.
- Exact bounded versioned plan: current owner/name, latest document proof/package,
  current unchanged job/destination, verified Reply-To, configured From, exact email
  text and two saved verified DOCX byte hashes/sizes/ASCII filenames. Copies off.
  Missing sender configuration blocks preview; no placeholder sender is selected.
- Explicit unchecked consent is required by API and service; authorization lasts
  24 hours. Same owned request key/binding returns its historical record before
  fresh eligibility checks. Changed binding conflicts; another owner's key is404.
  GET derives expiry; creation closes expired evidence before allowing replacement.
- New saves supersede active authorizations atomically. Withdrawal is idempotent
  until the committed dispatch handoff; after it, cancellation is not promised.
- Direct application DeliveryService calls now require exact authorization identity.
  Full payload/current proof/files/name/mailbox/job revalidation occurs before and
  inside reservation. Shared transaction reserves budgets, creates receipt/link and
  closes permission; rollback leaves no partial budget or cutoff. Network stays
  outside transactions. Receipt-only retries preserve the earlier concurrency fix.
- One explicit retry of the initial definite failure; no chain/fork, unknown retry,
  quota refund, copy or accepted resend. Existing account and alert policy unchanged.
- Separate injectable application-pilot boundary, exact owner/actual recipient,
  synthetic subject, exactly two attachments,2MiB each/4MiB raw, nonzero reviewed
  serialized ceiling, one application/Nairobi day and five total shared messages.
  No live factory exists and the endpoint remains disconnected even if global or
  application flags are set. Tests use fake transport only. No credentials read.

## Gates and evidence

Commands/environment match APPLICATION_SEND_SCHEMA_REVIEW.md, using Python3.12,
PYTHON_DOTENV_DISABLED=1, DEBUG=True, REAL_EMAIL_ENABLED=False and explicit
Node24.19.0. Actual results are recorded below after completion.

Final backend gates: `manage.py check` no issues;
`manage.py makemigrations --check --dry-run` no changes;
`manage.py test --noinput` **275 tests in156.140s, OK, one existing Windows
symlink skip**. This includes the added save/dispatch cutoff and concurrent name
change regressions. Expected synthetic failure-path logs are not live failures.

Focused `manage.py test jobs.test_delivery_service jobs.test_send_authorization
--noinput`:40 passed in16.789s before adding three cutoff/name regressions.
Initial fixture replay errors were fixed by refreshing the authorization fixture
state; unsafe-name normalization now collapses redundant underscores. Core replay
and owner conflict are explicitly tested; no failed run is counted as passing.

Node24.19: `npm ci`180 installed/181 audited, zero reported vulnerabilities;
`npm run lint` passed; `npm test -- --run`86 tests/14 files passed in21.04s;
`npm run build` passed in4.41s. All21 generated files match committed frontend_build
after index.html CRLF normalization. No frontend source/assets changed in P4b.

No new dependency or migration. Historical migrations, auth/CORS, ingestion, CI,
hosting, original checkout/Docker files, stash/config and existing coverage preserved.
Only disposable test databases were migrated. Windows-only verification does not
claim Linux or Python3.13/3.14 results; existing Windows symlink skip is recorded.

## Remaining manual/release checks

P4c adds the UI without sending. P5 supplies the supervised runbook/readiness report;
no real pilot is performed in this batch. Provider size/terms, verified sender,
owner allowlist and manual bounce/complaint review must be freshly established at
activation. Broader sending, copies, suppression/webhooks, certificates and alert
consent/defaults stay outside this local package. AJ-25 retention/erasure remains
unresolved; protected evidence can block deletion. Filesystem/network operations
cannot be atomic with SQL after the handoff.

Rollback to a reviewed email-disabled server/client pair while retaining populated
tables, private documents, receipts/links and newer writes. Do not reverse jobs0009/
0010, delete receipts to retry, or restore an old DB over newer writes. Exact later
server procedure is in APPLICATION_OWNER_PILOT_RUNBOOK.md (P5).

Suggested5 points, AJ-17 slice. Jira-ready title/acceptance:
**Bind application dispatch to exact revocable authorization | AC: private plan,
explicit24h permission, atomic withdrawal/dispatch cutoff, exact saved bytes,
one explicit retry, shared budgets/replay safety, fake-only tests and disabled
production endpoint pass all gates.**
