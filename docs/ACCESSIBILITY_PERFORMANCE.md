# Accessibility and mobile regression checks (AJ-29)

These are automated lab checks, not proof of complete WCAG compliance or field
performance. Manual keyboard, screen-reader, zoom, phone and slow-data checks remain
necessary. No production URL, account, real email or private document is audited.

The isolated browser journey runs [axe-core](https://github.com/dequelabs/axe-core)
on registration, login, jobs, profile, saved CV preview and application review.
Public registration/login/privacy/password-reset-request pages are also checked in
light and dark at 390×844. The selected rules cover WCAG 2.0/2.1 A/AA plus best practices.
All detected violations fail; no blanket exclusions are introduced. Incomplete
rules are retained for manual review, not counted as passes. Reports contain rule
IDs, impacts and selectors, not HTML, credentials, account links or request headers.

[Lighthouse](https://github.com/GoogleChrome/lighthouse) audits only the public login
and registration pages with mobile simulation, using three fresh-browser runs per
page. Each metric's median is compared with lighthouse-budgets.json. Authenticated
page performance, field data and real networks are not claimed covered.

## Initial measurement — Windows, 21 October 2026

Node 24.19, Lighthouse 13.5.0, installed Playwright Chromium 1248, built client at 20939e3:

| Median | Login | Register | Initial regression limit |
| --- | ---: | ---: | ---: |
| Performance |81 |82 |minimum75 |
| LCP |3660ms |3667ms |maximum4500ms |
| Blocking time |110ms |110.5ms |maximum250ms |
| Layout shift |0.0622 |0.0364 |maximum0.1 |
| Transfer |456324bytes |454989bytes |maximum500000bytes |

The initial run was measurement-only and reported a skip, **not** a passing budget
test. Limits allow bounded lab variance and prevent substantial regressions; they
do not turn the observed 3.67s LCP into a good-vitals claim. Improve this baseline
without silently increasing limits. The subsequent enforcing local test passed (one test, 91.159 seconds): login/register median scores 81/81, LCP 3673/3714 ms, blocking time 114/136.5 ms, with unchanged layout shift and transfer. Linux CI results remain pending.
Missing/failed/desktop/nonfinite Lighthouse reports fail closed, with focused tests.

## Run locally

Use the developer environment and locked Node 24.19 frontend installation:

```powershell
python -m pip install -r ajiri-backend/requirements-browser.txt
npm --prefix ajiri-frontend ci
python -m playwright install chromium
$env:DEBUG = 'True'
$env:PYTHON_DOTENV_DISABLED = '1'
$env:REAL_EMAIL_ENABLED = 'False'
Push-Location ajiri-backend
python manage.py test browser_tests.journey browser_tests.performance --noinput
Pop-Location
```

The server/database are disposable Django test infrastructure. Node must be on PATH;
optional NODE_BINARY and CHROME_PATH select the documented local test runtime/browser.
AJIRI_FRONTEND_TOOLS can point to an isolated locked frontend runner. Ordinary
backend test discovery does not silently skip these optional browser tools: the
explicit command fails if they are missing. AJIRI_LIGHTHOUSE_MEASURE_ONLY=1 records
a measurement-only skip; it must never be set in enforcing CI.

Artifacts under .verification/accessibility and .verification/performance are ignored
by Git. Raw Lighthouse diagnostics remain local. The approved CI extension uploads
only sanitized axe JSON and the numeric performance summary for seven days.

## CI extension — approved 21 October 2026, result pending

Michael approved extending the existing browser job with Node 24.19 and `npm --prefix ajiri-frontend ci`.
Keep its current Python/Chromium installation; run both explicit test modules above.
Retain sanitized reports even on failures. Preserve all six existing check names,
quality gates and production boundaries. No provider credentials or real sending.
The optional local Python browser tools are now installed. The complete local browser suite passed two tests in 20.841 seconds, including 14 axe scans. Linux CI results remain a separate merge gate.

## Trace-recording failure handling

A later Windows run reported `NO_NAVSTART`, a missing browser trace event also
tracked in [Lighthouse issue15382](https://github.com/GoogleChrome/lighthouse/issues/15382).
The runner allows one fresh-process retry total per suite for that exact nonzero
execution result. It records a numeric trace_retries count in the summary and logs
the retry explicitly. Other failures, malformed audits and exceeded metrics never
trigger a retry. Three successful measurements per page are still required; a
second recording failure fails the gate. This does not establish the cause of the
initial Linux execution failure, whose unsaved diagnostics remain unavailable.

## Missing navigation traces

A NO_NAVSTART run has no usable navigation measurement and fails the gate. The
single bounded fresh-process retry does not apply to budget failures. Local
synthetic-only trace assets help diagnose browser instrumentation; CI retains
only fixed event-name counts and the browser version parsed from Lighthouse's
report in summary.json. Trace URLs/args/IDs/page source are never uploaded. This
is separate from real mobile metric acceptance. Repeated failures require
investigation; successful PR checks do not erase failed main-run evidence.
