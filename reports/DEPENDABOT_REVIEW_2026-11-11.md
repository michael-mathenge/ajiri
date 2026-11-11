# Dependabot review — 11 November 2026

Baseline: reviewed main b1699915608f55129ab088ee3096155f940ef4d4.
The current task authorizes resolving the four remote dependency branches. This
package consolidates compatible changes from82/83/84;67 is deliberately rejected
for the selected Celery graph. No production deployment or flag activation is
included. Existing accounts, privacy, freshness and one-handoff controls remain.

## What the four PRs do

| PR | Purpose | Disposition and reason |
|---|---|---|
| [67](https://github.com/michael-mathenge/ajiri/pull/67) | python-dateutil2.9.0.post0 ->3.0.0; upstream timezone implementation/database changes | Closed as incompatible with the selected Celery5.7.0 graph. Retain2.9.0.post0; reconsider when a supported Celery graph permits3.0.0. |
| [82](https://github.com/michael-mathenge/ajiri/pull/82) | Lock follow-redirects1.16.2, fixing the high cross-realm sensitive-header redirect advisory | Preserve this exact security patch while consolidating83; close as superseded only after the replacement PR merges. |
| [83](https://github.com/michael-mathenge/ajiri/pull/83) | Frontend runtime/build/test updates: Axios1.21,React Query5.106.1,Router7.18.5,forms/icons,Vite8.3.6,Vitest5.1,lint tooling | Consolidate with82,run locked install/lint/tests and regenerate committed frontend_build last. Close only after replacement acceptance. |
| [84](https://github.com/michael-mathenge/ajiri/pull/84) |15Python pin updates, including Django6.1.3,Celery5.7,Kombu5.7,timezone packages and development tools | Install the actual combined pins in a fresh local virtualenv,pip check,and full suites/CI. Close only after replacement acceptance. |

All original tips were archived remotely and verified before closures. Exact SHAs
and branch names: [archive manifest](DEPENDABOT_ARCHIVE_2026-11-11.json), tag prefix
`archive/dependabot-20261111/pr-`. No original published history was rewritten.
Public unauthenticated GitHub API requests hit a rate limit; local fetched Git refs
and the existing authenticated browser provide review/CI/closure evidence. No
credentials or alternate authentication material were extracted.

## Compatibility finding: why67 cannot compose with84

A clean Python3.12 pip resolution of the requested combined pins failed:
`celery5.7.0 depends on python-dateutil==2.9.0.post0` conflicts with3.0.0.
The installed Celery5.7.0 distribution METADATA independently confirmed that exact
Requires-Dist constraint. A successful historical check of67 on an older base does
not establish compatibility with84. No --no-deps, fake package, relaxed constraint
or forced installation was used. Retaining the required2.9.0.post0 pin resolved the
graph; the complete quality/schema/browser requirements installed and pip check
reported no broken requirements.

The selected runtime pin changes are amqp5.4.2,asgiref3.13.0,billiard4.3.2,
Celery5.7.0,Django6.1.3,Kombu5.7.0,sqlparse0.6.1,tzdata2026.6,tzlocal5.4.5 and
wcwidth0.9.4. Development changes are DRF stubs3.18.2,Playwright1.64.1,
coverage7.17.2,Ruff0.17.4 and mypy2.4.1. Other runtime pins, including dateutil,
remain compatible with the original supported constraints.

## Security and residual findings

[GHSA-mrwp-f3q8-3g9p](https://github.com/advisories/GHSA-mrwp-f3q8-3g9p)
affects follow-redirects1.16.0–1.16.1 and is patched in1.16.2. The consolidated
lock retains82's complete version/resolved/integrity entry rather than reverting
to83's older transitive version. npm ci successfully installed the graph.
No claim that Ajiri was exploited is made.

Fresh online npm audit after the update reported0high/critical and3moderate affected
nodes. Production-only npm audit (--omit=dev) reported0findings. The moderate
chain is development-only eslint -> @eslint/config-array -> minimatch10.2.6,
root advisory [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249).
The current config-array constraint is minimatch^10.2.4,while the published fix
starts11.0.1. Its separate glob subtree already resolves patched11.0.5.
Do not claim the full audit is clean. No automatic major override,ESLint downgrade
or audit --force was applied. Follow-up [AJ87](https://michaelmathenge.atlassian.net/browse/AJ-87)
is in MVP2 for an upstream-compatible fix or separately reviewed migration.

## Validation

The exact updated pins were installed into a separate Python3.12 virtualenv;
the old parity environment and production virtualenv were preserved. Django check
and migration drift passed. Ruff0.17.4 and reviewed OpenAPI generation passed.
Full529backend tests passed in323.847s with one existing platform skip;the audit
hook recorded zero socket/DNS/SMTP attempts. Actual test versions were Django6.1.3,
Celery5.7.0,dateutil2.9.0.post0 and tzdata2026.6. Sixteen repository helper tests
passed in0.498s. Updated mypy executed successfully but reported309nonblocking
legacy findings;this is not a clean type check.

Node24.19 locked npm ci,Oxlint,ESLint,155component tests/27files (18.63s),the
quality helper test (2.66s) and Vite8.3.6 build (1.43s) passed. Application sources,
auth interceptor,cookie logic,CORS,ingestion handlers,migrations and CI workflows
were not edited. The generated build must be the final frontend package commit.
The replacement PR must pass all six required checks before merge/closure.

The old83frontend failure was inspected directly in
[job129018319632](https://github.com/michael-mathenge/ajiri/actions/runs/42574260173/job/129018319632):
the clean build produced new asset hashes,but committed frontend_build still had
the old bundles. The job explicitly reported frontend_build out of date. This is
resolved by committing the newly generated matching build,not by changing CI.

## Rollback and deployment boundary

Repository rollback is a reviewed revert restoring the prior dependency manifests,
lockfile and matching committed frontend assets together. Preserve newer user data,
receipts and schema; this package adds no migration. Do not restore an old database
or reinstall development/CI tools into the production virtualenv.

Any later production deployment requires fresh quota/backup/off-server isolated
restore evidence,reviewed exact source/runtime pins and the existing ordered
preflight. Do not infer production Django6.1.3 from a Git merge or local tests.
Existing hosted service/flag states and ambiguous-provider protections stay under
their current acceptance rules; the Celery package upgrade does not start a worker.
