# Checkpoint 3A deployment security verification — Michael only

No deployment performed by Codex. Apply only a reviewed revision after your normal
backup -> migrate -> activate-code checklist. Checkpoint 3A introduces no migrations.
Do not change JWT/cookie rotation, CORS, ingestion configuration or static mappings.

## Configuration to review privately before activation

| Name | DEBUG=False default | Local DEBUG=True default |
|---|---|---|
| SECURE_SSL_REDIRECT | True | False |
| SECURE_HSTS_SECONDS | 300 | 0 |
| SECURE_HSTS_INCLUDE_SUBDOMAINS | False | False |
| SECURE_HSTS_PRELOAD | False | False |
| SESSION_COOKIE_SECURE / CSRF_COOKIE_SECURE | True | False |
| SECURE_CONTENT_TYPE_NOSNIFF | True | True |
| SECURE_REFERRER_POLICY | same-origin | same-origin |
| X_FRAME_OPTIONS | DENY | DENY |
| TRUST_PROXY_SSL_HEADER | False (opt-in) | False |

Every row reads environment overrides; do NOT enable includeSubDomains/preload in this
rollout. REFRESH_COOKIE_SECURE and JWT/refresh logic are unchanged. Never weaken cookie
security on production to make a broken redirect work.

1. Privately record previous revision, non-secret settings and known-good behaviour.
   Back up DB/private media/config and verify restore as in DEPLOYMENT_CHECKLIST.md.
   Pause writers/callers for the normal cutover; stage reviewed code without activation.
2. Check PythonAnywhere's current support/documentation confirms its front proxy
   overwrites X-Forwarded-Proto, and confirm the app cannot receive arbitrary direct
   external traffic around that proxy. Do not assume the client's header is trusted.
   Also determine the trusted IP hop count separately (THROTTLING.md).
3. Before reload, set TRUST_PROXY_SSL_HEADER=True privately ONLY if step 2 is established.
   Keep SECURE_SSL_REDIRECT=False and SECURE_HSTS_SECONDS=0 while resolving uncertainty;
   retain PythonAnywhere Force HTTPS. If the proxy contract cannot be verified, stop
   rollout and ask support. Do not activate redirect defaults blindly.
4. Run checks from your PythonAnywhere Bash console (no secret printing):

   ```bash
   cd /home/Mathenge/ajiri/ajiri-backend
   workon ajiri
   python manage.py check
   python manage.py migrate --plan
   python manage.py check --deploy
   ```

   Review only the approved migration plan; none new for 3A. Once trust is verified,
   configure redirect=True, HSTS=300, session/CSRF secure=True, nosniff=True,
   referrer=same-origin, frame=DENY, includeSubDomains=False and preload=False using
   the table's environment names, privately. Re-run check --deploy: W004/W008 absent;
   W005/W021 expected because broader HSTS/preload are deliberately off. Never silence
   warnings or enable preload just to obtain a clean warning count.
5. Activate/reload only after checks pass and use credential-free checks from your
   own PowerShell terminal. These inspect the actual public proxy response:

   ```powershell
   curl.exe --head --max-redirs 0 http://mathenge.pythonanywhere.com/login
   curl.exe --head --max-redirs 0 https://mathenge.pythonanywhere.com/login
   curl.exe --head --max-redirs 0 -H 'X-Forwarded-Proto: http' https://mathenge.pythonanywhere.com/login
   curl.exe --head --max-redirs 0 -H 'X-Forwarded-Proto: https' http://mathenge.pythonanywhere.com/login
   ```

   Expected HTTP redirects to HTTPS; HTTPS is 200 without a redirect to itself,
   including when a client spoofs forwarded proto. Headers on HTTPS: HSTS max-age=300
   only, X-Content-Type-Options nosniff, Referrer-Policy same-origin, X-Frame-Options DENY.
   Missing headers/static response behaviour or unexpected redirects block verification;
   do not keep following a loop. These probes supplement, not replace, proxy assurance.
6. Log in through your browser yourself; inspect cookie attributes without copying
   values. Refresh remains Secure/HttpOnly/SameSite=Lax; session/CSRF cookies, if present,
   are Secure. Confirm login/refresh/logout and owner download. Direct private media
   still fails. Check one normal ingestion Actions result after resuming callers;
   never paste keys, cookies, token values or raw mail logs into chat.

## Rollback

Keep HTTPS at the host. If Django loops, privately set SECURE_SSL_REDIRECT=False,
SECURE_HSTS_SECONDS=0, restore the prior verified proxy-trust selection/revision and
reload manually. Keep session/CSRF and refresh cookies secure. Django stops adding
HSTS when zero; browsers may retain the previous 300-second policy until it expires
from their last positive header. HTTPS must continue working throughout. No preload
list or subdomain policy was enabled. Do not restore an old DB over new writes or
reverse migrations. Record outcomes privately; production remains unverified until
Michael completes these steps.
