# P5 application pilot readiness and release runbook

20 October 2026. **Preparation only; no live pilot, push, merge or deployment.**
Michael authorized completing local P4b/P4c/P5 readiness and will review the final
batch. Account reset/verification pilot remains independent. This document does
not grant employer contact, broad sending, alert consent, copies or attachments to
an existing account-only transport.

## Current boundary and release decision

P1-P4c implement saved revisions, exact document approval, private send-plan review,
explicit 24-hour permission, withdrawal, shared-ledger mocked dispatch and client receipt
reconciliation. The public dispatch route is **hard disabled**, including when
REAL_EMAIL_ENABLED or an unrecognized APPLICATION_EMAIL_ENABLED setting is true.
It can only return an already-linked receipt. ApplicationPilotTransport is an
injectable guard with no live factory. No environment toggle alone activates it.

After final approval, connecting that boundary requires a small explicitly reviewed
adapter/factory change, including current validated settings and server-advertised
dispatch eligibility. Do not replace the disabled response with an unguarded call
or construct BrevoTransport directly in a view. The supervised first-send package
must use DeliveryService with authorization ID, idempotency key=authorization ID,
exact dispatch_inputs, stable existing digest derivation, ApplicationPilot policy
and ApplicationPilotTransport. Resolve an existing link first, before eligibility
or files. Both the service and last transport boundary must enforce the actual
allowlisted owner/recipient. No alternate API/SMTP/console route is permitted.

No live connector/production/provider checks were done for this readiness artifact.
Readiness below is deliberately not a successful inbox, privacy or deployment claim.

| Gate | Current evidence / required next evidence |
|---|---|
| Local workflow/UI | Automated dummy/fake-transport results in APPLICATION_SEND_CLIENT_REVIEW.md |
| Schema | jobs0009/0010 additive populated-upgrade tests; production migration status uninspected |
| Current production SHA | Recorded894d1eb only; inspect again before pinning release |
| Brevo account security pilot | Historical user-confirmed reset/verification; not an application test |
| Sending domain/sender | Historical setup evidence only; freshly verify authenticated domain and sender |
| Provider serialized limit | UNVERIFIED; record official current limit, date, source and conservative explicit byte ceiling before factory/activation |
| Owner-controlled destination | Privately confirm exact account ID and actual destination; no wildcards, aliases inferred or employer retargeting |
| Suppression | No automated bounce/complaint intake; operator must review provider suppressions immediately before and after each supervised attempt |
| Privacy/retention | Employer contact use, representation, applicant disclosure, Reply-To, provider processing/transfers, support access and AJ-25 erasure/backups need review before broader release |
| Live application send/inbox | NOT RUN; requires final approval and reviewed connection above |

## Narrow supervised operating policy

1. One synthetic applicant/job/application addressed from the outset to an explicitly
   confirmed owner-controlled mailbox. Never replace a real employer's address to
   make a test pass. Use subject prefix `[AJIRI PILOT] ` and clearly synthetic body
   and documents. No real applicant information, certificate or employer contact.
2. Exactly the approved saved CV and saved letter, DOCX only; 2 MiB each/4 MiB raw.
   Freeze filenames and bytes from the plan. The serialized JSON/base64 request must
   fit the freshly reviewed explicit ceiling; a raw4 MiB limit alone is insufficient.
   Validation is not a malware-scan claim. No fetched URLs or on-send regeneration.
3. Copies/CC/BCC off; platform From/Ajiri, verified applicant Reply-To. Exact owner
   and actual destination checks at both boundaries; never widen accounts/pilot.py.
4. One application reservation per Nairobi day within five shared pilot messages,
   including earlier account messages/failures, and existing fixed 200/150/30/20 and
   per-user 10 limits. Failures spend quota; never borrow allocations, refund or
   delete receipts. A single explicit retry may need to wait until another day.
5. Review the plan, independently record unchecked permission, then request dispatch
   explicitly once. Permission alone cannot send. Withdrawal wins until the committed
   reservation/link/dispatch_started cutoff; afterwards recall cannot be promised.
6. If the request times out or response is lost, GET the authorization/receipt. Never
   press a new send to probe the result. Reserved/unknown requires private operator
   reconciliation and stays blocked; no reconciliation write endpoint is provided.
7. Accepted means provider accepted, not inbox delivery/read or website submission.
   Inspect the one synthetic email manually: sender, Reply-To, recipient, subject,
   exact text, two filenames and downloaded attachment SHA-256 values against plan.
   Record receipt category/outcome only; keep addresses/documents/links out of logs.
8. Review provider bounce/complaint/suppression status immediately after the attempt.
   Any bounce, complaint, wrong recipient, content mismatch or ambiguity stops the
   pilot. Keep application dispatch disabled while investigating. Do not infer that
   successful receipt authorizes broad applications or alerts.

## Later approved deployment — PythonAnywhere Bash

These are instructions for a future approved release, not commands executed now.
Replace the release placeholder with the final reviewed full SHA whose required CI
checks pass. Retain the actual currently running SHA/config privately for rollback;
do not assume the historical recorded SHA is still running. Use workon before
strict shell flags (virtualenvwrapper can reference unset ZSH_VERSION).

```bash
workon ajiri
cd /home/Mathenge/ajiri
git status --short
git rev-parse HEAD
git fetch origin
RELEASE='REPLACE_WITH_REVIEWED_FULL_SHA'
git rev-parse --verify "${RELEASE}^{commit}"
git merge-base --is-ancestor HEAD "$RELEASE"
git diff --name-only HEAD "$RELEASE" -- '*requirements*' '*migrations*'
```

Stop for dirty checkout, unexpected ancestry, unreviewed main advancement or
unexpected migrations. Inspect required GitHub checks for the exact release SHA.
The known delta from recorded894d1eb contains only jobs 0009/0010 migrations and no
requirements change. Re-evaluate against actual production at release time.

1. Keep host Force HTTPS and the existing Stage A redirect/HSTS/proxy configuration
   unchanged. Support's scheme guarantee remains a separate unresolved task.
2. Pause ingestion/sweep workflows and disable the web app for the consistency
   window; wait for in-flight writers. These operational actions require the final
   deployment authorization. Do not claim --writers-paused actually stops writers.
3. Make/verify the backup using the **currently running** backup command before
   staging new code. Check private directory ownership0700, remaining account quota
   and file visibility first. Use the Files quota, not shared filesystem df capacity.

```bash
cd /home/Mathenge/ajiri/ajiri-backend
python manage.py backup_private_data \
  --destination /home/Mathenge/ajiri-private-backups --include-media --dry-run
python manage.py backup_private_data \
  --destination /home/Mathenge/ajiri-private-backups --include-media --writers-paused
```

Expected: completed backup directory, complete manifest, verified SQLite integrity
and media inventory. No retention deletion. Verify manifest SHA-256 values and
perform isolated restoration using the existing BACKUP_ROUTINE.md instructions;
download an off-server copy privately. Preserve gzip bytes if the browser downloads
an uncompressed TAR: verify the media_uncompressed hash against that TAR and do not
claim it matches the compressed archive hash. Stop if backup/rehearsal fails.

4. With workers still stopped, stage only the pinned release and review migrations.

```bash
cd /home/Mathenge/ajiri
test -z "$(git status --porcelain)" || { echo 'STOP: local changes'; exit 1; }
git switch --detach "$RELEASE"
cd ajiri-backend
python -m pip check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
```

Expected known unapplied jobs 0009 then0010 only; already-applied ones are absent.
Stop on any unreviewed operation. No pip install is required for this batch because
neither requirements file changed. If actual reviewed requirements differ, preserve
the virtualenv first, then with the same active virtualenv run
`python -m pip install --no-cache-dir --requirement requirements-prod.txt` followed
by `python -m pip check`; that is a separate reviewed dependency delta, not a reason
to reinstall opportunistically.

5. Apply only the reviewed plan while workers remain off; then activate paired code.

```bash
python manage.py migrate --noinput
python manage.py migrate --plan
python manage.py check
git rev-parse HEAD
```

Expected: no remaining migration operations, exact release SHA, no check issues.
Reload/re-enable the web app only after migration success. Account email settings
remain unchanged; application dispatch remains disabled in this release.

6. Verify GET/HEAD /api/health/, login/logout/profile, approved CV/letter downloads,
   private anonymous media403/404, CSRF rejection, package review/approval, plan,
   permission/withdrawal/reconciliation and explicit disabled dispatch without quota.
   Inspect private log permissions, with no bodies/addresses in structured events.
   Resume ingestion/sweep workflows and verify one normal ingestion only after the
   app is healthy; if recovery fails, report which writers remain paused explicitly.
7. Record the verified production SHA/date and actual evidence separately from local
   tests. A later separately approved factory connection/pilot activation repeats
   review, backup, migration-plan inspection and paired acceptance as appropriate.

## Rollback and stop conditions

Keep application dispatch disabled first. Do not disable working account security
email solely to roll back this feature. Pause writers if a code rollback is needed,
then return to a specifically reviewed email-disabled server/client SHA and reload.
Do not roll back to the legacy console/SMTP application sender. Validate compatibility
with retained jobs0009/0010 tables and later writes. Re-run health/auth/private-media
smoke checks before resuming writers. Preserve authorizations, proofs, files,
receipts/links, newer writes and unresolved blockers. Never reverse populated0009/
0010, delete receipts to force retry, or restore the pre-release DB routinely.

If unexpected migrations, bad backup, wrong recipient, failing auth, unsafe proxy,
unreviewed serialized limit, missing sender approval, provider suppression or
ambiguous outcome appears, stop activation, retain evidence privately and report the
specific blocker. A DB repair or irreversible reversal needs its own concrete plan.

Suggested3 points for readiness; actual supervised live pilot remains unexecuted.
Jira-ready: **Prepare owner-only application pilot | AC: reproducible disabled-mode
gates, explicit owner/size/budget/suppression checks, pinned backup-before-migration
release and evidence-preserving rollback runbook; live-send evidence remains open
until final approval and a successful supervised synthetic attempt.**
