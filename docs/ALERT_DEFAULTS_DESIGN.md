# Alert defaults and confirmation design

19 October 2026. D1 proposal only. No defaults, signals, models, migrations,
senders or ingestion behavior changed. Design approval is not implementation or
permission to enable email. Existing True preferences are not consent evidence.

## Current state and recommendation

Profile.notify_email and notify_in_app both default True. create_profile calls
Profile.objects.create(user=instance) without explicit preferences. The existing
matching path uses notify_email and Django mail, then marks sent_email; it does
not require the confirmation evidence proposed here. This gap remains open.

| Approach | Benefits | Limits | Recommendation |
|---|---|---|---|
| A: signal passes notify_email=False explicitly | No migration; covers the existing User post_save path | Direct Profile creation, fixtures, management commands or future paths can still inherit True; not a complete invariant | Narrow interim only if separately approved, with all creation paths audited |
| B: model default=False with additive AlterField migration | Consistent default for ORM/admin and future creation paths | Requires reviewed migration; does not replace consent checks | Preferred permanent fix |

The agreed email default is OFF for new users. Model-default migration must not
run an UPDATE/backfill over existing rows. Existing True and False values remain
as stored; eligibility becomes a separate gate. Never infer past confirmation from
login, mailbox verification, a saved profile or a notification record.

In-app preference is independent. Options are retain its existing default or
change to OFF in a separately reviewed migration. Proposed default for this design:
leave it unchanged until Michael chooses. In-app notifications never imply email
consent. Do not silently synchronize the two preferences.

## Proposed confirmation interface and evidence

On Profile/Notifications, show email alert status as Not confirmed until explicit
confirmation exists. Present frequency/purpose, how matching works, address,
unsubscribe and policy version. Email starts unchecked for new users. Existing
users see their saved preference separately and must deliberately choose email
ON/OFF and confirm; no prechecked consent submission or modal trapping browsing.
Saving unrelated profile details must not count as confirming alerts.

Proposed future authenticated GET/PATCH /api/profiles/me/alert-preferences/ returns
saved preferences plus confirmed/pending status. PATCH requires explicit email
choice and displayed policy version; stale versions return 409 for review. This
is a proposal, not an added endpoint. Use existing auth/CSRF protections unchanged.

Recommend a minimal append-only AlertConsentEvent: owner/Profile link, unique
decision UUID, channel=email_alert, enabled boolean, server timestamp, policy
version, source=in_app or unsubscribe, and keyed digest of the normalized recipient.
No IP, user-agent, raw token or historical inference. Concurrent repeated decision
UUIDs are idempotent. Confirmed latest state must be read consistently with the
preference update. An address change invalidates recipient binding without deleting
history; a policy change requires confirmation only when its reviewed meaning
requires it. No automatic policy migration or acceptance is proposed.

A future send must check active user, verified current address, preference=True,
latest matching enabled confirmation, supported policy version and no suppression
immediately before quota reservation/network delivery. Recheck after queue delays;
withdrawal prevents unsent work. In-app eligibility is evaluated independently.
Old callers must not bypass the shared gate. Until implemented, broad alert email
activation remains blocked; console output must not be treated as inbox delivery.

## Unsubscribe and retention

Offer authenticated one-click OFF in preferences and a purpose-bound signed
unsubscribe link, with a confirmation POST to avoid link-preview GET side effects.
No login/reset/verification token reuse. A valid unsubscribe is idempotent, stops
future alert emails immediately and records withdrawal; it does not stop requested
account security emails or imply application withdrawal. Re-enabling requires a
fresh explicit in-app decision. Expired/invalid links offer the normal preferences
route without account enumeration. No secret tokens in logs or analytics.

Retention for consent evidence, suppression digests and backups needs privacy/legal
review before wider release; collect only evidence needed to explain current
eligibility and past sends. Preserve existing rows during migration and rollback.

## Required tests, release and rollback

Test every profile-creation path defaults email OFF; existing True/False rows stay
unchanged after migration; unrelated saves do not confirm; current-address binding,
policy mismatch, replay/idempotency, independent channels and concurrent preference
updates. Test withdrawal versus queued delivery and reservation, verified mailbox
without consent, suppressed address, unsubscribe replay/expiry and no sensitive
output. Existing notification history must remain readable and unchanged.

Approve exact default/evidence migration first. Future release order: backup,
stage reviewed source, inspect/apply only approved migration, activate all callers
with eligibility gates, then an owner-only synthetic pilot. Mixed old/new writers
must not send until all callers enforce the gate. Rollback disables alert sending
first and retains events/preferences/newer writes; never restore True defaults as
a way to resume sending or reverse a populated evidence table. No Phase C action
activates this design. Acceptance: new-user email OFF and zero alert email without
current explicit consent, including existing users.
