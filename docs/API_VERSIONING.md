# API contract and compatibility

AJ-34 introduces additive `/api/v1/` aliases for the existing account, profile,
job, application and notification endpoints plus health. They use the exact
legacy view classes: owner checks, CSRF, throttles, serializers and sending gates
are shared. Existing `/api/` paths remain supported with no removal deadline.
The current client continues using those paths. Migrate consumers explicitly
and test them before considering a future announced deprecation. Breaking
contracts require a new version; do not silently change version-one semantics.

Operational ingestion/sweep remain only at their existing paths. Their key
handling and workflows are unchanged. No new runtime dependency is needed.
The server publishes the reviewed static source contract at `/api/schema/`,
without inspecting production data or fetching third-party documentation assets.
No Swagger try-it-out interface or new access grant is introduced.

The OpenAPI generator is pinned to drf-spectacular0.30.0 in the separate optional
`ajiri-backend/requirements-schema.txt`. Use synthetic/local settings only:

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:DEBUG = 'True'
$env:PYTHON_DOTENV_DISABLED = '1'
$env:REAL_EMAIL_ENABLED = 'False'
python -m pip install -r requirements-schema.txt
python manage.py spectacular --settings=config.schema_settings --format openapi-json --file config/openapi.json --validate --fail-on-warn
```

Schema-specific settings/annotations do not change the normal authentication
implementation. Cookie refresh remains httpOnly with CSRF and same-origin Origin
checks; no JSON refresh token is accepted or returned. Existing cookie path `/`
works across old and versioned aliases. Documentation does not override guards.
Some existing custom response objects are explicitly extensible rather than
exhaustively typed; do not generate strict clients that reject unknown fields.
File responses are binary, including genuine uploaded formats. Provider acceptance
is not inbox delivery, and preparation/review never send an application.

Approved CI addition (21 October 2026): install the pinned schema requirements
in the existing quality job, generate JSON with validation and fail-on-warn, then
compare it byte-for-byte with the reviewed file. Keep all six check names and
production credentials unchanged. Generated schema contains source contracts only.

Rollback removes aliases/schema publication and retains the legacy routes, data
and configuration. No migration reversal is required. Before deployment verify
legacy and versioned health, authenticated owner reads and schema JSON.
