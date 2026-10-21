# Page reads and cache safety (AJ-32)

The jobs, job detail, profile, CV builder, applications and notifications pages use
TanStack Query through `useApiQuery`. This replaces the custom effect-based fetch
hook. Concurrent readers of the same API path share a request; each filter/page URL
has a separate key. Axios consumes the query's abort signal so late results cannot
replace a newer filter.

The cache stays in memory, never local storage or an offline cache. Data is fresh
for 30 seconds; inactive entries expire after five minutes. Successful profile,
CV, application and preference writes invalidate page reads. Background refresh
does not reset local unsaved form state or authorize any action. On-demand document
review/authorization reconciliation still performs explicit fresh reads.

Login/logout and cross-tab account storage changes discard the query client and
its cached private data. Query keys contain API paths, never access tokens. The
existing JWT cookie/rotation/interceptor implementation is unchanged. Server-side
ownership, revision and authorization checks remain authoritative.

Read retries are limited to one retry for network or server errors. Validation,
authentication, permission and rate-limit failures are not retried. Window focus
does not trigger another request. Mutations remain explicit existing actions with
no automatic retries; a query cache is never evidence of a successful send.

## Development

Use the locked installation and Node 24.19 from SETUP.md, then run:

```powershell
cd C:\dev\ajiri\ajiri-frontend
npm ci
npm run lint
npm run lint:eslint
npm run test -- --run
npm run build
```

`query-data.test.jsx` covers deduplication, cache reuse/invalidation, obsolete
request cancellation, bounded retries, same/cross-tab isolation and changed skill
matches after a successful save. Component tests create independent query clients
so one test's private synthetic cache cannot affect another.

Rollback is a source/client-build rollback; no database migration or data rewrite
is involved. Do not persist this private cache when adding offline/PWA features.
