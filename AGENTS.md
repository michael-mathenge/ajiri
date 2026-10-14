# AGENTS.md

Before doing anything in this repository, read `Ajiri.md` in the repo root in full. It is the source of truth for scope, rules, work packages, quality gates and stop conditions.

Non-negotiables (details in `Ajiri.md`):
- Never commit to `main` and never push. Work on `integration/checkpoint-1` and feature branches off it.
- Run `git branch --show-current` before every commit.
- Do not claim anything passes unless you ran the command. If you cannot run it, mark the work "unverified".
- Do not touch auth/JWT logic, CORS, migrations history, ingestion endpoints, CI or hosting config without asking.
- If `Ajiri.md` conflicts with a message from Michael, follow Michael and flag the conflict.
