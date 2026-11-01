# Jira report files

`reports/status_report_YYYY-MM-DD.md` is the human-readable progress report.
It records only work since the previous report, including evidence, limitations
and work needing a ticket. The same-day 1 November baseline is preserved under
`evidence/` so a later report does not repeat its updates.

`reports/status_updates.json` is a local review queue, not an application setting.
It contains an array of `{ "key", "status", "comment" }` objects. Status is exactly
`To Do`, `In Progress` or `Done`. Only evidenced new ticket progress belongs here.
An empty array means no new Jira updates. Work without a verified key stays in
the report under "Needs a ticket".

`.jira_sync_state.json` is the local deduplication cache. Its hashes record updates
already applied by the sync tool. Preserve it: deleting it can allow repeat comments.
It is not a credential file. Both JSON files are ignored by Git and are not needed
by the website. Do not edit the cache to pretend an update was applied.

From the repository root in Michael's own configured terminal:

```powershell
Set-Location C:\dev\ajiri
python tools/jira_sync.py --file reports/status_updates.json
python tools/jira_sync.py --file reports/status_updates.json --apply
```

Review the first command's proposed updates before running the second. The dry-run
can contact Jira; the apply command can change statuses and add comments. Private
configuration stays private. The agent does not run either command under AGENTS.md
section 13 and does not modify the sync script.
