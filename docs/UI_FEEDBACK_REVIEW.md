# UI feedback review — 17 October 2026

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. This document version was already present at recorded production revision 641cdfb. Historical statements/results below are preserved; see AGENTS.md section 4.

One local frontend package, three approved steps. Base: main `3309803`.
Branch: `codex/ui-feedback-polish`. No push, deployment, real email, backend
behavior, dependencies, migrations, auth interceptor, CI or production changes.

| Step | Result | Suggested points |
|---|---|---|
| Empty-profile job cards | Add skills link instead of a misleading score; genuine zero scores preserved | 2 |
| Registration errors | Bordered summary, spaced field messages, visible invalid input borders; all errors and associations preserved | 1 |
| Account email retry wait | Readable minutes/seconds, disabled submission until Retry-After expires, manual retry only | 2 |

The jobs screen reads `/profiles/me/` once per mount for all cards, independently
of jobs pagination/filter requests. Failed/pending profile reads withhold scores
and empty-profile advice without blocking jobs. Returning from Profile refetches.
Job detail and historical notification scores are unchanged.

The countdown accepts seconds and HTTP dates. It accounts for elapsed time in a
background tab. Invalid/missing headers show generic guidance. Reloading resets
the display; server throttling remains authoritative. No limit is bypassed and no
email or mutation is automatically retried. Delivery remains unconfirmed by this
package; the earlier 429 does not prove repeated clicking or a successful send.
The queued new-user alert-default change remains outside this UI package.

## Actual verification

Executed in the isolated checkout on 17 October 2026:

- Backend with dotenv disabled, DEBUG=True, REAL_EMAIL_ENABLED=False:
  `python manage.py check`: no issues;
  `python manage.py makemigrations --check --dry-run`: no changes;
  `python manage.py test --noinput`: 178 tests, OK, one Windows symlink skip.
- Frontend using bundled Node 24.19.0 and npm CLI explicitly:
  `npm ci`: 180 packages installed, zero reported vulnerabilities;
  `npm run lint`: exit 0;
  `npm run test -- --run`: 51 tests across eight files passed;
  `npm run build`: passed, Vite 8.3.4.
- Focused tests cover empty versus populated skills and failed profile fetches,
  all registration messages/associations, 429 submission blocking and manual
  expiry, background elapsed time, malformed headers and HTTP date parsing.
- Browser visual QA: **UNVERIFIED**. The browser's localhost address reached a
  different app rather than this checkout; no actions were taken in that app.
  Light/dark/mobile appearance and real screen-reader behavior need manual review.

## Review steps

Use the isolated checkout; leave the original checkout's dirty files untouched.
In PowerShell:

```powershell
cd C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-frontend
$env:PATH = 'C:\Users\micha\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;' + $env:PATH
node 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js' run test -- --run
```

Expected: 51 tests pass and the command exits. For a local development preview,
use your normal local backend and `npm run dev`; never point it at production.

1. With a local test account containing no skills, browse jobs. Cards offer
   “Add skills to see your match”, linking to Profile. Add a skill and return:
   scores appear, including genuine zero matches. Simulate a failed profile GET:
   jobs remain available without a guessed score or empty-profile claim.
2. Submit registration with server-rejected test values. Every returned error is
   readable in the bordered summary; affected inputs have visible borders and
   associated descriptions. Check both themes and a narrow phone viewport.
3. With a mocked/local 429 and `Retry-After: 65`, request an account email.
   Expect “1 min 5 sec”, a disabled button and no further POSTs. After expiry,
   the button enables; no POST occurs until clicked. Do not generate real email
   requests to test limits. Reload resets the display, not the server limit.

## Rollback and review boundary

Review the source and matching final committed `frontend_build` together. Revert
this UI package and rebuild together if needed; no database rollback is needed.
Existing root AGENTS changes, lockfile, coverage data, Git configuration and stash
were preserved. Stop here for review; publishing/deployment requires authorization.
