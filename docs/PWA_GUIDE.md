# Installable Ajiri and offline fallback

Ajiri can be offered by a compatible browser as an installed standalone app.
Its manifest uses a stable root identity, /login start URL and same-origin192/512
PNG icons based on the existing mint briefcase brand. No push permission or
notification subscription is requested. Installation is optional.

## Privacy and offline behaviour

After a successful online visit, a service worker can show a small generic
offline page for full-page navigation. Reconnect to use jobs, profile, CVs and
applications. The page does not submit or queue actions; if a request was
interrupted, check its status online before retrying. Client-side navigation
inside an already-open app may show its usual connection error instead.

Only four explicit public resources are cached: /offline.html, the manifest and
the two icons. No authenticated HTML, API responses, tokens, profiles, CVs,
applications, private downloads or job payloads are cached by the worker.
Non-GET requests, other origins and API/media/admin/static routes bypass it.
Data caching is not added as a convenience. Existing browser security and server
no-store headers still apply. Public fallback fetches omit credentials.

The worker is registered only for production builds in a secure context. Vite
development and the original Docker lesson are not changed. The existing
WhiteNoise root serves the public files; no hosting setting change is needed.

## Verification and installation

AJ-40 formerly asked for Lighthouse's PWA category. Chrome removed that category;
its acceptance now uses real Chromium installability diagnostics, decoded icon
dimensions, offline navigation, cache-inventory/private-response exclusion and
worker retirement. Existing axe and mobile performance budgets are retained.
Source: https://developer.chrome.com/blog/update-install-criteria .

Local browser tests use a synthetic private account and disposable server. They
verify a private API response is not cached, API fetches fail offline instead of
returning fallback HTML, and the generic offline page contains no account data.
The rollback fixture serves retirement bytes at the original worker URL, matching
a reloaded deployment; it is test middleware only, never production routing.

Manual phone checks remain UNVERIFIED until performed: Android Chrome menu >
Install app (or Add to Home screen), then launch and test offline/reconnect; iOS
Safari Share > Add to Home Screen, then repeat. Browser labels/availability vary.
Do not claim phone installation or a removed Lighthouse badge from desktop tests.

## Updates and rollback

Normal releases update /sw.js with updateViaCache:none. Increment the
ajiri-public-vN cache version when public fallback contents change; activation
removes only earlier Ajiri public-cache versions. Do not delete unrelated caches.
The app shell and private data are fetched online, so approved content is not
replaced by a stale offline snapshot. Failed worker installation leaves normal
online use available.

A rollback release should retain /sw.js and serve the reviewed sw-retire.js bytes
at that original URL. For a reviewed revert package, copy public/sw-retire.js to
public/sw.js, remove the registration block from src/main.jsx, regenerate the
frontend last, run gates, deploy and reload. Keep serving retirement code while
existing clients check for updates. It removes only ajiri-public-* caches and
unregisters itself. Existing open tabs may keep their controller until navigating
or closing; reconnect/refresh after rollback. No account data, backups or other
site caches should be deleted. Simply deleting sw.js is not a retirement plan.

The browser test verifies unregistration and deletion completion explicitly and
retains an unrelated synthetic cache. No production retirement has been performed.
