# Managed application pilot

The application route is disabled by default, independently of working account
verification/reset mail. No real employer destination is enabled by this package.
An operator can prepare one inactive synthetic job and blank owner review draft;
it stays outside public jobs, job detail and match sweeps. The owner then selects
an approved CV, edits the synthetic letter/email, saves and approves the exact
package, and separately authorizes its displayed email plan before dispatch.
Saving, previews, document approval and recording permission never send mail.

## Bounded release

The existing account pilot must be valid, with one exact current owner mailbox,
verified sender, HTTPS origin and shared daily limit5. Additional nonsecret flags:
`APPLICATION_EMAIL_ENABLED=False` by default, and
`APPLICATION_PILOT_LIMIT_REVIEW=brevo-api-attachments-2026-10-22` only after the
operator has checked this dated limit review. Do not create/copy credentials.
Activation requires the reviewed source, required checks, verified recovery copy,
owner-controlled recipient and explicit per-application owner action. Keep normal
application and alert sending closed; account-pilot approval is not application
permission. Broader legal/privacy and provider processing review remain open.

Brevo's [API attachment guidance](https://help.brevo.com/hc/en-us/articles/4402811730962-Add-an-attachment-to-a-transactional-email)
was checked22 October2026: transactional API messages are bounded at20MB including
content/attachments. The [endpoint contract](https://developers.brevo.com/reference/send-transac-email)
accepts base64 bytes and filenames. Ajiri is more conservative: exactly two validated
saved DOCX documents, each at most2MiB, aggregate4MiB raw, serialized request6MiB.
No external attachment URLs, CC/BCC, copies, redirects or arbitrary recipients.
Public marketing pages can describe other limits; retain the conservative API
bound and recheck provider guidance before later expansion. A clean DOCX structural
check is not malware scanning; this pilot sends only Ajiri-generated reviewed files.

## Operator preparation

After approved activation, in the existing PythonAnywhere virtualenv:

```bash
cd /home/Mathenge/ajiri/ajiri-backend
python manage.py prepare_owner_application_pilot
python manage.py prepare_owner_application_pilot --create
```

The first command is read-only and says DRY RUN. The second creates or returns the
same hidden blank draft ID. It never changes owner verification, infers consent,
approves a CV/package, authorizes dispatch or sends email. It does not overwrite
an existing changed job, reset a receipt or resurrect a dismissed application.

## Owner journey

1. Sign in and open My applications > the synthetic application > Review application.
2. Choose CV and edit cover letter. Select an already approved CV or first build
   and explicitly approve a synthetic test CV. Use synthetic letter text and keep
   the subject prefix `[AJIRI PILOT] ` and email-body opening:
   `Synthetic owner-only application test. No employer is being contacted.`
3. Save a package revision. Open its saved review, inspect both documents and
   explicitly approve that revision. Downloading/reviewing it sends nothing.
4. Open Review email plan / check authorization status. Confirm the recipient and
   Reply-To are your current owner mailbox, copies OFF and exactly two attachments.
5. If you want this one test email, check its exact authorization statement and
   Record authorization. This still does not send. Withdraw before dispatch if
   you change your mind; permission expires after24 hours.
6. Click Send this authorized application once. Provider acceptance is not inbox
   delivery. Check the receipt after an interrupted response; never resend an
   uncertain action. Confirm actual inbox/attachments privately, without sharing
   links, keys, passwords or private document content in chat.

The initial pilot permits one application attempt per Nairobi day and shares a
maximum of five total messages with account/alert pilots. Failed attempts still
consume allocation. An unknown/reserved outcome blocks a retry; only one separately
reviewed retry of a definite failure is supported, subject to the daily pilot cap.
A repeated HTTP dispatch reconciles the same receipt, including after disabling
the pilot, and never repeats provider I/O. Revocation/configuration changes are
checked again at the final transport boundary.

## Rollback and limits

Disable APPLICATION_EMAIL_ENABLED and reload first; leave account security mail
and all approvals, immutable documents, authorizations, budgets, receipts and newer
writes intact. Do not reverse history or restore an old DB over later writes.
The package adds no migration/dependency. Historical documents are not regenerated.
Employer website submission remains a user action, not automated form filling.
The synthetic pilot is not a public delivery rollout or legal-compliance claim.
