# Checkpoint 3 plan

Planning only, 15 October 2026. No package below is authorized for implementation yet.
Prepared from clean main at `2d5d175`, also confirmed as the remote main revision.
Production is https://mathenge.pythonanywhere.com: private storage is deployed;
console email delivers no real mail; ingestion/sweeps run through GitHub Actions.
The free web app requires periodic renewal (last recorded expiry: 14 November 2026).
No production or GitHub write action is part of this preparation.

## Candidate packages

### WP11 — Email delivery (8 points)

Branch: `feature/email-delivery`. See [SMTP design](SMTP_EMAIL_DESIGN.md).

- Scope: real application and notification delivery, verified platform sender,
  applicant Reply-To, accurate provider-acceptance tracking, atomic shared quotas
  and bounded alert retries. Preserve application claim/idempotency and 502/retry.
- Likely files: `ajiri-backend/config/settings.py`, `jobs/views.py`, `jobs/matching.py`,
  `jobs/models.py`, a shared delivery service and email/concurrency tests. Paths
  beginning jobs/ are beneath ajiri-backend/. No auth or ingestion endpoint rewrite.
- Migration: additive delivery-attempt/budget records likely required for limits
  shared across workers and channels. No deletion, status-value change or rewriting
  historical sent_email values. Exact schema needs approval before implementation.
- Tests: in-memory backend for recipients, Reply-To, saved attachments and accepted
  counts; mocked failures/timeouts; 502 leaves ready_for_review; overlap sends once;
  atomic cap boundaries, timezone reset, channel reservation and alert preference
  independence. Provider transport tests mock HTTP/SMTP; CI never contacts a provider.
- Risks: provider approval, free-tier reachability, domain authentication, quota
  exhaustion, sensitive attachments entering a third-party processor, uncertain
  delivery after lost acknowledgement. Console success is not delivery evidence.
- Decisions: provider/transport, verified sender, limits and alert retry policy;
  approval of privacy/vendor processing and any additive migration.

### WP12 — Dismissed applications (3 points)

Branch: `feature/application-restore`.

| Option | Benefit | Trade-off |
|---|---|---|
| Restore saved snapshots to review (recommended) | Preserves documents the user saw; no schema change | Old details may need review; cannot reconstruct prior draft status |
| Re-draft within the existing record | Uses current profile/job details | Replaces snapshots; must avoid losing user edits and handle missing/inactive jobs |
| Keep dismissal permanent | Smallest scope | User cannot apply again because user/job is unique |

- Scope: an owner-only restore action, a dismissed/history filter and an explicit
  review step before send. Proposed `POST /api/jobs/applications/<id>/restore/`
  changes dismissed to ready_for_review only when saved documents exist; repeated
  restore of an already reviewable record is a no-op. Sent/draft states return 400,
  missing documents return a clear 400, non-owner 404, anonymous 401. No regeneration.
- Likely files: `ajiri-backend/jobs/views.py`, `jobs/urls.py`, lifecycle tests,
  `ajiri-frontend/src/pages/Applications.jsx` and component tests; verify actual UI
  component paths before implementation. Extend the existing auth client usage.
- Migration: none for recommended option; existing unique user/job rule stays.
- Tests: owner restoration, immutable snapshot bytes, missing files, invalid states,
  repeats, concurrent restore/send/dismiss and review UI; no automatic send.
- Risks/decision: stale documents and inactive job destinations need visible review;
  Michael chooses restoration versus re-draft before building.

### WP13 — Privacy and consent (8 points)

Branch: `feature/privacy-consent`.

**DRAFT — requires legal review. This is engineering planning, not legal advice;
Codex is not a lawyer.** Kenya's Data Protection Act 2019 likely applies to CVs and
contact details. Confirm lawful bases, controller obligations, registration duties
and cross-border safeguards with a qualified reviewer, rather than treating a
checkbox as compliance. See [ODPC consent guidance](https://www.odpc.go.ke/wp-content/uploads/2024/02/ODPC-Guidance-Notes-on-Consent.pdf)
and [data-subject rights](https://www.odpc.go.ke/rights-of-a-data-subject/).

- Scope: lightweight public privacy page linked from registration/profile, covering
  controller/contact, data collected, purposes/lawful bases, employer disclosure,
  PythonAnywhere/email processors and transfers, retention, security, rights and
  complaints. Separate required notice acknowledgement from optional email consent;
  do not bundle marketing with access to the service. Recommend optional email off
  for new users pending an explicit choice; existing users need a separate policy.
- Record on the server: notice version and acknowledgement time; optional consent
  purpose/version, grant/withdrawal and timestamp in a separate consent model linked
  to the existing user. Do not collect IP/user-agent without a specific justified need.
  Profile preferences enforce operational choices; consent history records evidence.
  Do not invent consent for historical accounts or change AUTH_USER_MODEL.
- Likely files: `ajiri-backend/accounts/serializers.py`, registration view/tests,
  separate consent model/migration; frontend Register/Profile/router and privacy page.
- API: proposed registration acknowledgement/version and separate optional choice;
  server owns version validation and timestamps. Existing-user handling must be
  approved before making new registration fields mandatory. No token/cookie changes.
- Migration: additive consent records only; legacy users have no acknowledgement
  until collected. No destructive backfill or automatic change of old preferences.
- Tests: required acknowledgement, invalid version, optional rejection allowed,
  withdrawal, server timestamps, historical accounts, field-keyed errors and mobile
  accessible links/checkboxes. No personal data in fixtures or snapshots.
- Risks/decisions: legal wording, lawful bases, controller contact, processor terms,
  retention, optional-alert defaults and existing-user transition require Michael/legal review.

### WP14 — Account data rights (8 points)

Branch: `feature/account-data-rights`. **DRAFT — legal review required.**

- Scope: compare (A) manual identity-verified export/deletion requests with
  (B) authenticated self-service export and confirmed deletion. Recommend A for the
  initial small pilot, with documented fulfilment and identity verification; B is
  a later capability unless Michael approves it now. Disabled users alone are not
  deletion. Never request account passwords by chat/email as verification.
- Export inventory: user/contact fields, profile/skills/preferences, consent,
  applications and private snapshots, notifications and uploaded CV. Exclude password
  hashes, tokens, other users' information and internal secrets. Authentication rows
  must be considered for revocation/deletion, not exported as live credentials.
  Any generated archive is private, owner-checked and short-lived.
- Deletion inventory: user-owned DB rows/relations, consent/audit retention only as
  legally justified, uploaded CV and generated documents, pending sends and refresh
  tokens. Keep shared jobs/skill taxonomy. FileField cascade deletion does not itself
  remove storage bytes; inventory before row removal and make failures recoverable.
  Stop sends/alerts for pending deletion. Already-sent employer/provider copies
  cannot be recalled; describe recipient requests and provider retention limits.
- Backups: Michael/legal reviewer sets an explicit expiry and access policy. Explain
  delayed removal from encrypted/private backups, prevent operational reuse, and
  maintain a minimal legally reviewed deletion ledger so restores reapply deletions
  before serving traffic. Never claim immediate backup erasure if it is not performed.
- Likely files: accounts/profile/jobs service and permission tests, private storage
  cleanup/export tooling, docs and (only for option B) Profile UI and owner endpoints.
- Migration: possibly additive request/progress records; exact choice is open.
  Actual row/file removal is destructive and requires separate explicit approval.
  Do not change AUTH_USER_MODEL or reverse migration history.
- Tests: owner isolation, complete export/no secrets, shared records retained,
  missing files, partial cleanup failure/retry, token revocation, concurrent sends,
  and backup-restore deletion rehearsal using disposable local data only.
- Risks/decisions: identity verification, self-service scope, irreversible deletion,
  retention exceptions, backup expiry and restore suppression need approval.

### WP15 — Basic monitoring (3 points)

Branch: `feature/basic-monitoring`.

- Scope: built-in Python/Django sanitized error events to the existing server log,
  minimal `GET/HEAD /api/health/`, manual ingestion-failure visibility and an operations
  routine. No paid services, dependency, CI workflow change or production automation.
- Health contract: unauthenticated generic 200 when a bounded DB probe succeeds,
  generic 503 otherwise; HEAD has no body; no-cache; no versions, paths, counts or
  exception text exposed. This tests app/DB reachability, not SMTP or ingestion freshness.
- Likely files: `ajiri-backend/config/views.py`, `config/urls.py`, logging settings,
  backend tests and a manual monitoring runbook. Do not replace auth/CORS logic.
- Log only event category, time, safe correlation identifier and outcome. Never log
  bodies, tokens, headers, email addresses, CV content or personal filenames; raw
  exceptions can contain these too. Console email itself prints messages/attachments:
  restrict log access and flag this existing privacy risk pending real delivery.
- Routine for Michael: each day inspect PythonAnywhere error logs/quota and latest
  ingestion/sweep Actions status; on failure inspect the failed step and sanitized
  server event, without pasting credentials/log bodies. Check expected job freshness
  separately. Check renewal weekly and renew before the dashboard expiry. Use GitHub's
  existing personal Actions notification settings; do not configure them for him.
- Migration: none. Tests: GET/HEAD, DB failure 503, no caching, no secret/error detail,
  representative redaction cases; protected endpoints unchanged.
- Risks/decision: manual checks can miss failures between reviews; approve health
  exposure and assign a human owner/frequency. Monitoring must not make live SMTP calls.

## Housekeeping backlog — list only

- Three harmless private production probe files.
- Inactive production test job and disabled synthetic users.
- Line-ending policy check for `.gitattributes`.

## Recommended order and dependencies

WP13 -> WP15 -> WP11 -> WP12 -> WP14. Privacy/legal and sender processing decisions
precede real mail; monitoring supports delivery diagnosis; WP14 depends on retention
and consent decisions. WP12 can proceed independently after its product choice.
Numbers are stable identifiers, not execution order. Suggested total: 30 points,
subject to splitting WP11/WP14 once provider and deletion options are selected.
Future implementation needs package branches, section 7 gates, tests and concepts
updates. Regenerate frontend_build only at the end of each future frontend package.
Deployment compatibility is backup -> migrate -> activate code, with additive schema
remaining compatible with the preceding code. No deployment is authorized here.

## Audit impact

See [read-only modernisation audit](MODERNISATION_AUDIT.md) and the consolidated
[decision form](DECISIONS_NEEDED.md). No findings authorize application changes.

- Add a proposed WP16 `feature/security-baseline` (8 SP, split after approval):
  configured password validation, content-aware uploads, abuse controls and explicit
  cookie-auth CSRF/inactive-account review. Auth/CORS changes require separate approval.
- Add proposed WP17 `feature/account-recovery-verification` (8 SP): anti-enumerating
  password reset, mailbox verification and unverified-account restrictions. Real
  employer mail depends on verified identity, not merely working SMTP.
- Put P0 security/legal/backup/advisory verification ahead of public onboarding.
  Revise sequence to WP16 and WP13 planning first; WP15 next; WP11 owner-inbox-only
  delivery enables WP17; only then permit general real sending. WP12 is independent;
  WP14 follows approved rights/retention policy. Resolve provider/send dependency with
  a controlled recipient pilot, not by sending to unverified employers/users.
- Expand WP11 acceptance to bounce/complaint suppression, attachment budget, receipt
  copies, metadata retention, accurate notification flags and an operator disable gate.
  WP15 must cover console log sensitivity, manual backup/restore verification and renewal.
- Propose later query-count/scaling and reproducible-packaging maintenance; no index,
  dependency, CI or ingestion change is authorized now. Python vulnerability scan and
  coverage remain UNVERIFIED/unmeasured; npm audit returned zero advisories today.
- The earlier 30-point total excludes WP16/WP17 and expanded SMTP requirements; revised
  minimum is 46 SP before splitting/re-estimation, not a commitment to fit one sprint.

## Decisions Michael must answer before building

1. Gmail SMTP for a pilot or Brevo HTTPS delivery? Recommend Brevo, subject to
   provider approval and acceptance of API transport; Gmail reachability remains unverified.
2. Approve platform From plus applicant Reply-To? Which verified sender/domain
   will you configure privately? Do not send credentials to Codex.
3. What platform daily/per-user caps and application-versus-alert allocation apply?
   Approve bounded alert retries only after definite failures, with no ambiguous retry?
4. Restore saved applications to review or regenerate? Recommend saved snapshots.
5. Who reviews the draft notice/lawful bases, and what controller contact is published?
6. Should new-user optional email alerts default off, and how do existing users confirm choices?
7. Manual verified rights requests or self-service? What active-data, export-archive,
   provider and backup retention periods and deletion exceptions are approved?
8. Approve the order, additive migrations in principle and dependency-free monitoring?
   Exact migration designs and destructive actions still need separate review.
