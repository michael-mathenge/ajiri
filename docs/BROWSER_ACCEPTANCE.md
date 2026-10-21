# Browser acceptance (AJ-27)

This suite drives real Chromium against Django's disposable live test server and
the committed React build. It is separate from Vitest component tests and the
DRF endpoint journey. No production URL, credentials or user data are used.

From `ajiri-backend`, with a development Python environment:

```powershell
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
$env:DEBUG = 'True'
$env:PYTHON_DOTENV_DISABLED = '1'
$env:REAL_EMAIL_ENABLED = 'False'
python manage.py test browser_tests.journey --noinput
```

The explicit label is required: ordinary Django discovery does not import this
optional browser dependency. Browser launch/install failures must fail the explicit
run; they are not reported as skipped successes. The runner creates a test database,
temporary private document storage and a synthetic vacancy. The browser is blocked
from external URLs. No test-only HTTP routes, real mail or production flags are added.
Playwright runs in a worker thread so Django's async-safety protection stays enabled.

Covered: mobile viewport registration and real login/CSRF, profile save, CV start,
preview, explicit approval, private download, required approved-version selection,
application preparation/review, exact CV-byte preservation, no provider calls,
no mail or delivery-ledger reservation. This does **not** yet cover successful
managed application sending; that remains disabled pending its gated integration.
No claim of full AJ-27 completion until that path and CI run are verified.

## CI job (approved and browser-verified 21 October 2026)

Michael explicitly approved the additive job required by AGENTS.md section10:
Ubuntu, Python3.12, install requirements-browser.txt, install Chromium with system
dependencies (`python -m playwright install --with-deps chromium`), then run the
explicit command above. Use synthetic DEBUG/secret settings, disable dotenv and real
email. Preserve all four existing required jobs/check names and branch protection.
Use committed frontend_build so the current consistency check remains authoritative.
No deployment, provider credential, public inbox, live sender or private artifact.
Browser failure fails the job; do not mask failures with `continue-on-error`.

The remaining quality-tool proposals (AJ-28–30) are separate packages, not silently
bundled into this job. Existing backend/frontend required checks are unchanged.

The corrected browser suite passed on Linux at b02d2b7 in
[CI run39599872379](https://github.com/michael-mathenge/ajiri/actions/runs/39599872379).
The initial test wrongly assumed the current approved CV was not displayed by
default; it now explicitly clears and reselects that version. Windows installation
of the optional dependency stalled and was stopped; no local browser pass is claimed.
