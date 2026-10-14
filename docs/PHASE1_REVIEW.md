# Phase 1 review

## 1. What changed

- `ajiri-frontend/src/index.css`, `index.html`, `package*.json`, `vite.config.js`: semantic light/dark tokens, Tailwind 4, system fonts, Radix primitives and lucide icons. JSX only.
- `src/components`, `src/hooks`, `src/lib`: reusable controls, dialogs, toasts, states, pagination, match/status badges; responsive app shell; protected routes; cancellable resource reads; formatting helpers.
- `src/pages/Login.jsx`, `JobList.jsx`, `JobDetail.jsx`: redesigned login, API-backed filters and pagination, match explanation, clear prepare/review application action.
- Applications and Notifications adopt shared states, badges and pagination. Register retains its existing flow and receives an accessible error alert. Their feature completion remains Phase 2.
- `docs/DESIGN_SYSTEM.md` and `ajiri-backend/docs/CONCEPTS.md`: usage rules, tokens, verification instructions and plain-language concepts.
- `ajiri-backend/frontend_build`: regenerated static deployment build, including lazy route chunks.
- `.gitignore`: ignores the workspace npm cache and isolated QA files inside it.

Backend Python code, migrations, auth client, CORS and CI configuration are unchanged.

## 2. How to run and verify

See DESIGN_SYSTEM.md for exact PowerShell commands. Verification performed on Node 22.15.0 and Python 3.12.6:

- Clean `npm ci`: pass, 0 reported vulnerabilities.
- `npm run lint`: pass without lint warnings.
- `npm run build`: pass; main JS about 90 KB gzip, shared runtime chunk about 36 KB gzip, CSS about 5 KB gzip. Route chunks load on demand. These are build sizes, not measured mobile transfer totals.
- Repository `build_frontend.ps1`: pass; generated build compared with dist.
- Django system check: pass.
- Existing Django suite: 19 tests pass. TEMP/TMP were directed to an ignored workspace directory because sandbox-default temp directories denied writes.
- Browser smoke checks against real Django with an isolated in-memory database: protected redirect and return after login; job detail; prepare application and generated document links; pagination; title search resetting page; filtered empty results; notification mark-read; light/dark persistence; mobile disclosure/navigation; dialog Escape and focus restoration.
- Expired access tokens: server logs confirm 401 -> refresh 200 -> original request succeeds, without visible logout.
- Responsive checks: desktop plus 360px and 390px, without horizontal overflow on checked views.
- Palette checks: normal text pairs meet 4.5:1; input borders meet 3:1. Light muted/surface is 6.04:1 and primary/soft 6.37:1; dark equivalents are 8.43:1 and 7.38:1. This is not a full WCAG audit.

No production requests, real emails or real user data were used in QA.

## 3. Decisions and why

- System fonts avoid external font downloads.
- Locally owned shadcn-style JSX components use Radix for focus-sensitive behaviour; native selects keep mobile controls simple. No TypeScript migration.
- Search is submitted explicitly, avoiding a request on every keystroke. Filters live in the URL for bookmarking and browser history.
- The API client remains unchanged to preserve cookie refresh and token handling.
- Route guards guide navigation; Django continues to enforce authorization.
- The shell stays visible while a lazy page downloads.
- Existing Celery worker/Beat and Redis configuration remains for optional local use. SQLite is the configured database. Production documentation uses GitHub Actions for ingestion/sweeps. No active Postgres configuration was found. Running production services were not inspected.

## 4. Risks and follow-ups

- Michael's browser/Postman review is still required before merge; no push or merge is part of Phase 1.
- Profile notification API gaps, application editing/dismissal and external-employer confirmation flow remain Phase 2, each on its own branch with tests.
- Registration field-by-field validation, CV management and subscriptions remain Phase 2.
- Frontend automated component tests remain Phase 3. Browser checks here are smoke checks, not an automated regression suite.
- Production email delivery and payment processing were not exercised.

Suggested Monday.com tasks (relative story points):

| Completed task | Points |
| --- | ---: |
| Tokens, themes, accessible UI primitives and design documentation | 5 |
| Responsive shell, protected routes and shared page states | 5 |
| Login redesign and return-to-page behaviour | 3 |
| Job listing redesign, API filters and pagination | 5 |
| Job detail redesign and application preparation feedback | 3 |
| Build packaging and Phase 1 verification | 3 |

Stop after Phase 1 for Michael's review before starting Phase 2.
