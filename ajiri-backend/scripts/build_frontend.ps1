# Builds the React app and copies the result into ajiri-backend/frontend_build/,
# which Django serves (see config/urls.py and docs/CONCEPTS.md#spa-fallback-route).
#
# Run from anywhere:  .\scripts\build_frontend.ps1
# Assumes the folder layout  <project>\ajiri-backend  and  <project>\ajiri-frontend.
# Commit the refreshed frontend_build/ afterwards so the server gets it on `git pull`.
$ErrorActionPreference = 'Stop'

$backend  = Resolve-Path (Join-Path $PSScriptRoot '..')
$frontend = Join-Path $backend '..\ajiri-frontend'

if (-not (Test-Path $frontend)) {
    throw "Frontend folder not found at $frontend"
}

Push-Location $frontend
try {
    npm install
    if ($LASTEXITCODE -ne 0) { throw 'npm install failed' }
    # Uses .env.production, so the app calls the API at the relative path /api.
    npm run build
    if ($LASTEXITCODE -ne 0) { throw 'npm run build failed' }
} finally {
    Pop-Location
}

$target = Join-Path $backend 'frontend_build'
if (Test-Path $target) { Remove-Item -Recurse -Force $target }
Copy-Item -Recurse (Join-Path $frontend 'dist') $target
Write-Host "Frontend copied to $target"
