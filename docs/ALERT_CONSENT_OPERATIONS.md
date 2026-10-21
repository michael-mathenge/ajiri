# Alert choice and unsubscribe

The email preference defaults OFF only for newly created profiles. Migration
profiles.0007_alert_consent changes the model default and adds consent evidence;
it does not rewrite existing preference values or infer historical consent.
In-app defaults and existing notification history remain unchanged.

Owners use Profile → Email job alerts → Save email choice. This records the
explicit choice, channel, server time, policy `job-alert-email-v1`, source and a
keyed fingerprint of the current email address. No IP, browser header or raw email
is added to that evidence. Repeated decision keys cannot reverse newer choices.
Ordinary profile saves cannot grant email consent. Old tabs must reload; their
legacy notify_email payload receives a field-specific400 rather than silent success.

Delivery eligibility requires an active owner, current verified mailbox, enabled
preference and latest matching positive consent evidence. Reservation rechecks the
database evidence under the writer transaction. Unsubscribe after provider handoff
cannot recall mail already handed off. A future send integration must also apply
provider suppression/bounce/complaint rules before expanding delivery.

Unsubscribe tokens are purpose-signed, address-bound and expire after30 days.
The future email URL uses `/unsubscribe#token=...`; fragments are not sent as URL
query strings to the server. Opening the page or previewing a token never mutates
preferences. The owner explicitly confirms a POST; no login is required. Repeated
confirmation leaves email off and in-app/account security mail unchanged. Changing
the account address invalidates an old unsubscribe link. Do not place tokens in logs.

The earlier console-mail alert function is disabled. Notifications never claim
email acceptance merely because console output succeeded. Real alert transport
remains disconnected pending the shared-ledger owner pilot; no live mail was sent
by this package. This does not complete broader application/alert sending AJ-17.

Deployment: fresh verified paused-writer backup, stage reviewed source, inspect the
exact plan (only profiles.0007 expected), migrate, activate the matching server/client
pair, then verify new defaults, unchanged old values and independent preferences.
No pip install is needed. Keep public email sending disabled.

Rollback must preserve the consent table/evidence and new account choices. Do not
reverse the schema or restore an old database over newer writes. An old sender can
ignore consent and misreport console mail: disable email matching/sweep invocation
before any rollback to such source. Prefer a forward repair; retain all in-app data.
