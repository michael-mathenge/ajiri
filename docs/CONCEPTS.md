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
of service. Even for email-method jobs, the actual design decision was to
never send silently — every application is drafted automatically, then a
human reviews/edits and hits send. See `application-lifecycle` below for
how that draft → review → sent flow is tracked.

## application-lifecycle
The `Application` model (`jobs/models.py`) tracks one user applying to one
job, moving through four states:
- `draft` — auto-created by the system, CV + cover letter generated, nothing
  sent to anyone yet.
- `ready_for_review` — user has been notified (email/in-app/WhatsApp) that
  a match is ready; they haven't acted yet.
- `sent` — user reviewed (optionally edited) the draft and hit send.
- `dismissed` — user declined to apply to this match.

Two things make this different from the earlier CV/cover-letter generators
(`profiles/cv_generator.py`, `jobs/cover_letter_generator.py`), which build
a `.docx` fresh in memory (`BytesIO`) on every single request:
1. `Application.generated_cv`/`generated_cover_letter` are saved as real
   files on disk (`media/applications/`), generated ONCE at draft-creation
   time — so the document the user reviews is guaranteed to be the exact
   same one that eventually gets sent, not a freshly-regenerated variant.
2. `application_method`/`application_email` are copied ("snapshotted") from
   the `Job` at draft-creation time rather than read live — so an in-progress
   application can't silently change behavior if the underlying job listing
   is edited later.

`unique_together = ('user', 'job')` on the model is the guard against
duplicate drafts, since two different triggers (immediate ingest-check and
the periodic Celery Beat sweep) will both attempt to create Applications
for matching jobs — `get_or_create()` makes this safe.

IMPORTANT: this was later revised — draft creation is now user-triggered
on demand (via an API endpoint), NOT automatic. See `job-alerts` below for
why, and for what's still automatic vs. what's now manual.

## job-alerts
Notifying a user that a new job matches their profile is kept SEPARATE
from Application draft creation, and deliberately runs automatically —
unlike Applications, alerts cost effectively nothing:
- Email: free (just your existing EMAIL_BACKEND).
- In-app: free (just a `Notification` row read by the frontend).
- SMS/WhatsApp (Africa's Talking): NOT free once live — real per-message
  cost, a $35 Sender ID setup fee, and a multi-day approval process. The
  sandbox is free for testing, but nothing is wired to real phone numbers
  yet. Deferred until there's a monetization path to cover it.

Because alerts are cheap, `notify_matching_profiles(job)` (jobs/matching.py)
runs automatically from two triggers:
1. Immediately at the end of each job's ingestion (`ingestion.py`) — so a
   strong match (score >= MATCH_ALERT_THRESHOLD, currently 70%) reaches the
   user right away.
2. A Celery Beat sweep every 6 hours (`sweep_all_active_jobs_for_matches`)
   — catches matches the immediate check would miss, e.g. a profile
   created or edited AFTER a job was already ingested.

`Notification` has `unique_together = ('user', 'job')` for the same reason
`Application` does — both triggers can independently discover the same
match, and this guarantees only one alert ever fires per pair.

Contrast with Application drafts: generating a CV + cover letter and
saving files is real compute/storage cost, so THAT step only happens when
the user explicitly requests it (clicks "Apply"), not automatically just
because a Notification exists. An alert says "here's a match" — it does
not imply a draft has been (or will be) created.