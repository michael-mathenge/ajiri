# Application package roadmap — local final review

20 October 2026. Michael approved completing remaining P4b/P4c/P5 readiness without
intermediate approval pauses. This is the final local batch; no push, PR, main merge,
production action or real message was performed. Production remains recorded at
894d1eb, not freshly verified. Root checkout, existing Docker lesson, uncommitted
AGENTS/lockfile/coverage, stash and Git configuration were preserved.

## Package status and ranges

| Package | Local evidence | Status / suggested points |
|---|---|---|
| Delivery concurrency repair |09b76a1| Previously reviewed; one provider call with bounded receipt-only retries |
| P1 additive package schema |e1e8f94| Previously reviewed;3 |
| P2 select CV/edit/revision |622d639,ae8d05f| Previously reviewed;5 |
| P3 exact preview/document approval |18b7092,9f08327| Previously reviewed;5 |
| P4 approved design |b1bd394| Previously reviewed; no sending activation |
| P4a additive authorization schema |b1bd394..d6b7b1e| Previously reviewed;3 |
| P4b authorization/withdrawal/shared dispatch |d6b7b1e..711872a| Implemented/tested locally;5 |
| P4c UI/final concurrency hardening |711872a..local final HEAD| Implemented/tested locally;5 |
| P5 pilot readiness/runbook |Included with P4c final batch| Documentation ready;3 proposed; live pilot NOT RUN |

Current branch is codex/application-send-client in
`C:\dev\ajiri\.worktrees\application-package-schema`. Resolve the final commit
range using the identity command below; the frontend-build commit is last.

## What the user can do after a reviewed release

Choose an approved CV and draft/edit a job-specific cover letter, save immutable
revisions, review/download exact DOCX bytes, approve those documents, review the
exact outgoing email plan and separately record/withdraw per-application permission.
The system distinguishes permission, dispatch handoff and provider receipt. It does
not infer future-job permission or submit forms on employer websites.

The current web sender remains explicitly disabled. Mocked shared-service dispatch
requires the exact authorization and verifies bytes/payload/current identity/job
again inside the atomic budget reservation. It commits one receipt/link and handoff
before one provider call. Replays only reconcile; unknown outcomes block new sends;
one explicit initial-failure retry costs another slot. No console/SMTP workaround.

## Verification summary

P4b: backend check/drift passed,275 tests/156.140s,OK with one existing Windows
symlink skip. Node 24.19 locked install/lint passed,86 component tests/14 files,
build passed;21 generated files matched existing committed assets.

P4c/final: commands, focused/UI regressions and final outcome details are in
APPLICATION_SEND_CLIENT_REVIEW.md. Current runbook is
APPLICATION_OWNER_PILOT_RUNBOOK.md. Only disposable test DBs were migrated; jobs0009/
0010 were added by earlier reviewed schema packages, no new migration here.

Final results: system check/drift passed; **279 backend tests in141.350s, OK with
one existing Windows symlink skip**; explicit **Node24.19.0**, locked install/lint,
**98 frontend tests/15 files** and build passed. Subsequent build matched all21
generated files (index.html CRLF normalized). New source and generated build are
separate local commits, with the build last. No manual browser/inbox claim is made.

Before handback, verify the nonempty local range and identity:

```powershell
Set-Location C:\dev\ajiri\.worktrees\application-package-schema
git branch --show-current
git status --short
git log --format="%h %ae | %ce" d6b7b1e..HEAD
git diff --check
```

Every new author/committer must equal the configured noreply identity; actual
verification is appended after final commits. Do not amend configured identity.

## Clear remaining release path

1. Michael reviews this finished local batch, test results and manual instructions.
   No action is required between individual local packages.
2. On final approval, explicitly authorize push/PR/merge and the specific disabled
   release/deployment. Pin the CI-green release; pause writers, fresh verified
   backup/off-server copy, stage migration source, review/apply only expected0009/
   0010, then activate paired code and perform manual acceptance. Dependencies did
   not change; no routine pip install is needed. Resume/verify ingestion afterwards.
3. Real application pilot additionally needs a reviewed connection of the currently
   disconnected adapter, freshly verified sender/provider size/owner/suppression
   evidence, privacy/retention review and explicit final live-send approval. Use one
   synthetic owner-addressed job/application, not a real employer destination.
   Configuration alone cannot enable sending in this current release.
4. Run one supervised attempt and record receipt plus independent inbox/attachment
   checks; stop on ambiguity/bounce/complaint. This remains open in Jira rather than
   claiming the live pilot or AJ-17 is Done from passing mocks.
5. Broad employer/alert sending, copies, certificates, alert defaults/consent,
   suppression/webhooks and erasure remain outside this agreed narrow local batch.
   Existing design approvals do not expand the implementation scope automatically.

No fresh Jira writes were performed during this local batch. Each package review
contains a Jira-ready title/acceptance line and honest point suggestion. The HTTPS
scheme/support/HSTS question and web-app renewal remain separate operational items.
