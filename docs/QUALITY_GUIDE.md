# Developer quality checks

Use Node24.19 and a Python3.12 development environment. None of these optional
tools belongs in the PythonAnywhere production virtualenv. Existing Oxlint and
application tests remain in place.

```powershell
# From the repository root, with your development virtualenv activated:
python -m pip install -r ajiri-backend/requirements-quality.txt
npm --prefix ajiri-frontend ci
python -m ruff check --no-cache ajiri-backend
python -m pre_commit validate-config
npm --prefix ajiri-frontend run lint:eslint
npm --prefix ajiri-frontend run test:quality
```

Ruff initially checks syntax, undefined-name and invalid control-flow defects;
ESLint adds JavaScript correctness checks. Neither claims a full style/type audit.
Prettier checks changed frontend source/configuration files only: existing formatting
is not rewritten across the repository. Use `npm --prefix ajiri-frontend run
format:write -- PATH` on deliberately selected files and review the diff.
No hook rewrites source automatically. Prettier excludes the generated lockfile.

Hooks are **opt-in**. The setup above does not alter Git configuration or install a
hook. To enable hooks yourself, run `python -m pre_commit install`. Before doing
so, preserve any existing custom hook. Without installing, a developer can run:

```powershell
python -m pre_commit run --files ajiri-backend/jobs/matching.py
```

The frontend hooks call the locked local Node tools and require Node24.19 on PATH.
No remote hook environments or unpinned downloads are invoked by the hook definitions.
The first full-repository Prettier run may report historical formatting: do not
claim that a changed-file policy establishes a clean historical formatting baseline.

## Coverage

The root `.coveragerc` measures lines and branches in accounts/config/jobs/profiles,
excluding migrations, tests and synthetic upload fixtures. It does not exclude
untested application code to increase the score. Keep the original checkout's
coverage database; write this run to the ignored verification directory:

```powershell
New-Item -ItemType Directory -Force .verification/quality | Out-Null
$env:COVERAGE_FILE = (Join-Path (Get-Location) '.verification/quality/.coverage')
Push-Location ajiri-backend
python -m coverage run --rcfile=../.coveragerc manage.py test --noinput
python -m coverage report --rcfile=../.coveragerc
python -m coverage xml --rcfile=../.coveragerc
Pop-Location
```

Run with synthetic DEBUG settings, dotenv disabled and real sending disabled as in
BROWSER_ACCEPTANCE.md. A coverage percentage is evidence of executed paths, not
proof of correctness. No arbitrary minimum percentage has been declared here.

## Type baseline

`python -m mypy --config-file=mypy.ini` reports the existing backend type findings.
This initial stage is nonblocking for legacy code; errors must be reported rather
than presented as a clean type check. It checks bodies of untyped functions, keeps
the custom User unchanged and does not load a Django plugin or query a database.
Known missing third-party types/imports are ignored; imported modules are followed
silently. JavaScript remains JavaScript. Baseline counts/results must be recorded
from actual execution before declaring AJ-30 done.

## CI job — approved 21 October 2026, verification pending

The separately approved isolated quality job uses Python3.12/Node24.19. Install the locked frontend
and requirements-quality.txt. Run Ruff, pre-commit configuration validation, ESLint
and the hook safety test. Measure the full Django suite under coverage and retain
the XML/report as a short-lived source-only CI artifact. Run the initial mypy report
as explicitly nonblocking using `python scripts/type_baseline.py`; preserve its
diagnostics and count. Missing tools and execution failures still fail, as tested
by the wrapper regressions. Preserve the existing five
checks, deployment boundaries and branch protection. No production credential,
email, private file or coverage database from a developer checkout is uploaded.

AJ-29 axe/Lighthouse will be a separate measured accessibility/performance package;
this tooling does not claim those checks exist. The new job's actual result must
be recorded before claiming either AJ-28 or AJ-30 complete.
