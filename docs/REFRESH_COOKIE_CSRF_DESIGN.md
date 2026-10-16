# Refresh-cookie CSRF design — Checkpoint 3A WP15

Design only. Michael approved option C on 15 October 2026 in the Sprint 3 follow-up.
This records design acceptance (AJ-13), not authorization to implement or deploy it.
No mitigation below is implemented or approved for automatic deployment.
JWT/refresh-cookie logic remains unchanged. Changes to auth, CORS or the interceptor
need Michael's separate approval. Request throttling is not a CSRF mitigation.

## Actual request boundary

- accounts/views.py LoginView and RefreshView are DRF APIViews. Installed DRF marks
  APIViews csrf_exempt; JWT authentication does not enforce Django session CSRF checks.
  The presence of CsrfViewMiddleware alone therefore does not protect this custom flow.
- Refresh takes only refresh_token from a cookie, returns access in JSON and rotates/
  blacklists the token. Cookie: HttpOnly, Secure outside DEBUG, SameSite=Lax, path /,
  seven-day max age, no Domain attribute (host-only). Do not expose its value to JS.
- Production UI/API are same origin. config/settings.py has CORS_ALLOW_CREDENTIALS=True;
  default production CORS_ALLOWED_ORIGINS is empty, development permits localhost/127.0.0.1
  on port 5173. The frontend axios client uses withCredentials and a plain axios refresh
  request. Refresh requires no access-token Authorization header by design.
- Lax generally excludes cookies from cross-site POST, but same-site is broader than
  origin: another port or a related host may be same-site. HttpOnly prevents reading,
  not browser attachment. CORS limits reading responses/preflight, not all requests.
  A form POST can trigger a state-changing request without reading its response.
- Consequences may include token rotation/session disruption; login CSRF can confuse
  account identity. This audit has not demonstrated an end-to-end exploit or cross-site
  token exfiltration. XSS/token theft and inactive-user refresh are separate open risks.

## Options

| Option | Benefit | Trade-off / limits |
|---|---|---|
| A. SameSite=Strict only | Small cookie change, stronger cross-site attachment restriction | Still allows same-site cross-origin requests; can affect external-navigation/embedded flows; not a complete CSRF control |
| B. Exact Origin validation plus non-simple custom header on login/refresh | Small explicit browser boundary; cross-origin attacker cannot add header without preflight; no new secret required | Reject null/absent Origin by default; nonbrowser clients need explicit documented policy. Static header alone is not secret or sufficient; proxy origin handling must be correct |
| C. Explicit Django CSRF validation, bootstrapped CSRF cookie/token and exact origin checks | Standard token+origin defence, no new dependency; covers form/browser attacks | Adds bootstrap/client/header contract and rejection handling. DRF exemption must be explicitly addressed; login token rotation must be handled; refresh cookie stays HttpOnly |

Recommendation: **C** for the durable solution, with same-origin deployment retained.
B is a smaller interim option only if separately approved with strict missing/null-origin
policy and adversarial tests. A may add defence-in-depth later but should not replace
request validation. Keep the refresh cookie itself Lax until a separately reviewed change.

For C, use Django's normal CSRF secret/masking/origin validation rather than a naive
unsigned double-submit implementation. A readable CSRF cookie contains only the CSRF
secret, never JWT/refresh tokens. Obtain a token from an explicit same-origin bootstrap
response, attach X-CSRFToken to login/refresh (and other approved cookie-based mutations),
and validate before authentication side effects. Constrain trusted origins to the actual
reviewed UI origin(s), never wildcard/suffix string matching. Production requires HTTPS.
Local Vite needs an explicit reviewed origin/token bootstrap contract; don't silently
expand existing CORS settings. No third-party-site exception is proposed.

## Proposed interface and failure policy (requires approval)

- Proposed GET CSRF bootstrap with no-store response and no auth token in JSON; no
  DB change. Exact route is selected in the eventual auth implementation review.
- Login/refresh carry CSRF header and cookie. Invalid/missing CSRF/origin returns a
  stable 403 detail before token creation/blacklisting. Existing valid 200 and invalid
  refresh 401 behaviours remain. Never consume/rotate a refresh on rejected CSRF.
- Frontend must distinguish 403 from 401 and request a fresh CSRF token once only
  when appropriate; do not create mutation loops, silently clear unrelated sessions,
  or retry ambiguous sends. Review the existing silent-refresh catch/logout behaviour.
- Do not waive checks for missing Origin/User-Agent or a caller-provided proxy header.
  Any native/server client support needs a separately explicit auth contract.

## Test plan before implementation approval

Use disposable local test users/token material only; no production probes or raw token
logging. Unit/API tests must enforce real CSRF checks (ordinary DRF test clients bypass
some checks unless configured). Browser tests/manual smoke are also needed for SameSite.

1. Valid HTTPS same-origin bootstrap/login/refresh works; refresh rotates and old token
   replay is 401. Refresh token stays cookie-only and HttpOnly/Secure/Lax.
2. Missing/mismatched CSRF cookie/header, missing/null/untrusted Origin and malicious
   same-site different-port origin get 403 without rotating/blacklisting or minting tokens.
3. Exact trusted development origin succeeds only under approved development configuration;
   scheme, port, suffix-lookalike and unrelated domain mismatches fail.
4. Simulated malicious form/simple POST and custom-header preflight cannot change session
   state. CORS response policy remains unchanged unless a separate change is approved.
5. Expired/missing refresh remains 401 after CSRF request validation; valid CSRF is not
   authentication. Existing login/logout and public stale-Authorization exclusions work.
6. Check concurrent refresh requests, tab start-up and token-bootstrap expiry. Prevent
   repeated automatic refresh loops; throttled 429 is visible without retry storms.
7. Test external navigation/normal mobile usage before considering Strict cookies.
   XSS and nonbrowser forged headers are not solved by CSRF protection; don't claim they are.

## Manual rollout and rollback proposal — Michael only

Ship server/client contract together through reviewed build packaging; no migration.
Before any production activation, back up, verify proxy HTTPS/origin assumptions and
run local tests. No server changes are performed by this document. Stage rollout to a
controlled account and monitor only sanitized event categories/counts, no cookie values.

If legitimate refresh breaks, keep HTTPS and private media protections, preserve issued
refresh-cookie semantics, and revert to the prior reviewed server/client revision together.
Do not weaken CORS, disable Secure cookies, expose refresh in JSON or accept every Origin
as a hotfix. Reverting validation reopens the documented gap: record that risk and pause
new onboarding until an approved fix is ready. No schema reversal is needed. Never
invalidate/reset every account merely to roll back request validation.

References: [DRF CSRF/CORS](https://www.django-rest-framework.org/topics/ajax-csrf-cors/),
[Django CSRF protection](https://docs.djangoproject.com/en/6.1/ref/csrf/).

## WP18 local implementation — 16 October 2026

Option C is implemented locally for Phase A, not deployed. GET /api/accounts/csrf/
returns {csrfToken: masked Django token}, sets the CSRF cookie, and is no-store.
It ignores stale JWT headers and has THROTTLE_CSRF_RATE=60/min by default.
POST login/refresh/logout require exact Origin plus Django cookie/header checks;
rejection is 403 {detail: generic message, code: csrf_failed}. Validate before
credentials, blacklist or cookie side effects. Successful login rotates CSRF;
JWT access-only JSON, refresh cookie flags/lifetimes/rotation are unchanged.

DEBUG dev CSRF defaults list only the existing localhost/127.0.0.1:5173 UI origins;
explicit CSRF_TRUSTED_ORIGINS overrides them. CORS is unchanged. Production trusts
only its own origin plus exact explicitly configured CSRF origins, no wildcard match.
The ordinary Django test client's exemption remains; attack tests explicitly enforce
checks and cannot be taken as a reason to disable production CSRF.

Current sessions need no forced reset: upgraded frontend bootstraps before the next
cookie mutation. An old open tab may fail with CSRF 403 until reloaded; tell users
to reload, never clear every token/account. Failed post-login bootstrap does not
turn an issued login into failure; the next mutation fetches again. Parallel expired
requests share one refresh. Identified CSRF rejection gets one bootstrap/retry;
other mutations/403s never automatically retry. Refresh 401 alone retains existing
logout handling; 403/429/network failures preserve local access and surface errors.

No runtime bypass switch is added. Roll back the reviewed backend and packaged
frontend together via Michael's normal deployment flow. Rollback reopens the known
gap; do not weaken CORS/cookie security, erase DB data or rotate all sessions.
Manual review: new login; reload; expire access; confirm silent refresh; logout;
check missing/wrong token and hostile/null/missing Origin return 403 without rotating
refresh; existing sessions bootstrap successfully. Use synthetic local users only.
