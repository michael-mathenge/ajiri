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
`../profiles/signals.py` listens for User saves specifically and auto-creates
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
