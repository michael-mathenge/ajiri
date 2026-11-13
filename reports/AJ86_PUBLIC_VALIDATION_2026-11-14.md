# AJ86 public-form validation loading

Branch codex/mvp2-aj86-deferred-validation from reviewed MVP2/396913c.
The evidence-only PR101 browser job43514052814 failed a real metric gate:
all11 journeys passed, but registration's three-run median TBT251ms exceeded250ms.
Login measured242ms; public transfer496063/498966bytes was also close to500000.
The unchanged runtime9676fc4 had passed its own release-head/merged-main checks
and live verification. The later failure is retained evidence; no budget or CI
workflow is weakened and no metric failure is rerun merely to obtain a green job.

Public forms imported the full shared validation module during initial page load.
The change requests that same module only on explicit submit, preserving the
schemas, fields, privacy agreement and API contracts. The existing synchronous
submit guard spans download/validation/request, the form exposes its busy state,
and a failed download reports a generic accessible error, retains input and requires
an explicit retry. It never starts a mutation without successful validation.

Focused tests cover delayed resolution/duplicate submit, failed download with no
automatic retry or API action, and all field errors after deferred loading.
Existing registration/login/recovery and real browser journeys remain gates.
No production configuration, credentials, sending, user preferences or data change.
No new migration or dependency. Actual commands/results and release evidence must
be recorded before any passing or deployed claim. AJ86's broader genuine consented
pilot/manual mobile/field-performance acceptance remains unfinished.

Actual local frontend verification: explicit Node24.19 locked npmci installed358
packages/audit0. Oxlint/ESLint passed. The first full component run failed its new
busy-state assertion: RHF does not report a validator-module wait for these controlled
unregistered fields. Explicit loader state corrected that behavior. The corrected
full175tests passed20.58s, including delayed load/duplicate submit, generic error/
explicit retry, all field errors and changed-input refusal. Five tooling tests
passed2.787s; Vite built in1.47s. Safe synchronization produced44 committed-build
files; validators are now a separate23.69KB chunk requested on submit.

Real Chromium registration/login/CV approval/private-document/preparation/review
journey passed10.398s. Network assertions proved no validation-module request on
initial registration and a request on explicit submit; real disposable API calls,
private document bytes and no provider/send receipt were verified. No production
or external service was used. Ruff and whitespace checks passed. Linux Lighthouse
metrics and required CI remain unverified until their actual execution; the earlier
251ms failure is not erased by this source change or its functional checks.
System check and migration drift passed; the full backend suite passed591tests
in261.992s with one existing platform skip, including Windows hardlink tests
outside the filesystem restriction. No schema, auth interceptor, JWT cookie or
hosting/CI/budget configuration was changed. All passing claims above correspond
to executed commands, not the separate pending Linux metric gate.
