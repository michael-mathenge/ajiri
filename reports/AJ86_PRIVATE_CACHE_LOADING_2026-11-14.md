# Deferred private query cache — 14 November 2026

PR108 first head1ed83ed passed backend3.12/3.13/3.14, frontend and quality.
Actual Linux run43602973332 passed11browser journeys but failed the unchanged
mobile budget: login TBT251ms against250ms. Register230ms passed. Login/register
performance81/82, LCP4069.11495/4037.84335ms, CLS0.0996482599/0.0622485528,
transfer474740/471864bytes, trace retries0/0. Retained browser artifact14116813650,
SHA256395c5f20b562a1ec7a559e9321d373823cc65ab18bb436c58d72d495821d21c9.
This valid metric failure is retained; it was not rerun unchanged or relaxed.

The public shell statically imported and initialized the private query cache.
AuthProvider now lazy-loads a separate PrivateQueryProvider only for signed-in
sessions. Each login/logout/account-storage transition resets the keyed private
provider; unmount clears the cache and cancels pending reads before reuse.
Public pages create no query client. JWT cookies/token refresh/interceptor code,
server permissions and request/mutation retry policies are unchanged. A missing
lazy chunk uses the existing explicit page-recovery boundary. No automated retry
of a user action or provider call is added.

The production main JS fell395.30kB to362.34kB in the build report. This is a bundle
observation, not a field p75 or passing Lighthouse result. The47-file generated
build exactly matches dist; index SHA256
c1a069b2ec992fbb5714a2a7a017e01b0337ac0fdd33df9b2dd53aa3e9a42448.

Validation after this fix: both frontend linters,177components28.21s, build2.61s,
and11real Chromium journeys74.607s passed. Two new component regressions verify
no signed-out cache construction and cancellation of a pending private read on
logout; existing account-switch/cache-isolation tests remain. The actual network
journey asserts no private-cache chunk during signed-out registration/login, then
requires it after login. Tests use disposable local data and block external
requests; provider paths remain mocked. Backend business source is unchanged from
the611-test302.848s pass (one existing platform skip); Ruff passes the new browser
assertions. No schema/dependency/CI/budget change. Corrected-head Linux checks and
actual production activation remain pending at this checkpoint.
