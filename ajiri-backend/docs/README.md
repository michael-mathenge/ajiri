# Backend documentation

Ajiri is deployed on PythonAnywhere. The API uses Python 3.12, Django/DRF and
SQLite; Django serves the committed React build. Celery/Redis availability in
local development is not production-worker evidence.

Use the maintained repository entry points:

- [Local setup and checks](../../SETUP.md)
- [Documentation index](../../docs/README.md)
- [Current pending work](../../docs/ROADMAP_NEXT_ACTIONS.md)
- [Backend concepts](CONCEPTS.md)
- [Current release checklist](../../docs/DEPLOYMENT_CHECKLIST.md)
- [Feature activation and rollback](../../docs/BACKEND_ACTIVATION_CHECKLIST.md)
- [Executed release evidence](../../docs/JIRA_ROADMAP_PROGRESS.md)

The former long onboarding guide duplicated setup instructions and incorrectly
said the site was not live and all sending was complete. Its original content is
[retained as a historical snapshot](../../maintenance/HISTORY.md#record-backend-readme-pre-first-release).
`DEPLOY_PYTHONANYWHERE.md` documents initial host provisioning; use the current
release checklist for an existing installation. Real sending, malware scanning,
public publication and other gated services require their own acceptance evidence.
