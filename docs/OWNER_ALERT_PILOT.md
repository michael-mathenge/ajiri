# Owner alert delivery pilot

Status (21 October 2026): PR31 deployed at40c1ea0. One owner-only synthetic alert
was accepted by Brevo and the owner confirmed inbox receipt and successful
unsubscribe. A read-only production check confirmed the latest event came from
unsubscribe, email preference/eligibility were false and the pilot flag was off.
Opening the link without confirming was not independently reported; automated
coverage checks that no-effect preview separately. No broader delivery is verified.
Normal job-alert
sending and employer-facing application sending remain disabled. AJ-17/AJ-26 are
not complete merely because a synthetic transport test passes.

This package extends the existing owner-only Brevo HTTPS pilot. It adds no new
credentials, SMTP setup, attachment sharing, CC/BCC or employer recipient. The
default ALERT_EMAIL_ENABLED=False does not read provider credentials or claim quota.
When explicitly enabled, the same exact owner ID/current verified email/platform
sender and five-attempt shared Nairobi-day cap remain in force. Security mail and
alerts share the existing ledger and quotas. Provider acceptance is not inbox proof.

The owner must personally choose email job alerts in Profile → Email job alerts →
Save email choice. A stored old preference, deployment approval or administrator
action is not that consent. The address must still be verified. Other users cannot
use the pilot. No such production choice has been inferred or recorded by Codex.

After source/CI/deployment and private configuration review, an operator may set
ALERT_EMAIL_ENABLED=True for the owner-only test. Existing private account-pilot
configuration and credential must remain unchanged. Then in PythonAnywhere Bash:

```bash
cd /home/Mathenge/ajiri/ajiri-backend
python manage.py owner_alert_pilot --prepare
```

Expected: a hidden, inactive synthetic job and email-only notification, no email.
It does not appear in normal job browsing/in-app history and is not a real vacancy.
Use only the reported notification ID after confirming this is the allowlisted
owner recipient; the following command can send one real email to that owner:

```bash
python manage.py owner_alert_pilot --notification-id NOTIFICATION_ID --confirm-owner-recipient
```

No broad sweep or ingestion route can send through this pilot. The final boundary
rechecks configuration, exact owner, synthetic source and current consent after
reservation. A revocation observed at that last check produces a definite no-send receipt; it can
still consume reserved quota. Unknown/reserved/definite-failure receipts are not
automatically retried, even by rerunning the command. Reconcile before any new test.
An accepted receipt is retained/read rather than handed off twice.

Ask the owner whether the email actually arrived; never request its private link.
Opening the unsubscribe link must make no change. Confirming unsubscribe must
disable email while leaving in-app/security mail unchanged; check profile status
and that later pilot attempts are blocked. Record sanitized outcomes only. Restore
ALERT_EMAIL_ENABLED=False when the bounded test ends or any check fails.

The email contains a purpose-signed, address-bound30-day unsubscribe URL in a
fragment. A separate confirmed POST changes preferences; link previews do not.
Both plain text and escaped HTML carry the same message. No raw provider errors,
tokens, recipient identities or message bodies enter application logs.

Broader release still needs reviewed suppression/reconciliation, actual inbox and
unsubscribe evidence, consent eligibility for intended users and application-specific
authorization/attachment/copy checks. No bounce/complaint webhook is claimed here.
Source rollback keeps the ledger, profile choices and existing attempts; disable
the alert flag before rollback and never reset a receipt to repeat an uncertain send.

Provider contract reviewed21 October2026: the [Brevo send API](https://developers.brevo.com/reference/send-transac-email)
documents sender/recipient/content and201 message identifiers; the [attachment guide](https://help.brevo.com/hc/en-us/articles/4402811730962-Add-an-attachment-to-a-transactional-email)
lists20MB total API message size. This alert has no attachments and a64KiB serialized
cap. These provider limits do not expand Ajiri's existing application attachment
policy or prove a particular account's quota/deliverability.
