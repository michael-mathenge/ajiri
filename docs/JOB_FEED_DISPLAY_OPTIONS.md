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

Once the exact reviewed code is deployed, Michael can privately run the same
`python manage.py job_feed_display_counts` command from the production backend
directory in its existing virtual environment. The command itself performs SELECT queries only. Counts are database snapshots, not evidence of open vacancies.
