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
