# Ajiri Backend — Concepts Glossary

Running notes on Django/DRF concepts I had to look up while building this.
Referenced from inline comments in the code as `# see docs/CONCEPTS.md#slug`.

---

## virtual-environment
A sealed, private copy of Python + installed packages for one project only.
Prevents `pip install` for one project from breaking another. Created with
`py -3.12 -m venv .venv`, activated with `.venv\Scripts\activate`.

## migrations
Django's system for keeping the database schema in sync with `models.py`.
`makemigrations` reads your models and writes a *plan* (a Python file) —
it does NOT touch the database. `migrate` actually executes that plan.
Order matters: e.g. `accounts.0001_initial` must apply before `admin.0001_initial`
because admin depends on knowing what the User model looks like.

## custom-user-model
Django's default User uses `username` for login. To use email instead, you
can't just tweak a setting — you replace the whole User model, using
`AbstractBaseUser` (bare-bones, no username) + `PermissionsMixin` (adds
admin/permission support) + a custom `UserManager` (tells Django *how* to
create a user without a username). Must be set up via `AUTH_USER_MODEL` in
settings.py BEFORE any real data exists — changing it later is very painful.

## serializer
Translator between raw JSON and Python model objects. Two jobs:
(1) validation — check incoming data is valid before touching the DB,
(2) conversion — JSON → model instance, and model instance → JSON.
`ModelSerializer` auto-generates fields from a model via `Meta.model`.
`write_only=True` = accept on input, never show on output (e.g. passwords).
`read_only=True` = show on output, ignore on input.

## generic-views (DRF)
Pre-built view classes for common patterns, so you don't hand-write the
same "validate → save → respond" logic every time.
- `CreateAPIView` = POST only (e.g. registration)
- `RetrieveUpdateAPIView` = GET + PUT/PATCH bundled (e.g. profile)

## jwt-access-vs-refresh
Two tokens issued at login, doing different jobs:
- ACCESS token: short-lived (15 min), sent on every request via
  `Authorization: Bearer <token>`, proves "I'm logged in right now."
- REFRESH token: long-lived (7 days), stored in an httpOnly cookie
  (invisible to JavaScript — protects against theft via XSS), ONLY used
  to silently get a new access token when the old one expires.
They're linked by which login event created them, not by value.

## httponly-cookie
A cookie flag that makes it invisible to JavaScript entirely — only the
browser can read/send it. This is why the refresh token lives in a cookie
(safe from malicious JS) while the access token lives in the JSON response
(frontend JS needs to read it to attach to headers, so it can't be httpOnly).

## token-rotation-and-blacklisting
Every time a refresh token is used to get a new access token, the OLD
refresh token is invalidated (blacklisted) and a genuinely NEW refresh
token is issued. Prevents a stolen old token from being reused forever.
GOTCHA: just calling `str(refresh)` again does NOT create a new token —
you must call `refresh.blacklist()` then `set_jti()`/`set_exp()`/`set_iat()`
to actually mutate the token's identity before re-stringifying it.

## django-signal
Code that runs automatically when something happens elsewhere in the app,
without that other code needing to know this file exists. Example:
`post_save` fires every time ANY model instance is saved — our
`profiles/signals.py` listens for User saves specifically and auto-creates
a blank Profile. Must be manually "activated" via `apps.py`'s `ready()`
method importing the signals file — otherwise the decorator never connects.

## many-to-many-relationship
Used when many of A can relate to many of B (e.g. many profiles can each
have many skills, and each skill can belong to many profiles). Django
auto-creates a hidden joining table (e.g. `profiles_profile_skills`) to
store these links — you never touch that table directly, just use
`.set()` (replace all links), `.add()` (add without removing), or query
through the relationship normally.

## get_or_create
`Model.objects.get_or_create(name=x)` — finds an existing row matching
`name=x`, or creates one if it doesn't exist. Returns `(object, created_bool)`.
Used for skills so "Python" only ever exists once in the database, no
matter how many different profiles list it — critical for match-scoring
to work efficiently later.

## related_name
When you define a relationship field (ForeignKey, OneToOneField, ManyToMany),
`related_name` lets you query it BACKWARDS from the other side. E.g.
`Profile.user` with `related_name='profile'` means you can write
`some_user.profile` to get their Profile directly — very convenient.

## double-underscore-lookup
Django's syntax for reaching across a relationship in queries, e.g.
`search_fields = ('user__email',)` in admin means "go through the `user`
link, then search its `email` field." Used constantly in filters/lookups.

## curl-vs-curl.exe-on-windows
PowerShell secretly aliases `curl` to its own `Invoke-WebRequest`, which
uses different syntax than real curl. Use `curl.exe` explicitly to bypass
the alias and get standard curl behavior (needed for `-X`, `-H`, `-d`, etc.)

## git-branching
`main` = always a safe, working checkpoint. `feature/xyz` branches let you
work on something new without risking `main` until it's tested and ready.
`git checkout -b name` creates + switches in one step. Merging brings a
feature branch's commits into `main` — if `main` never changed while you
were working, it's a "fast-forward" (no real merge needed, just moves
the pointer).

## pull-request (PR)
A GitHub feature (not a git concept) for reviewing changes before merging.
Lets a collaborator see a diff, comment on specific lines, and approve
before code touches `main`. More valuable with 2+ people than solo, but
good practice to know for when Ajiri gets contributors.

## application-method-detection
When ingesting a job, we scan its description for an email address using
regex (`jobs/utils.py::detect_application_method`). If found, the job is
flagged `application_method='email'` and `application_email` is stored —
this job supports true auto-apply (we can programmatically send an
application email on the user's behalf). If no email is found, the job
is flagged `application_method='external_link'` — the user must click
through to `source_url` and apply manually.

This distinction exists because true auto-apply is only safe and reliable
when we're just sending an email; auto-filling arbitrary third-party web
forms (Workday, Greenhouse, company career portals, etc.) is fragile,
breaks constantly as those sites change, and risks violating their terms
of service. Even for email-method jobs, the design decision was to never
send silently — every application is drafted, then a human reviews/edits
and hits send. See `application-lifecycle` below.

## application-lifecycle
The `Application` model (`jobs/models.py`) tracks one user applying to one
job, moving through four states:
- `draft` — reserved for a future "save for later" step.
- `ready_for_review` — CV + cover letter generated, nothing sent yet.
- `sent` — user reviewed (optionally edited) the draft and hit send.
- `dismissed` — user declined to apply to this match.

Two things make this different from the CV/cover-letter generators
(`profiles/cv_generator.py`, `jobs/cover_letter_generator.py`), which build
a `.docx` fresh in memory (`BytesIO`) on every request:
1. `Application.generated_cv`/`generated_cover_letter` are saved as real
   files (`media/applications/`), generated ONCE when the user clicks
   Apply — so the document reviewed is exactly the one that gets sent.
2. `application_method`/`application_email` are copied ("snapshotted") from
   the `Job` at that moment, so an in-progress application can't silently
   change if the job listing is edited later.

`unique_together = ('user', 'job')` guards against duplicate drafts, and
`ApplyToJobView` is idempotent: applying twice returns the existing one.
Drafts are created ON DEMAND (the user clicks Apply), not automatically:
generating files costs compute and storage, so it only happens when asked.

## job-alerts
Notifying a user that a new job matches their profile is kept SEPARATE
from Application drafts, and deliberately runs automatically — unlike
drafts, alerts cost effectively nothing:
- Email: free (just your EMAIL_BACKEND).
- In-app: free (just a `Notification` row read by the frontend).
- SMS/WhatsApp (Africa's Talking): NOT free once live — real per-message
  cost, a one-time Sender ID fee and a multi-day approval process.
  Deferred until there is a monetization path to cover it.

`notify_matching_profiles(job)` (jobs/matching.py) runs from two triggers:
1. Immediately at the end of each job's ingestion — a strong match
   (score >= MATCH_ALERT_THRESHOLD, currently 70%) reaches the user at once.
2. A periodic sweep (`sweep_all_active_jobs_for_matches`) — catches matches
   the immediate check misses, e.g. a profile created or edited AFTER the
   job was ingested. Celery Beat runs it locally; in production a scheduled
   GitHub Actions workflow calls POST /api/jobs/sweep/ instead.

`Notification` has `unique_together = ('user', 'job')`, so both triggers can
discover the same match and still only one alert ever fires per pair.

## cors
CORS (Cross-Origin Resource Sharing) is a BROWSER security rule — different
ports count as different "origins" even on the same machine, so JS running
on localhost:5173 (React) is blocked by default from calling
127.0.0.1:8000 (Django), even though nothing is actually wrong with the
request itself. Postman never hits this because Postman isn't a browser
and doesn't enforce it — this is why something can work perfectly in
Postman and fail silently (well, loudly, in the Console) from the actual
frontend.

The browser first sends an invisible "preflight" OPTIONS request asking
"do you allow requests from my origin?" before sending the real
POST/GET/etc. If the server's response doesn't include an
Access-Control-Allow-Origin header matching the requesting origin, the
browser refuses to send the real request at all — you'll see the OPTIONS
request succeed (200) in the Django terminal, but the actual POST never
even shows up there, because the browser blocked it client-side before
it went out.

Fixed via django-cors-headers: add 'corsheaders' to INSTALLED_APPS,
'corsheaders.middleware.CorsMiddleware' near the TOP of MIDDLEWARE (must
run before most other middleware), and a CORS_ALLOWED_ORIGINS list naming
exactly which frontend origins are trusted. Settings.py changes need a
runserver restart — unlike regular code changes, which auto-reload.

## stale-token-on-public-endpoints
Attaching a JWT to EVERY request (even AllowAny ones like login/register)
can break those endpoints if the stored token is expired or invalid.
Permission (`AllowAny`) and authentication are separate DRF steps —
`AllowAny` means "no permission required," but if `JWTAuthentication` is
in `DEFAULT_AUTHENTICATION_CLASSES` project-wide, DRF still tries to
validate any Authorization header present and raises an error if it's
bad, BEFORE the view runs at all — regardless of that view's permission
class. Symptom: login fails with a misleading "invalid credentials"-style
error even though the email/password are correct, because the real
rejection never reaches the actual credential check. Fixed in
`src/api/client.js` by excluding known public/auth endpoints from the
request interceptor's Authorization header entirely.

## cors-credentials
Cross-origin cookies (here: the httpOnly refresh_token cookie, set by
Django, needed by the browser at localhost:5173) are NOT sent/accepted
by default, even with CORS otherwise working. Both sides must opt in
explicitly: the frontend sets `withCredentials: true` on every request
(axios config), and the backend sets `CORS_ALLOW_CREDENTIALS = True`
(django-cors-headers). Without both, Set-Cookie headers from the server
are silently dropped by the browser — no error is shown anywhere, the
cookie just never appears in DevTools, which makes this easy to miss.

## refresh-on-401
An axios response interceptor (src/api/client.js) catches any 401 from a
PROTECTED endpoint, assumes it means "access token expired" (normal after
15 min, not a real error), and silently: calls /accounts/refresh/ using
the httpOnly cookie, stores the new access token, retries the original
failed request once, and returns that retried response to the original
caller — who never sees the failure at all. If the refresh itself fails
(refresh token also expired, 7-day window passed), the user is logged out
and redirected to /login. An `_retry` flag on the request config prevents
infinite refresh loops. The refresh call itself uses plain axios, not
apiClient, to avoid recursively triggering these same interceptors.
## mojibake
Garbled text like 'â€"' appearing where an en-dash (or curly quote, etc.)
should be. Cause: the original text was correctly encoded as UTF-8, but
something decoded those bytes using the WRONG character set — here,
Windows-1252 — before the string was ever saved. feedparser.parse(url)
with no explicit charset override trusts the source server's declared
encoding (or a default guess per RFC 3023 when that's ambiguous); for
the MyJobMag feed specifically, it guessed cp1252 instead of UTF-8.

The fix is reversible with ZERO data loss, because nothing was actually
destroyed — only mis-decoded. Re-encoding the WRONG string back to
cp1252 bytes recovers the ORIGINAL correct UTF-8 bytes, which then
decode properly:
    text.encode('cp1252').decode('utf-8')
This only works, and will usually raise an error, on text that WAS
actually corrupted this specific way — which is why fix_mojibake()
(jobs/utils.py) wraps it in try/except and returns the original text
unchanged on failure, making it safe to call on any string.

Two-part fix: (1) ingestion.py now calls fix_mojibake() on every text
field pulled from the feed, so this can't happen to NEW jobs going
forward; (2) a one-off management command,
`python manage.py fix_mojibake` (add --dry-run to preview first),
repairs jobs already sitting in the database with the bug baked in.

## django-management-commands
A way to add custom `python manage.py <name>` commands beyond Django's
built-ins (migrate, runserver, etc.). Structure: a `management/commands/`
folder inside an app (here, jobs/), with an empty `__init__.py` in both
`management/` and `management/commands/` (marks them as Python packages —
without these, Django won't discover the command at all), and one file
per command named after the command itself (fix_mojibake.py defines
`python manage.py fix_mojibake`). Each file defines a `Command` class
inheriting from `BaseCommand`, with a `handle()` method holding the
actual logic. `add_arguments()` lets a command accept flags like
--dry-run, read back via the `options` dict passed into `handle()`.
Good for one-off data repairs, scheduled maintenance, or anything that
needs to run as a standalone script but still wants full access to
Django's models/settings — same environment as a view, just triggered
from the terminal instead of an HTTP request.

## remote-ingestion
Some hosts block outbound requests (PythonAnywhere's free tier only lets a
server reach whitelisted sites), so the server can't fetch the job feed
itself. Remote ingestion flips the direction: something WITH open
internet (a scheduled GitHub Actions workflow) downloads the feed XML and
POSTs it to `POST /api/jobs/ingest/`, where `IngestFeedView` runs it
through `ingest_feed()` — the same dedupe / mojibake-repair / scam-check /
match-alert pipeline the Celery task uses. `ingestion.py` was split in
two for this: `ingest_feed(feed)` processes an already-parsed feed, and
`ingest_myjobmag_kenya()` is now just "fetch, then call ingest_feed()".

The endpoint is called by a machine, not a user, so it skips JWT entirely
(`authentication_classes = []`) and checks a shared secret in an
`X-Ingest-Key` header instead. Three details matter:
- An UNSET server key must disable the endpoint, never open it — otherwise
  forgetting the environment variable leaves it unprotected.
- `hmac.compare_digest` compares in constant time, so response timing
  can't be used to guess the key a character at a time.
- The body is parsed as raw BYTES, so feedparser reads the encoding from
  the XML itself rather than guessing from HTTP headers (the guess that
  caused the mojibake bug).
Also raised `DATA_UPLOAD_MAX_MEMORY_SIZE` to 10 MB, since Django rejects
request bodies over 2.5 MB by default and a full feed could exceed that.

## environment-variables
Configuration that differs per machine, or must stay secret, is read from the
process environment instead of being written into code:
`os.environ.get('INGEST_API_KEY', '')`. The same code then runs unchanged on
your laptop and on a server; only the values differ.

Setting them by hand (`$env:NAME = "value"` in PowerShell) only lasts for that
one terminal tab, which is easy to forget. So `config/settings.py` also loads a
git-ignored `.env` file next to `manage.py` using python-dotenv
(`load_dotenv(BASE_DIR / '.env')`). Real environment variables win over `.env`.
`.env.example` is the committed template (never put a real secret in it);
copy it to `.env` and fill it in. The same mechanism works on PythonAnywhere.

Fail-safe defaults: `DEBUG` defaults to OFF, and with DEBUG off a missing
`SECRET_KEY` raises `ImproperlyConfigured` instead of starting insecurely —
forgetting to configure a server fails loudly, not silently. Locally, put
`DEBUG=True` in `.env`. The old hard-coded key is in git history, so treat it
as public and never use it for anything real.

## secure-cookies
A cookie flagged `Secure` is only sent over HTTPS. Local development runs on
plain HTTP, so the refresh cookie used `secure=False`; on a real HTTPS site
that would let the cookie travel unencrypted. `settings.REFRESH_COOKIE_SECURE`
(and SESSION/CSRF_COOKIE_SECURE) are `not DEBUG`: off locally, on in
production. `HttpOnly` (invisible to JavaScript) is a separate flag that stays
on in both.

## whitenoise
Django's dev server serves static files (admin CSS, etc.) for you, but with
`DEBUG=False` it stops — in production something else must. WhiteNoise is
middleware that serves them straight from Django, so no separate web-server
configuration is needed. `collectstatic` copies every app's static files into
`STATIC_ROOT` (`staticfiles/`), and WhiteNoise serves that folder. It also
serves the built React app: `WHITENOISE_ROOT` points at `frontend_build/`, so
`/assets/...` files come from there. It does NOT serve user uploads
(`media/`) — on PythonAnywhere that folder gets its own static-files mapping
on the Web tab.

## spa-fallback-route
React Router changes the URL in the browser without asking the server, so a
page like `/jobs/5` exists only client-side. If you refresh on it, the
browser asks Django for `/jobs/5`, which Django has never heard of. The fix
is a catch-all route, last in `config/urls.py`, that returns the same
`index.html` for any path that isn't `api/`, `admin/`, `media/` or `static/`;
React then boots and its router renders the right page. `never_cache` on that
view matters: `index.html` names hashed asset files, so the browser must
re-fetch it after every deploy to pick up new ones.

## vite-env-variables
Vite replaces `import.meta.env.VITE_*` values in your code with fixed text AT
BUILD TIME — they are not read when the page runs in the browser, and anything
you put in them ships to every visitor, so never put a secret there. Which file
supplies them depends on the command: `.env.development` for `npm run dev`
(API at `http://127.0.0.1:8000/api`, another port) and `.env.production` for
`npm run build` (API at the relative path `/api`, because Django serves the
app itself, so there is no cross-origin request and no CORS to configure).
Changing a value means rebuilding.

## unguessable-filenames
Generated CVs and cover letters are plain files under `media/`, served by URL
with no login check. A predictable name like `CV_Acme.docx` would let anyone
who guesses it download someone's CV, so each file gets a random 32-character
prefix (`uuid.uuid4().hex`). That protects new files by obscurity only — the
URL is a secret link, not real access control. The proper fix is to serve CVs
through a Django view that checks the logged-in owner; until then, treat the
URLs as sensitive. Files created before this change keep their old names.

## github-actions
GitHub's built-in automation: YAML files in `.github/workflows/` (GitHub only looks
for them at the repository ROOT) that run on
GitHub's servers when something happens. Three are used here:
- `ci.yml` — Continuous Integration: on every push and pull request it installs
  dependencies and runs `manage.py check`, a missing-migrations check and the
  tests (on Python 3.12 and 3.13), so a broken change is caught before merging.
- `ingest.yml` and `sweep.yml` — scheduled jobs (`on: schedule: cron`) that call
  the production API on a timer; see `remote-ingestion`. Scheduled workflows run
  only from the default branch (`main`); `workflow_dispatch` adds a manual Run
  button. GitHub may delay runs queued at minute :00, so the schedules use odd
  minutes. Credentials come from repository Secrets (`${{ secrets.NAME }}`),
  which are masked in logs and never stored in the repo.
Cron syntax: `17 */3 * * *` = minute 17, every 3rd hour, every day.

---

# Frontend (React) Concepts

## node-and-npm
Node.js is a JavaScript runtime — it lets JS run outside a browser. `npm`
(Node Package Manager) ships with it and is JS's equivalent of `pip`. Every JS
project gets its own `node_modules/` folder (created by `npm install`) holding
that project's dependencies — no `.venv`-style "activate" step; you're always
just "in" whichever project folder you're standing in.

## vite
The tool that runs a React app locally (dev server with live reload) and
bundles it into static files for production (`npm run build`). Roughly Django's
`runserver` + `collectstatic` combined, but for a JS frontend.

## spa-single-page-application
Unlike Django, which sends a fresh HTML page per URL, a React app ships ONE
`index.html`, ever. It is nearly empty — a single `<div id="root">` — and React
injects/swaps content into it as the user navigates, with no full page reload.
Routing between "pages" happens entirely in the browser (see `react-router`).

## react-component
The core building block: an ordinary JavaScript function that returns JSX and
is exported so other files can use it. Component names are Capitalized (`App`,
not `app`) — that is how JSX tells a custom component from a plain tag like
`<div>`. Every Ajiri screen is its own component.

## jsx
The HTML-looking syntax inside a component's `return (...)`. Not valid
JavaScript on its own — Vite compiles it into plain JS function calls before
the browser runs it. Inside JSX, single curly braces `{ }` evaluate a real
JavaScript expression — the equivalent of Django's `{{ variable }}`, except it
is actual JavaScript, not a separate template language.

## useState-and-state
`useState` is a React "Hook" that gives a component memory between renders.
`const [count, setCount] = useState(0)` creates a state variable and returns
the current value plus a function to change it. Calling `setCount(...)` tells
React to re-render the component with the new value. You never touch the page
yourself (no `document.getElementById(...)`); you describe what the UI should
look like for the current state and React updates the screen.

## jsx-attribute-quirks
Some HTML attributes are renamed in JSX because they collide with JavaScript:
`class` becomes `className`, and `onclick="..."` (a string) becomes
`onClick={...}` (a real function).

## react-fragment
A component can return only ONE root element. `<> ... </>` is a Fragment: an
invisible wrapper that lets you return several siblings without adding an
extra real `<div>` to the page.

## react-router
A library that lets an SPA fake having multiple pages. `<BrowserRouter>` wraps
the app once (in `main.jsx`) and watches the URL; each `<Route path="..."
element={<Component />} />` maps a URL to a component — like one line of
Django's `urlpatterns`, but matched in the browser with no reload.
`path="/jobs/:id"` is a URL parameter (like `<int:pk>`), read with the
`useParams` hook. `<Link to="...">` replaces `<a href>`: a real `<a>` would do
a full page reload, defeating the point of an SPA.

## controlled-forms
React ties every input's value to state: `value={x}` shows it,
`onChange={(e) => setX(e.target.value)}` updates it on every keystroke, and
`onSubmit` on the form calls `event.preventDefault()` first to stop the
browser's default full-page submit.

## async-await
Plain JavaScript for work that takes time, like a network request, without
freezing the page. `await apiClient.post(...)` pauses that function until the
response arrives (inside a function marked `async`). Pair it with
`try`/`catch` to handle failures — similar to Python's `try`/`except`.

## axios-and-interceptors
axios is a library over the browser's `fetch()`. Interceptors are functions
that run before every request (or after every response). Ajiri's
`src/api/client.js` builds one shared client with `axios.create({ baseURL })`,
a request interceptor that attaches the JWT as an `Authorization` header, and a
response interceptor that handles expired tokens (see `refresh-on-401`).

## localstorage-token-tradeoff
`localStorage` is the browser's simple persistent key-value store. The JWT
access token lives there — simple to build with, but anything in
`localStorage` is readable by any JavaScript on the page, including a
malicious injected script (XSS). An acceptable tradeoff early on, and worth
revisiting (e.g. an httpOnly cookie, as the refresh token already uses) before
real users' credentials are at stake.

## monorepo
One git repository holding several related apps — here the Django backend and the
React frontend, side by side under a single root (`ajiri-backend/`, `ajiri-frontend/`).
Benefits: one clone, one branch and pull request can change API and UI together, CI
can check both (and check that the committed `frontend_build/` matches the frontend
source), and root-level files like CLAUDE.md and SETUP.md are versioned too. Cost:
tools must be told which folder to work in — in workflows that is
`defaults.run.working-directory`, on a server it is `cd ~/ajiri/ajiri-backend`.

How the existing history survived the move: the old repository's `.git` folder was
moved up one level, so every backend file now sits one folder deeper
(`manage.py` became `ajiri-backend/manage.py`). Git detects a moved file with
unchanged content as a RENAME, so `git log --follow <file>` still shows its full
history. A nested `.git` inside `ajiri-frontend/` had to be removed first: a repo
inside a repo is recorded as an opaque pointer, not as files.
