# Feed display options

| Option | Benefit | Limitation |
| --- | --- | --- |
| A: labelled feed listings | Restores discovery without claiming availability is verified | Requires a warning and separation from all application and sending paths |
| B: listings posted within 14 days | Reduces older results | Recency does not prove availability; the board may still be empty |
| C: keep hidden | Preserves the current display policy | No useful discovery when no feed deadlines qualify |

Recommend A for authenticated Find jobs browsing only. Use the exact warning
"Not verified: check the employer's page before applying", the original source
link and posted date (or "Posted date not supplied"). Do not offer application,
document-generation or sending actions on these rows. Keep known closed jobs,
withdrawals, inactive jobs, unexplained archives and scam-flagged rows hidden.

`JOB_FEED_DISPLAY_ENABLED` defaults to False. Michael enables it privately;
`JOB_FRESHNESS_ENFORCED` and all eligibility/sending gates stay unchanged.
There is no age cap under A and no migration. Anonymous pages and sitemaps remain
restricted to eligible jobs. Disabling the setting restores existing browsing.

## Read-only counts

From the repository in PowerShell, using a configured local Python environment:

```powershell
Set-Location C:\dev\ajiri\ajiri-backend
python manage.py job_feed_display_counts
```

Expected: aggregate JSON with one evaluation timestamp, total/scam counts,
eligible count, supplemental candidates, browse totals with the switch off/on,
and candidates posted within 14 days. Missing posted dates are not counted as
recent. Queries do not archive, ingest, notify or send anything.

Production uses the `ajiri` virtualenv, not the system Python. Use its absolute
interpreter so a new Bash console cannot silently select Python 3.13:

```bash
cd /home/Mathenge/ajiri/ajiri-backend
/home/Mathenge/.virtualenvs/ajiri/bin/python --version
/home/Mathenge/.virtualenvs/ajiri/bin/python -c "import celery; print('ok')"
/home/Mathenge/.virtualenvs/ajiri/bin/python manage.py job_feed_display_counts
```

Expected: Python 3.12, `ok`, then aggregate JSON. `workon ajiri` is an equivalent
activation shortcut. A missing Celery import from `/usr/local/lib/python3.13`
means Django failed during settings import before command discovery; do not
install dependencies into the system interpreter to work around it.

## Private activation

`eligible` counts genuine availability evidence accepted by the existing rules.
`supplemental_unverified` counts additional display-only candidates; `browse_on`
is the combined result. Zero eligible jobs does not imply zero browse-only rows.
If `browse_on` is zero, this switch cannot populate the board. Do not change
availability records, deadlines or labels to increase a count.

Michael confirmed on 1 November that clearly warned browse-only rows may be shown
even when `eligible` is zero. Privately edit the existing production configuration
entry to `JOB_FEED_DISPLAY_ENABLED=True`, keep `JOB_FRESHNESS_ENFORCED=True`,
and reload the existing web app. The owner may set that one entry in their own terminal:

```bash
/home/Mathenge/.virtualenvs/ajiri/bin/python -c "from dotenv import set_key; set_key('/home/Mathenge/ajiri/ajiri-backend/.env', 'JOB_FEED_DISPLAY_ENABLED', 'True')"
```

Then use the PythonAnywhere Web tab Reload button. No migration or sending switch is involved.
The code default remains False; this guide does not activate the setting.

Sign in and verify the exact warning, posted date or explicit missing-date text,
original source link and absence of apply/CV/cover-letter/send controls on these
rows. Eligible jobs retain their normal behavior. Set the display entry back to
False and reload to roll back. Production counts and activation remain owner-run;
the command performs SELECT queries only and does not ingest, sweep, notify or send.
