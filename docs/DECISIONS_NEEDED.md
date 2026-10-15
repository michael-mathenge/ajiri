# Decisions needed — Checkpoint 3

Choose A/B/C (or D where offered) in the Answers block; add brief notes where requested.
No answers have been selected. Recommendations are advice, not your decisions.
**Defaults are planning assumptions only: silence never authorizes implementation,
protected auth/CORS changes, dependencies, migrations, deletion, production or GitHub writes.**
If a required identity/legal fact is missing, the affected rollout stays blocked.

Sources: [plan](CHECKPOINT3_PLAN.md), [email design](SMTP_EMAIL_DESIGN.md),
[read-only audit](MODERNISATION_AUDIT.md). Privacy items are DRAFT requiring legal
review; Codex is not a lawyer. Never put credentials in this form. Public sender/domain
and contact details are configuration facts, not requests for passwords or keys.
WP16/WP17 are new proposals from Audit impact, not approved work.

## SMTP

### D1 — Which transport/provider?
Why: free-tier outbound restrictions determine feasibility.
A: Brevo HTTPS (free quota, adapter/provider approval). B: Gmail SMTP pilot (built-in
backend, current PythonAnywhere exception unverified). C: defer real email (console
must not be presented as delivery).
**Recommend/default:** A for planning; no activation until verified. **Blocks:** WP11, WP17 rollout.

### D2 — Do you own/control a sending domain and its DNS?
Why: authenticated From identity needs SPF/DKIM/DMARC and verified sender rights.
A: yes, domain/DNS under my control (supply public domain, provider setup manual).
B: only a verified mailbox, no domain (limited pilot, provider From restrictions).
C: neither/unknown (block real sending until identity is established).
**Recommend:** A if true; otherwise B pilot. **Default:** C, never infer ownership. **Blocks:** WP11.

### D3 — Which sender model?
Why: delivery alignment and employer trust.
A: verified platform From + applicant Reply-To (clear platform identity).
B: per-user mailbox OAuth/delegation (new security/dependency scope).
C: manual user-side email only (less automation, no server delivery claim).
**Recommend/default:** A; never spoof arbitrary user From. **Blocks:** WP11; platform support
Reply-To/public sender address must be supplied before rollout.

### D4 — Initial sending budgets (all channels/copies count)?
Why: abuse and provider caps; atomic reservations need explicit ceilings.
A: pilot 5/user/day, 2/user/hour, 50/platform/day, 20 reserved for applications.
B: pilot 10/user/day, 3/user/hour, 100/platform/day, 40 reserved for applications.
C: custom limits (give four numbers after provider review).
**Recommend/default:** A, Nairobi daily window, below provider cap; caps must also fit
provider reset windows. **Blocks:** WP11 quota design.

### D5 — Behaviour when a cap is reached?
Why: silent loss versus queued load.
A: applications 429/reviewable with retry hint; alerts pending at most 24h, no burst catch-up.
B: applications 429; discard email alerts over cap, retain in-app alerts.
C: durable queue for both (new scope/scheduling and migration design).
**Recommend/default:** A. **Blocks:** WP11.

### D6 — Retry definite versus uncertain failures?
Why: accepted mail may lose its acknowledgement; exactly-once SMTP is not guaranteed.
A: applications manually retry definite 502 failures; alerts up to 3 attempts, minimum
1h apart within 24h; uncertain outcomes held for manual reconciliation.
B: no automatic alert retry; manual reconciliation only (simpler, more lost alerts).
C: durable provider-idempotent delivery redesign (separate status/schema proposal).
**Recommend/default:** A, preserve existing 400/502 claim behaviour and never auto-retry
uncertain acceptance. **Blocks:** WP11; ingestion service changes still need scope approval.

### D7 — Bounce and complaint handling?
Why: protect sender reputation and stop unwanted mail.
A: manual provider-dashboard review daily during pilot; immediate suppression of
confirmed hard-bounce/complaint destinations, soft failures follow D6; no new webhook.
B: signed provider webhook + suppression records (more automation/testing/security scope).
C: defer all real sending until B is built (slower, no manual gap).
**Recommend/default:** A for tightly controlled pilot; general release needs reliable
suppression and a named reviewer (Michael unless reassigned). **Blocks:** WP11 rollout.

### D8 — Send an application copy to the applicant?
Why: extra cost and another sensitive attachment copy.
A: no email copy, show confirmation/history in app. B: opt-in separate receipt without
attachments (uses quota). C: opt-in separate full copy (privacy, size and quota costs).
**Recommend/default:** A; never silently CC/BCC. **Blocks:** WP11 composition/quota.

### D9 — Attachment limits?
Why: upload size is not the same as generated-document/provider message size.
A: 5 MB combined raw generated attachments plus conservative encoded-message check
against selected provider limit (reject before claim/delivery).
B: 10 MB combined, conditional on verified provider/worker budget (higher mobile cost).
C: manual external application above a lower custom ceiling (supply size).
**Recommend/default:** A; no public attachment URLs, preserve saved documents on rejection.
**Blocks:** WP11; exact provider cap must be verified before implementation acceptance.

### D10 — Email attempt metadata and retention?
Why: troubleshooting versus personal-data minimization.
A: outcome/timestamps, opaque application/user reference and provider message ID for
30 days; no body, attachment, address or raw error; anonymized aggregate counts after.
B: same for 90 days (longer diagnosis, more retention). C: legal-review custom period
and fields (state minimum needed; no credential/content logging).
**Recommend/default:** A subject to legal approval; suppression data has its own D25 policy.
**Blocks:** WP11 schema, WP13/WP14 retention.

### D11 — Safe production rollout and outage control?
Why: console can falsely report success; accidental employer email cannot be recalled.
A: disabled by default -> allowlisted Michael-controlled inbox with synthetic docs ->
small verified-user pilot -> general release after review, operator disable retained.
B: owner-inbox pilot only this checkpoint (general release deferred).
C: defer live email entirely.
**Recommend/default:** B until security/legal/account gates pass; server operations
remain Michael-only under separate approval. **Blocks:** WP11 rollout, WP17 delivery.

### D12 — Provider adapter/dependency approach?
Why: dependency budget versus transport maintenance.
A: Django-compatible standard-library HTTPS adapter, mocked transport (no new dependency).
B: propose Anymail/official SDK with cost/security rationale before installing.
C: Gmail built-in SMTP only, conditional on D1/connectivity.
**Recommend/default:** A for Brevo; B needs separate dependency approval. Finite timeout
proposed 10s, subject to worker verification. **Blocks:** WP11 implementation design.

## Accounts

### D13 — Password reset capability?
Why: recovery without leaking whether an address exists.
A: built-in Django token primitives + generic response, single-use/expiring link,
rate limits, new-password validation and refresh-token revocation after reset.
B: manual identity-verified recovery initially (human workload; never ask for password).
C: defer recovery and keep public onboarding closed.
**Recommend/default:** A design, proposed 1h token expiry. **Blocks:** WP17, public readiness;
real reset email requires D1/D11 and tokens never enter logs/chat.

### D14 — What may unverified accounts do?
Why: prevent using another person's email as applicant identity/Reply-To.
A: browse/edit profile; block employer sending and email alerts until verified.
B: block all authenticated features until verified (stronger gate, worse onboarding).
C: invite-only pilot with manual ownership verification (temporary operational burden).
**Recommend/default:** A, expiring single-use verification links (proposed 24h), generic
resend response/rate limits. **Blocks:** WP17, WP11 general sending.

### D15 — How do existing accounts transition to verification?
Why: historical registration proves no mailbox ownership.
A: mark unknown, prompt verification; preserve data and block email until verified.
B: manually verify an explicitly reviewed pilot list (no blanket grandfathering).
C: defer rollout until migration/communication strategy is reviewed.
**Recommend/default:** A design; additive separate verification records, no change to
AUTH_USER_MODEL, no invented historical proof. **Blocks:** WP17 migration/rollout.

### D16 — Disabled/deletion-pending accounts and sessions?
Why: custom refresh lacks an activity lookup; matching iterates inactive profiles.
A: stop refresh, revoke refresh sessions, suppress alerts/sends; existing short access
tokens rejected by current active-user checks; add concurrency/regression coverage.
B: design immediate revocation of all access tokens too (new mechanism/scope).
C: hold account changes/public rollout until a separate auth design is reviewed.
**Recommend:** A design. **Default:** C until protected auth changes are expressly approved.
**Blocks:** WP16/WP17, WP14, public readiness.

## Privacy — DRAFT, legal review required

### D17 — Who owns wording, lawful bases and processor/transfer review?
Why: checkbox implementation cannot establish legal compliance.
A: Michael drafts with qualified legal reviewer approving before release.
B: qualified reviewer supplies text, Michael implements as controller contact.
C: reviewer not selected; draft only, public onboarding held.
**Recommend:** B where available. **Default:** C. **Blocks:** WP13, real-user rollout, vendor use.

### D18 — Controller and rights/support contact to publish?
Why: users need an accountable party and usable request channel.
A: Michael as controller with a monitored dedicated contact (provide public details).
B: named organisation/controller and monitored contact (provide public details).
C: undecided; do not publish invented details.
**Recommend:** accurate A/B as legally reviewed. **Default:** C. **Blocks:** WP13, WP14.

### D19 — Registration acknowledgement and optional processing?
Why: preserve free choice and distinguish acknowledgement from consent.
A: required versioned notice acknowledgement; separate unchecked optional email choice;
server records version/time/purpose and grant/withdrawal, no IP/user-agent by default.
B: acknowledgement only; disable optional email until consent UI is approved.
C: legal reviewer specifies an alternative lawful-basis/choice model before coding.
**Recommend:** A subject to legal review. **Default:** B for planning until wording approved.
**Blocks:** WP13, WP11 alerts; schema must stay additive and not fabricate old consent.

### D20 — Existing users' notification preferences and notice transition?
Why: current default-true preference is not proof of informed consent.
A: prompt acknowledgement and explicit email choice; pause optional email until confirmed.
B: invite-only re-confirmation manually before email rollout (human work).
C: hold rollout until legal transition policy supplied; never silently infer agreement.
**Recommend:** A. **Default:** C until reviewed; no automatic preference backfill.
**Blocks:** WP13 transition, WP11 general alerts.

### D21 — Rights fulfilment: manual or self-service?
Why: identity checking and destructive operations need reliable handling.
A: documented manual verified requests for pilot (Michael owns queue).
B: authenticated self-service export + manual deletion (partial automation).
C: self-service export/deletion with explicit confirmation and recovery workflow (larger scope).
**Recommend/default:** A design, not authorization to delete. **Blocks:** WP14, rights readiness.

### D22 — Deletion scope and failures?
Why: DB cascades leave files; employers/backups retain independent copies.
A: remove user-owned DB/private media, revoke sessions and stop pending sends;
retain shared jobs/taxonomy, minimal legally justified ledger, backups expire by D25.
B: temporary deactivation followed by A after a reviewed grace period (state duration).
C: legal reviewer specifies retention/hold exceptions before destructive design.
**Recommend:** A subject to legal review. **Default:** C; deletion requires separate explicit
approval, including partial-file failure/retry design. **Blocks:** WP14.

### D23 — Export format and availability?
Why: portability, document access and risk of lingering archives.
A: private ZIP containing JSON and original CV/application files; 24h maximum lifetime,
owner-only authenticated retrieval, no tokens/hashes/secrets or other users' data.
B: JSON/CSV data plus separate existing owner downloads (less archive/storage complexity).
C: manual private delivery in reviewer-approved format (more operator work).
**Recommend/default:** B for manual pilot; A for later self-service. **Blocks:** WP14.

### D24 — Active-account/inactive-data retention?
Why: saved CVs/applications currently persist without an expiry policy.
A: retain while active, notify after 12 months inactivity then allow 30 days to export
before approved deletion (needs legal review and operational tooling).
B: shorter custom lifecycle (state period, notice and enforcement owner).
C: legal policy not decided; no automatic purge and no public retention promise yet.
**Recommend:** legally reviewed A or B. **Default:** C; flag unresolved before public release.
**Blocks:** WP13 policy, WP14 deletion automation.

### D25 — Backup, suppression/provider retention and exceptions?
Why: deletion claims must match recoverability and processor policies.
A: rolling 30-day private backups; restore replays minimal deletion/suppression ledger
before reopening; provider retention minimized and documented, legal holds explicit.
B: 90-day backups with same controls (greater recovery window and privacy exposure).
C: reviewer defines periods/holds, suppression lifetime and provider deletion constraints.
**Recommend:** A if legally appropriate; suppression held only as long as necessary to
prevent prohibited resends, reviewed separately from D10 attempts. **Default:** C pending
review. Never promise immediate backup or employer-copy erasure. **Blocks:** WP13/WP14/WP11.

## Product

### D26 — Dismissed applications: undo, re-draft or final?
Why: unique user/job row prevents starting a second application.
A: restore saved snapshots to review, no auto-send (recommended existing plan).
B: regenerate within record after explicit warning (may replace user-approved content).
C: final dismissal (simple, no second application).
**Recommend/default:** A design; specify inactive/missing-document behaviour in D27.
**Blocks:** WP12.

### D27 — Restore stale/inactive applications or missing documents?
Why: restoring must not silently send outdated content or regenerate snapshots.
A: restore when files exist, warn on stale/inactive destination and require review;
block send where destination no longer usable, missing files return clear 400.
B: allow restore only for active jobs with intact files (stricter, fewer recovery paths).
C: route such records to explicit re-draft/manual external process (larger UI scope).
**Recommend/default:** B for initial scope; amend prior WP12 proposal if selected.
**Blocks:** WP12 acceptance.

### D28 — Public SEO/PWA/cache work now?
Why: audit found shared metadata/no offline shell/no shared fetch cache; private caching is risky.
A: defer public SEO/PWA; measure mobile transfer first, no persistent private cache.
B: add public-job discovery/metadata design only (auth/product scope changes).
C: offline public shell design only, never private CV/token caching (new scope).
**Recommend/default:** A. **Blocks:** optional P2 backlog only.

## Operations

### D29 — P0 password, CSRF and abuse-control package?
Why: configured validators are bypassed, refresh is CSRF-exempt and throttles are absent.
A: approve separate WP16 design covering validator enforcement, explicit login/refresh
CSRF/origin policy, per-endpoint limits and active-account tests; then approve exact changes.
B: prioritize validators/uploads while commissioning auth threat review; public rollout held.
C: defer all code and keep onboarding closed pending review.
**Recommend/default:** A design only. Auth/CORS/interceptor changes remain protected;
no framework default or SameSite alone is accepted as a complete CSRF policy.
**Blocks:** WP16, P0 real-user release.

### D30 — HTTPS/HSTS/header policy and access-token storage?
Why: deploy checks warn W004/W008; live proxy/headers unverified; localStorage is XSS-readable.
A: Michael manually verifies HTTPS/proxy/cookies, then short HSTS without preload or
subdomains; plan CSP report-only and token-storage threat review without rewriting auth.
B: review at hosting layer first, keep app policy changes deferred and release gated.
C: request dedicated security design before any hardening choices.
**Recommend/default:** A design; never enable redirect behind an unverified proxy.
**Blocks:** WP16 deployment readiness; any server work remains Michael-only.

### D31 — Content validation: keep legacy DOC?
Why: current extension/5 MB checks accept disguised content; signatures are not malware scanning.
A: PDF/DOC/DOCX with signature/container + safe ZIP limits; no malware-free claim.
B: PDF/DOCX only, reject legacy DOC (simpler but changes accepted user formats).
C: propose external scanning/dependency separately (privacy/cost/approval required).
**Recommend/default:** A to preserve current format support; implementation feasibility
must be checked, with approval before dependencies or format removal. **Blocks:** WP16 uploads/P0.

### D32 — Python advisory scan and patch maintenance?
Why: pip-audit absent; pip check is not a vulnerability scan; packages are outdated.
A: Michael provides/runs pip-audit separately, triage findings and plan focused patch PRs.
B: approve a separate tooling/dependency proposal first; no installs now.
C: defer scan and keep public-release gate unresolved.
**Recommend/default:** A as a verification request, never infer scan passed.
**Blocks:** P0 vulnerability verification; future maintenance scope.

### D33 — Monitoring ownership, health endpoint and logs?
Why: no health/error tracking; console mail exposes content in private logs.
A: Michael checks logs/quota/Actions daily, renewal weekly; generic public GET/HEAD
health checks DB only, sanitized events, no paid service/dependency; review log retention.
B: same manual routine, authenticated health only (less useful external probing).
C: propose free external monitoring separately (data sharing/permissions need approval).
**Recommend/default:** A design; log retention follows D10/D25 legal review, no raw mail
content in new application logs. **Blocks:** WP15; public readiness needs named owner.

### D34 — Backup ownership and recovery evidence?
Why: checklist exists, current schedule/off-host copy/restore evidence is UNVERIFIED.
A: Michael performs private daily backup while writes occur, before every deployment,
weekly off-host copy and monthly disposable restore rehearsal, retention per D25.
B: same manual minimum plus separately designed automated backup (hosting scope).
C: propose alternative recovery objectives/owner before public release (supply targets).
**Recommend/default:** A planning baseline, never authorization for server/file operations.
**Blocks:** P0 operational gate, WP14 retention, deployment readiness.

### D35 — Coverage/E2E/accessibility and performance follow-up?
Why: coverage tooling absent, no browser/a11y gate; static evidence suggests N+1/scaling gaps.
A: targeted security/query-count/concurrent-draft tests and manual keyboard/mobile
smoke first; measure latency/query counts; defer new test dependencies until proposal.
B: propose coverage + E2E/a11y tools now, with dependency/CI approval separately.
C: commission a larger test/load study before feature work (slower, stronger evidence).
**Recommend/default:** A; query/index/chunking designs follow measurement, no ingestion
rewrite approved. **Blocks:** WP16 acceptance and later performance backlog.

### D36 — Packaging/schema/housekeeping scope?
Why: packaging uses npm install; no API schema/versioning policy; production probes remain.
A: defer as listed backlog; retain /api compatibility, exact build guard and LF scope.
B: separate maintenance design for npm ci packaging, docs-first API/error contract and
measured indexes (new branch/estimate, no production cleanup).
C: prioritize B after P0, separately request manual fixture cleanup later.
**Recommend/default:** A this checkpoint; no CI changes/dependencies/cleanup authorized.
**Blocks:** optional P1/P2 backlog only.

### D37 — Approve revised order and migration boundary?
Why: audit expands original 30-point proposal to at least 46 before SMTP re-estimation.
A: WP16/WP13 design -> WP15 -> WP11 controlled inbox -> WP17 -> reviewed real-mail
release; WP12 independent, WP14 after rights/retention approval; split into smaller sprints.
B: only P0 security/privacy + monitoring first; defer email/restoration/rights automation.
C: return for a smaller revised plan before any building.
**Recommend:** B for manageable next sprint. **Default:** C until explicit approval.
Any additive consent/verification/budget/request migration needs exact schema review;
no AUTH_USER_MODEL change, destructive operation or historical backfill implied.
All changes must support backup -> migrate -> activate code; no new dependency, CI,
ingestion or hosting change without separate approval. **Blocks:** checkpoint execution.

## Answers

Copy this block and enter option letters plus necessary non-secret notes. Leaving a line
blank leaves it unanswered; recommendations have not been preselected.

```text
D1:
D2:
D3:
D4:
D5:
D6:
D7:
D8:
D9:
D10:
D11:
D12:
D13:
D14:
D15:
D16:
D17:
D18:
D19:
D20:
D21:
D22:
D23:
D24:
D25:
D26:
D27:
D28:
D29:
D30:
D31:
D32:
D33:
D34:
D35:
D36:
D37:
```
