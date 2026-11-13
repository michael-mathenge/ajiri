# AJ83 normalized mobile vacancy filters

Package branch `codex/mvp2-aj83-discovery` starts from reviewed MVP2 e3682bf and
was advanced without losing feature work to checked documentation merge c6ae61e.
This extends the already deployed skill explanation rather than rebuilding it.

## Behaviour

Employers can explicitly supply one of Kenya's47 counties, remote/on-site/hybrid
work arrangement and minimum whole years of experience. Missing facts remain null;
the existing location/prose is never mined for inferred requirements. Independent
staff see these facts during review, then publication copies the same facts.
Submission retry keys distinguish changed metadata from a replay of one decision.

Job list and detail expose the facts and honest unknown labels. Mobile search
keeps the new controls under More job filters, with the existing clear/back/URL
behaviour. A maximum required-experience value0 means explicitly no prior
experience required; absent requirements are excluded only when a bound is chosen.
County/work filters also require explicitly matching facts. No filter uses protected
traits or changes70% skill-alert rules, freshness or preparation eligibility.

Save this search preserves all selected filters, including0. Owner-scoped saved
preferences, revision conflicts and due-window matching retain that same intent.
Clearing stores null; saving never grants consent or activates email. Legacy saved
queries keep their original behaviour. Existing channel settings are not changed.

The shared vocabulary lives in backend jobs/vacancy_metadata.json and is bundled
by Vite into the frontend; it has no metadata network dependency. Official county
reference: https://kdsp.devolution.go.ke/counties. The0–80 whole-year validation
bound is a technical input limit, not an age or employment eligibility rule.
Concept and user guide explain zero/unknown/filter semantics.

## Migration and rollback

Additive jobs.0019_normalized_vacancy_filters depends on deployed0018 and adds
nine nullable fields across Job, EmployerJobDraft and SavedSearch. No historical
migration, auth/refresh/interceptor/CORS, ingestion/key handling, CI or hosting
configuration changed. Disposable forward/reverse tests preserved old job prose,
draft/job relationships, saved queries and all three SQLite FTS triggers/searches.
Production activation requires a current consistent private recovery gate, paused
writers/web, migration then activation and preservation verification. Keep additive
columns and new writes on code rollback; do not restore old data routinely.

## Executed validation

- `manage.py check` and `makemigrations --check --dry-run`: passed.
- `manage.py test jobs.test_vacancy_filters jobs.test_original_source --noinput`:
  19 passed2.701s, including low-score browsing, explicit zero, invalid values,
  unknown legacy facts, independent review and intent replay.
- New filter/schema rehearsal:10 passed5.499s, including disposable forward/reverse.
- Complete `manage.py test --noinput`:565 passed291.252s; one existing platform skip.
  Run outside the Windows hard-link sandbox restriction identified in the preceding
  evidence package; no implementation/test workaround was introduced.
- Ruff0.17.4 across backend/scripts and strict generated OpenAPI comparison: passed.
- Node24.19 locked `npm ci`:358 installed, zero audit vulnerabilities. Oxlint and
  ESLint passed. Focused16 components passed9.45s; full164/28 files passed37.22s.
- Five real tooling tests passed4.207s. Vite production build passed2.37s.
  Safe generated-build synchronization checked all prior files against HEAD and
  preserved unexpected files by failing closed; new build contains39 files.
- Initial local browser invocation failed before running a journey because the
  optional Playwright module was absent. Installed the repository-pinned1.64.1
  runner and its official Chromium headless shell only in ignored local tooling,
  without removing existing browser installations. Production dependencies did
  not change.
- Actual Chromium employer/review/mobile-filter journey then passed12.581s against
  a disposable DB and built React app: accepted/lost-response replay, one draft,
  independent review, exact source/official link, explicit0-year label, collapsed
  mobile filters, selected query, saved-form prefill, accessibility and withdrawal.
  Provider calls remained mocked and uncalled. This is not a manual phone/pilot test.

## Acceptance limits

This package is not production activation or completion of AJ83. Owner-controlled
recommendation dismissal remains a later slice, and8/10 consented participants
finding a genuinely current relevant role within5 minutes remains unverified.
The live source still has no genuine eligible inventory, and no vacancy, employer,
staff access, email consent or participant was fabricated for production.
