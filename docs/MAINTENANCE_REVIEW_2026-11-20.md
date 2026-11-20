# Framework, security and operations review -20November2026

## Evidence and scope

Production remains last verified e3e8f74; today's development does not establish
activation. PythonAnywhere and Ajiri HTTPS requests time out from this workstation
while GitHub returns200. No production web/writer pause, reset or cleanup occurred.
A worldwide provider incident is not confirmed. Unattended API setup is pending.

Local housekeeping removed four newly created labelled/no-host-mount PostgreSQL
retry containers. Exactly10863830bytes of four regenerated source contexts were
removed after their manifests and every backend hash were verified; exact manifests,
Dockerfiles/lab scripts and failure/success receipts remain in private verification
records. Existing Docker lessons/resources, root user files, five Git stashes and
all private recovery copies remain. No production backup retention is authorized.

## Recent releases and applicability

- Django6.1.3 (3November): six security fixes including base64 upload memory limits,
  private-cache Vary distinctions, admin hash exposure and GeoDjango SSRF/logging.
  The runtime requirements already pin6.1.3; the currently loaded production package
  version must be measured, not inferred from a repository pin. No Django6.1.4
  pre-release should be deployed as a security fix.
- React19.3 (9September): stable ViewTransition and Fragment refs, browser() and
  Trusted Types support. Ajiri already locks19.3.1; no SSR/RSC redesign is needed.
  Existing mobile accessibility/performance goals take priority over animation.
- Vite8.3.8 (11November): upgrade from8.3.6. GHSA-p4f5-76q4-ffq7 was disclosed
  10November;8.3.7 fixed development-server arbitrary code execution for exposed
  dev servers.8.3.8 includes that patch and subsequent fixes. Production serves
  committed static assets, not a Vite development server. Keep development local.
- Axios1.21.1 (9November): raises follow-redirects minimum to1.16.2 for
  CVE-2026-116689, affecting the Node HTTP adapter. Ajiri already locked the patched
  transitive1.16.2 and uses Axios in its browser app; the direct update prevents a
  future resolution below the secure dependency floor. Interceptor code is unchanged.
- PostgreSQL17.12 (12November): security and correctness fixes, including native
  text-search functions and index/incremental-backup issues. The candidate uses
 17.12; existing17.x operators must review reindex/full-backup instructions.

The locked frontend npm advisory query returned zero findings. That did not surface
Vite's upstream advisory, so it is not a comprehensive security clearance.
The local Python environment does not contain pip-audit; no complete current Python
advisory audit is claimed. A separate query of public PyPI version metadata for
all33 declared production pins returned zero published findings and no lookup
failures; this excludes undeclared/environment/OS dependencies. Source release
notes were also reviewed.

## Deprecated patterns to avoid or schedule

Django6.1 introduces MAILERS and deprecates EMAIL_BACKEND/related EMAIL_* settings
and get_connection() toward Django2028. Ajiri still uses the compatibility setting;
its settings.py comment that MAILERS is not a real setting is historical and stale.
Schedule a focused captured-mail migration with existing consent/receipt gates; do
not change delivery configuration during a dependency patch or enable any transport.

Vite8 deprecates esbuild/optimizeDeps.esbuildOptions in favor of oxc and
optimizeDeps.rolldownOptions. Ajiri's inspected Vite config uses neither old option
and already uses ESM. Legacy DEFAULT_FILE_STORAGE/STATICFILES_STORAGE configuration
should use STORAGES; neither legacy setting was found in inspected runtime settings.
Do not introduce public storage URLs or .path assumptions for private documents.

Do not replace Python cascading deletes with Django6.1 DB_CASCADE for private
files: database cascades do not emit Django pre/post-delete signals, while Ajiri's
identity-bound file cleanup depends on its signals and transaction callbacks.

## Specific recommendations

1. Keep Celery5.7/Redis and the existing durable outbox; use the official Celery
   task acknowledgement/idempotency guidance. A different queue would not remove
   receipt reconciliation, unknown outcomes or host-durability requirements.
2. Keep psycopg3.3.6 and Moto5.2.5/boto3 in their labs for now. Select a real private
   storage provider before adding django-storages[s3] to runtime. Its STORAGES
   integration still needs Ajiri's exact-version reads/deletes and no-public-URL
   boundary; installing an adapter alone does not meet those requirements.
3. Add pip-audit as an isolated development/security tool in a checked follow-up,
   alongside npm audit and upstream advisories. Propose any CI-workflow change to
   Michael; do not silently change required checks. Never use automatic --fix
   across this production dependency graph.
4. Reuse Playwright, axe-core and existing component tests for owner isolation,
   private downloads, expiry and phone/accessibility journeys. No new test framework
   is necessary for this release.
5. Use the PythonAnywhere token API and Windows Credential Manager for remote
   administration. This avoids foreground browser input while retaining private
   token entry; it does not add an application diagnostic endpoint or paid service.

## Enable browser-free administration

1. Privately open PythonAnywhere Account > API token and create/copy the token.
2. Open Windows Credential Manager > Windows Credentials > Add a generic credential.
   Target: Ajiri/PythonAnywhere; username: Mathenge; password: the API token.
   Never paste it into chat, a repository file, a command argument or a transcript.
3. Open the existing PythonAnywhere Bash console once; API console creation alone
   does not start a shell. It can then remain in a background tab.
4. The operator must read that credential only in memory and uses the fixed official
   HTTPS host for console commands, private recovery downloads and web reload.
   Verify authenticated read access before any writer pause. Never blindly retry
   an uncertain command; inspect its receipt first. Revoke the token from Account
   when no longer needed; its permission scope is broad.

If connectivity, API authentication, required checks, capacity or independently
verified private restoration is unavailable, hold activation and retain writers.
No browser focus workaround can safely substitute for those release prerequisites.

## Official references

- https://docs.djangoproject.com/en/6.1/releases/6.1.3/
- https://docs.djangoproject.com/en/6.1/howto/mailers-migration/
- https://docs.djangoproject.com/en/6.1/releases/6.1/
- https://react.dev/blog/2026/09/09/react-19-3
- https://react.dev/blog/2025/12/11/denial-of-service-and-source-code-exposure-in-react-server-components
- https://github.com/vitejs/vite/security/advisories/GHSA-p4f5-76q4-ffq7
- https://github.com/vitejs/vite/releases/tag/v8.3.8
- https://vite.dev/guide/migration.html
- https://github.com/axios/axios/releases/tag/v1.21.1
- https://www.postgresql.org/docs/17/release-17-12.html
- https://docs.celeryq.dev/en/stable/userguide/tasks.html
- https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
- https://pypi.org/project/pip-audit/
- https://help.pythonanywhere.com/pages/API/
- https://help.pythonanywhere.com/pages/GettingYourAPIToken/

## Local patch verification

Node24.19.0 locked install/lint/build1.23s passed;177 component tests passed across
30files in23.10s. Backend check/migration drift and690tests in335.268s passed
(one existing platform skip); Ruff/OpenAPI, ESLint and five quality helpers passed.
The resulting lock has Vite8.3.8/Rolldown1.2.19, Axios1.21.1 and
follow-redirects1.16.2. Generated frontend assets are committed last in this package.
Exact-head CI and release/production verification are separate, pending evidence.
