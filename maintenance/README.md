# Maintenance entry point

Start here when maintaining Ajiri. Historical documents describe past decisions;
they are not an instruction to repeat completed work.

| Task | Read |
| --- | --- |
| Find remaining work in order | [Next actions](../docs/ROADMAP_NEXT_ACTIONS.md) |
| Set up or change the application | [Setup](../SETUP.md), [backend concepts](../ajiri-backend/docs/CONCEPTS.md) |
| Deploy or recover | [Deployment checklist](../docs/DEPLOYMENT_CHECKLIST.md), [backup routine](../docs/BACKUP_ROUTINE.md) |
| Investigate an old review or decision | [Single historical reference](HISTORY.md) |
| Manage checkouts and retained work | [Worktrees](WORKTREES.md) |
| Prepare a Jira update | [Jira report files](JIRA_SYNC.md) |
| Find a current technical guide | [Documentation index](../docs/README.md) |

The screenshot's CHECKPOINT/PHASE reviews, CI proposal and superseded design or
decision files were previous delivery records. Their content has been consolidated
into HISTORY.md and their separate files removed. Deployment, design-system,
throttling and upload-validation guides remain maintained references in `docs/`;
there is no second runbook copy here.

Before deleting anything else, establish its owner, references and recovery path.
Keep unfinished code, private configuration, backups, Git configuration and stashes.
Do not interpret a local commit, a merged PR or a successful provider response as
proof of production deployment or inbox delivery.

## Supplemental job browsing

Menu: Django admin > Jobs > **Job browsing settings** > Job browsing settings.
The only editable field is `supplemental_browsing_enabled`, default **off**.
`created_at`, `updated_at`, and `last_changed_by` are read-only. Only active
superusers can view/change settings or view **Job browsing settings audit**.
Audit rows show who, when, old value and new value; they cannot be added, changed
or deleted in admin. Settings cannot be added or deleted there; the database
constraint permits only row 1. Audit insertion and the setting change are atomic.

The additive migration creates one disabled row and never reads/imports the
retired `JOB_FEED_DISPLAY_ENABLED` flag. A leftover True cannot enable browsing.
`JOB_FEED_DISPLAY_FORCE_OFF=True` overrides admin and cached True. Missing rows
and read/cache failures fail closed. Cache reads expire after at most 60 seconds;
successful admin saves invalidate the current worker cache after commit. Allow
up to 60 seconds for other workers and refresh the browser to confirm a change.

### Owner activation and smoke test

Before activation, verify deployed main/CI evidence, a fresh backup with checksum,
private off-server copy and isolated restore, and sufficient disk quota for this
release and the next backup. Do not prune backups or branches. Confirm freshness
remains enforced and every sending/publication flag retains its approved state.
Review SELECT-only counts in the production Python 3.12 environment:

```bash
cd /home/Mathenge/ajiri/ajiri-backend
/home/Mathenge/.virtualenvs/ajiri/bin/python manage.py job_feed_display_counts
```

`supplemental_browsing_window_days` is 14. Unverified rows require posted dates
from exactly 14 days before evaluation through evaluation, inclusive. Null, future
and older dates are excluded. Inactive, scam-flagged, known closed and unexplained
archived rows remain excluded. Expired confirmation is not proof of source closure;
it never grants verified eligibility. `supplemental_browsing_enabled` reports the
effective read. `browse_on` and `browse_off` are hypothetical counts, not activation
evidence; force-off also overrides the hypothetical on query.

Only Michael activates: tick the field, save, inspect the new audit record and
refresh Find jobs after at most 60 seconds. Untick/save to turn off; confirm the
audit and refresh again. The agent leaves production off. Smoke test list, detail,
ordinary keyword search, location/type filters, **Availability not verified**
warnings and **View original listing, availability not verified** links. Links
must reach the HTTP(S) source in a new tab with `noopener noreferrer`. There must
be no application preparation, document generation or sending controls for these
rows. Synthetic tests cover age boundaries, expired jobs and scam exclusion; never
edit production rows to manufacture test cases. Features remaining disabled are
verified synthetically rather than temporarily activated in production.

Supplemental rows are excluded from saved-search matches, in-app notifications,
email alerts, public vacancies, sitemap and JobPosting metadata. Browse skill
scores remain visible but do not verify availability. No email smoke test is
authorized here. Existing application and eligibility rules remain unchanged.

List disclosure: “Some listings are supplemental feed results posted within 14
days. Availability not verified. Check the employer's original listing before
sharing information. Skill match scores describe relevance, not availability.”

### Rollback and admin access

Normal rollback: untick the admin field, save, wait at most 60 seconds, refresh.
Emergency rollback: Michael privately sets `JOB_FEED_DISPLAY_FORCE_OFF=True` in
the hosting environment and reloads. Never relax freshness. Retain job rows,
settings/audit tables and evidence. Leave the admin field off before removing
force-off later. Prefer this rollback to old code which still reads the retired
enable flag; a source rollback requires ensuring that old flag is false first.

Default admin URL: `https://mathenge.pythonanywhere.com/admin/`. Michael may
privately set `ADMIN_URL_PATH` to a non-reserved single segment ending in `/`,
then reload. Do not publish or commit the chosen path. Once set, `/admin/` and
its children return 404. Privately remove this setting/reload to recover the
default route. The release does not choose a custom path for Michael.

Production session and CSRF cookies already default to Secure; session cookies
remain HttpOnly and CSRF protection remains enforced. Preserve HTTPS/HSTS settings.
Admin login POSTs use the existing trusted-proxy IP rules, default 10/minute
(`THROTTLE_ADMIN_LOGIN_RATE`). Hashed counters are shared across host workers in
the private `~/ajiri-admin-login-cache` directory, outside the web checkout.
Counter-storage failure temporarily denies login; GET login stays available.
DRF counters are best-effort throttling, not a strict concurrent-attempt limit or
account lockout system. No provider setting or secret is exposed in admin.

Create/reset a superuser interactively in the hosting Bash console, without email:

```bash
cd /home/Mathenge/ajiri/ajiri-backend
/home/Mathenge/.virtualenvs/ajiri/bin/python manage.py createsuperuser
/home/Mathenge/.virtualenvs/ajiri/bin/python manage.py changepassword <existing-account-email>
```

Run only the appropriate command. Michael enters the real account identifier
privately, replacing the placeholder; passwords use hidden interactive prompts.
Never pass passwords as arguments or capture identifiers/passwords in logs.
This release does not create users or reset credentials.

### General account-security email prerequisites

Michael supplies/approves the sender address/name, verified sending domain and
DNS authentication, Brevo account/domain approval, Brevo credentials entered
privately, and a controlled recipient inbox. Reconcile recorded configuration
and the completed owner pilot before repeating setup. Under separate authorization,
verify verification/reset inbox delivery, correct content/links, expiry, failure
handling, budgets and rollback. Provider acceptance is not inbox confirmation.
Do not activate or send account-security email for this release; application,
alert, saved-search and employer mail remain separate acceptance work.
