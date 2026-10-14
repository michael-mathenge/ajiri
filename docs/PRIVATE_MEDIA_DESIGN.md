# Private media design — Checkpoint 2 preparation

15 October 2026. **Proposal only; not implemented or deployed.** Base: fetched
`origin/main` at `e5e0038`, containing Checkpoint 1 tip `b8c1881` and WP1-WP6.
No hosting dashboard, production files, database or environment was accessed.
Approval of this document is required before implementation. Prompt 2 has not
been supplied, so no exceptions to standing rules are assumed.

## Current storage and exposure

Repository evidence:

| Data | Model field | Relative storage name / creation |
|---|---|---|
| Uploaded CV | `profiles.models.Profile.cv_file` | `cvs/<uploaded filename>`; default storage sanitizes names and resolves collisions |
| Saved application CV | `jobs.models.Application.generated_cv` | `applications/cvs/<uuid hex>_CV_<company>.docx` |
| Saved cover letter | `Application.generated_cover_letter` | `applications/cover_letters/<same uuid hex>_Cover_Letter_<company>.docx` |

All three use default FileSystemStorage. `config/settings.py` currently sets
`MEDIA_ROOT = BASE_DIR / 'media'` and `MEDIA_URL = '/media/'`. Locally that root
is `C:\dev\ajiri\ajiri-backend\media`. FileField database values are relative
names, not file contents or absolute paths. Existing default DRF FileField
representations expose media URLs in Profile/Application JSON. Preserving these
JSON fields initially avoids a separate API contract change; their legacy URLs
must cease serving bytes. UI blob downloads already use protected endpoints.

`jobs/views.py` prepares application snapshots once with `ContentFile` and
`FieldFile.save()`. Sending email reads the stored attachments; moving storage
must preserve those exact bytes, names and attachment behaviour. A newly generated
CV (`GenerateCVView`) or cover letter (`GenerateCoverLetterView`) is produced in
memory on demand and returned as DOCX, rather than stored by those actions.

`config/urls.py` adds Django's media serving route only when DEBUG is true.
Production already omits that route. The React fallback excludes `media/`.
`ajiri-backend/docs/DEPLOY_PYTHONANYWHERE.md` instructs a mapping from `/media/`
to `/home/YOURNAME/ajiri/ajiri-backend/media`, bypassing Django permissions.
This is documented configuration, not a verified snapshot of the live account.
The runbook's Python 3.13 example is historical; this proposal uses the user's
Python 3.12 environment and does not alter any environment or CI matrix.

Current protected downloads:

- `/api/profiles/me/cv/`: authenticated caller's uploaded CV.
- `/api/jobs/applications/<id>/documents/cv/` and `.../cover-letter/`:
  authenticated owner only; another user's application is 404.
- Fresh document generators remain authenticated DOCX responses.

Saved downloads use `FileResponse`, attachment filenames, and
`Cache-Control: private, no-store`; anonymous requests return 401. Missing files
return 404. The existing auth client, refresh cookies/interceptors, CORS, response
statuses, headers, document contents and endpoint paths must remain unchanged.

## Options and recommendation

| Option | Benefit | Limitation / cost |
|---|---|---|
| A. Dedicated unmapped storage root; remove all direct media serving | Defence against both local debug serving and public hosting mappings; same relative names and owner endpoints | Requires operational copy/verification, storage capacity and manual cutover |
| B. Keep current root; remove DEBUG media route and PythonAnywhere media mappings | Smallest change; no relocation | Future accidental mapping of the repository/media folder reopens exposure; weaker separation |
| C. Randomize every filename, including uploads | Reduces casual guessing | A leaked URL still grants access; requires renaming existing references; not an authorization solution |

Recommend **A**, with B's removal of direct serving. C may be defence in depth,
but is insufficient alone; generated documents already have random prefixes.
PythonAnywhere explicitly warns that files inside mapped directories can be
publicly reachable ([account security guidance](https://help.pythonanywhere.com/pages/SecuringYourAccount)).

Proposed configuration: make the default media storage root configurable using
an absolute `PRIVATE_MEDIA_ROOT` environment value, with an unmapped local default
outside the repo (for example `C:\dev\ajiri-private-media`). Set MEDIA_ROOT to
that private location while retaining existing FileField definitions and relative
names. Do not add a second storage backend or change `.url()` behaviour in this
iteration; keeping MEDIA_URL as a legacy URL prefix does not serve anything by
itself. Remove the DEBUG media route entirely, and keep `/media/` excluded from
the SPA fallback. No web server/static mapping, WhiteNoise directory, symlink or
parent mapping may expose the private root. Public static/frontend assets remain
separate. Future public uploads must use separate, explicit public storage.

FileSystemStorage roots and URL prefixes are separate configuration concepts
([Django storage API](https://docs.djangoproject.com/en/6.1/ref/files/storage/)).
Storage access remains through FieldFile.open/save, preserving owner endpoints
and email attachment access. Configure new files as owner read/write (0600) and
directories as owner accessible (0700) on Linux; verify the web worker can operate
as that account. Permissions alone cannot protect files deliberately mapped by a
web server, so removing mappings is essential.

## Migration and existing data

The recommended default-storage-root change needs **no model/schema migration**
and no database row rewrites: `cvs/...` and `applications/...` stay identical.
Confirm with `makemigrations --check --dry-run` during implementation. Choosing
field-specific custom storage instead could create migration state changes and
would need separate approval. AUTH_USER_MODEL and migration history are untouched.

There is a real **operational data relocation**, even with unchanged DB values.
Never silently move files at application startup or regenerate saved snapshots.
Back up the database and media together while writes are paused. Keep the source
copy for rollback in an unmapped location; removal is a later manual retention
decision. Uploaded replacements/deleted rows can leave orphaned files. Inventory
all regular source files, including orphans, so they do not remain publicly
exposed; report unreferenced files separately without deleting them.

### Proposed management command contract (not available yet)

`relocate_private_media` would support explicit absolute `--source`, `--destination`,
`--dry-run`, `--apply`, `--manifest`, and a read-only `--verify` mode. Dry-run is
the default; apply requires explicit selection. It must not depend on which root
is currently configured for the web app. Example future commands:

```bash
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --dry-run --manifest "$AUDIT/plan.json"
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --apply --manifest "$AUDIT/applied.json"
python manage.py relocate_private_media --source "$OLD" --destination "$NEW" --verify --manifest "$AUDIT/verified.json"
```

These are a proposed interface, not runnable instructions for current main.
Dry-run must not create directories, manifests, files or DB updates; with
`--manifest` it reports where the manifest would be written. Read-only verify
prints results; persist its output manually to a protected audit location if
needed. Apply writes a protected manifest containing relative names, sizes,
SHA-256 checksums and copied/already-identical/error status; no file contents,
tokens or user details. Relative filenames can contain personal information, so
manifests and logs must remain private and uncommitted.

Required safety behaviour:

- Resolve roots; reject identical/nested roots, filesystem roots, symlinks,
  traversal, absolute DB names and paths escaping either root. Do not follow
  symlinks found inside the tree. Refuse a destination known to be inside a
  local static/frontend root; actual host mappings require Michael's inspection.
- Inventory the three FileFields, deduplicate shared names and identify missing
  referenced files and orphaned disk files. Missing references or unsafe names
  prevent a successful cutover; do not fabricate empty replacements.
- Preflight disk headroom and permissions. Copy bytes to exclusive temporary files
  under the destination, checksum and atomically finalize without overwriting a
  different file. Existing identical destination files are safe resumptions;
  different content at the same name is a hard conflict, not a suffix rename.
- Preserve all relative names and content; never use normal storage save collision
  renaming to relocate. Do not update rows, delete source files, or change status.
- Rerun safely after interruption, returning nonzero for any unresolved error.
  Verify the full source inventory plus every DB reference after copy. Pause all
  writers throughout inventory/copy/switch/verification; no best-effort live copy.

## PythonAnywhere manual cutover — Michael only, after implementation approval

Nothing in this section has been performed. Verify the actual clone path, Python
3.12 virtualenv, account and all static mappings before proceeding. Replace
`YOURNAME`, the approved revision, and backup timestamp explicitly. The existing
deployment runbook's public media mapping must not be followed for this change.

1. Schedule a maintenance window. Pause all users/uploads/application preparation,
   ingestion and sweeps, including GitHub Actions/external callers, and stop any
   local workers writing this database/storage. If writes cannot be paused, abort
   relocation. Use your established maintenance procedure; none is introduced here.
2. In Web → Static files, record all existing mappings privately. Remove `/media/`
   **and any aliases/parent mappings** exposing the old media root or planned private
   root. Reload the app, then test a known old URL anonymously: it must not return
   document bytes. Removing a Django route alone cannot defeat this mapping.
   Keep legitimate `/static/` and frontend asset mappings unchanged.
3. In your PythonAnywhere **Bash** console, prepare account-owned private folders:

   ```bash
   cd /home/YOURNAME/ajiri/ajiri-backend
   workon ajiri
   python --version  # must be your approved Python 3.12 environment
   umask 077
   OLD=/home/YOURNAME/ajiri/ajiri-backend/media
   NEW=/home/YOURNAME/ajiri-private-media
   AUDIT=/home/YOURNAME/ajiri-private-backups/checkpoint2-YYYYMMDD-HHMMSS
   test -d "$OLD" || exit 1
   mkdir -m 700 -p "$NEW" "$AUDIT"
   chmod 700 "$NEW" "$AUDIT"
   ```

   Inspect resolved paths (`realpath`) and every Web mapping: neither private
   directory nor any ancestor may be mapped. Never use chmod 777. Verify the web
   worker's account can read/write the new directory; if not, stop for a platform-
   specific permissions review rather than making it world-readable.
4. With writers paused, make a consistent SQLite backup using your established
   SQLite backup procedure (including WAL handling); archive the complete old media
   tree, settings revision and private environment backup under AUDIT. Verify the
   backup can be read/restored. Do not put backups in Git or a mapped folder.

   For the current default `db.sqlite3` location, these Bash commands use SQLite's
   backup API rather than copying a potentially incomplete main file. If the
   configured database differs, stop and substitute its verified location first:

   ```bash
   test -f db.sqlite3 || exit 1
   export AUDIT
   python -c 'import os, sqlite3; from pathlib import Path; src=sqlite3.connect("file:db.sqlite3?mode=ro", uri=True); dst=sqlite3.connect(str(Path(os.environ["AUDIT"])/"db.sqlite3")); src.backup(dst); result=dst.execute("PRAGMA integrity_check").fetchone()[0]; dst.close(); src.close(); assert result == "ok", result'
   tar -czf "$AUDIT/media.tar.gz" -C "$OLD" .
   tar -tzf "$AUDIT/media.tar.gz" >/dev/null
   git rev-parse HEAD > "$AUDIT/revision.txt"
   if test -f .env; then cp -p .env "$AUDIT/environment.backup"; chmod 600 "$AUDIT/environment.backup"; fi
   ```

   Require successful exit status for every command; stop at the first failure.
   An archive listing and integrity check are initial checks, not a restore drill:
   verify recovery in a separate private test directory before cutover.
5. Deploy the separately approved implementation revision in the clone using the
   established deployment procedure. Do not alter auth, CORS, WSGI routing or CI.
   Before reloading, run the proposed command's dry-run; resolve all missing files,
   conflicts, unsafe paths and disk space issues. Then run apply and verify using
   the explicit OLD/NEW paths above. Inspect counts and hashes, not just exit status.
6. In the existing server environment-loading mechanism (the private `.env` beside
   manage.py if that is how your app is configured), set
   `PRIVATE_MEDIA_ROOT=/home/YOURNAME/ajiri-private-media`. Keep DEBUG=False. Existing
   process environment values override `.env`; check the effective value without
   printing other settings or secrets. Protect the environment file with chmod 600.
   Apply owner-only file/directory permissions to copies using the approved command;
   verify future uploads receive those permissions too.
7. Web → Reload. Test known old URLs with GET and HEAD, without credentials and
   while signed in: expect 404 (or host denial), never file bytes, a redirect to
   the file or an SPA 200. Check uploaded CV and both snapshot types. Then test owner
   downloads, another user's access, anonymous requests, new upload/preparation and
   captured-mail attachment generation. Confirm byte hashes and no-store headers.
   Never test delivery against a real employer. Inspect server error logs privately.
8. Reconfirm no mapping exposes OLD, NEW, backups or manifests. Retain unmapped OLD
   and backups for an agreed retention period. Resume writers only after all checks
   pass. Update deployment documentation in the later implementation package.

PythonAnywhere mapping changes require reload and tests through the actual web
server ([static-file instructions](https://help.pythonanywhere.com/pages/DjangoStaticFiles)).
A Django test client cannot validate that platform layer. No mapping changes,
folders, chmod operations, environment edits or command execution above are part
of this documentation-only preparation.

## Required tests before implementation acceptance

Use synthetic data, temporary directories and captured email only.

| Layer | Required assertion |
|---|---|
| Django routing, DEBUG true and false | Existing files requested via `/media/cvs/...`, both application subpaths, and encoded/traversal variants return 404; GET/HEAD never stream private bytes or return SPA HTML as success. Reload URL configuration per setting; override_settings alone can leave cached routes |
| Uploaded CV endpoint | Owner gets original bytes, filename and private/no-store; anonymous 401; profile ownership cannot be supplied by a caller; missing file 404 |
| Snapshot endpoints | Owner gets identical saved CV/letter bytes after profile edits; non-owner 404; anonymous 401; invalid kind/missing file 404; attachment and no-store headers retained |
| New writes and email | Upload and preparation write only under private root; email uses same snapshot bytes with captured backend; no public copy created |
| Relocation | Dry-run changes nothing; no DB mutation; hashes/names preserved; orphans counted/copied; shared references deduplicated; rerun identical files succeeds; conflicting/missing files, traversal, symlinks, nested roots, permission/disk errors fail; interrupted copies resume safely |
| Existing regression suite | Django check, migration drift check, full backend suite; existing frontend install/lint/tests/build gates without packaging or committing a new frontend_build for backend/docs-only work |
| Real PythonAnywhere after manual cutover | Actual known legacy URLs fail anonymously and authenticated, including every old mapping alias; owner endpoint succeeds. Test with cache bypass and inspect response bytes, not status alone |

## Rollback and risks

If verification fails before writers resume, keep maintenance in place. Restore
the previous application revision and root setting so owner endpoints read OLD;
**do not restore public media mappings**. Production's existing DEBUG=False route
behaviour allows this privacy-preserving rollback. Verify owner downloads again.
Do not automatically restore an old DB over newer user records.

If new writes have already occurred, pause them again and reconcile new private
files back to the old *unmapped* root using the manifest/hash safeguards, or keep
the private-root configuration while fixing forward. Avoid a blind reverse move
or deletion. Restoring a backup is a separate destructive operation requiring
approval. Local rollback to older code with DEBUG=True must not re-expose a root
containing personal files; retain the no-media-route protection or keep it offline.

Risks: copies double storage temporarily; filesystem and DB backups can diverge
without a write freeze; old aliases/symlinks or broad parent mappings can defeat
isolation; stale environment values can select the wrong root; permission errors
can break uploads and attachment reads; missing originals cannot be recreated
faithfully. Browser/proxy copies downloaded before cutover cannot be revoked, and
prior public exposure may require a separate incident assessment. This proposal
does not claim to erase previously downloaded copies. Backups and manifests need
their own retention and access controls. No deletion policy is introduced here.

## Preparation verification and approval boundary

This document is based on repository inspection and official platform/storage
documentation, not a production audit. Runtime implementation, relocation command,
new tests and deployment are deliberately pending approval. No auth, CORS, endpoint,
model, hosting, dependency or build changes are included. Approval should resolve
the recommended option, maintenance window, destination root and retention policy
before implementation starts.

Preparation checks run on 15 October 2026 (Africa/Nairobi): Django `check`
passed, `makemigrations --check --dry-run` reported no changes, and all 57 existing
Django tests passed in 51.762 seconds using temporary test storage and captured
email. `git diff --check` passed; a section-by-section comparison confirmed all
eight standing AGENTS sections unchanged. These checks validate the unchanged
baseline, not the proposed privacy implementation. `npm ci` failed with Windows
EPERM unlinking the locked Rolldown native binary. Frontend lint/tests/build were
not run after that failed install; the frontend gate is **unverified**. A failed
clean install may leave node_modules incomplete; stop Ajiri Vite and rerun `npm ci`
before the next frontend session. No dependency manifest or frontend_build changed.

Git identity was checked without changing configuration:
`11541427+michael-mathenge@users.noreply.github.com`. The documentation commit's
author and committer identity must be confirmed in the handback report.
