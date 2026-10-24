# From account to application

1. **Register and log in.** Read the draft privacy notice and make the registration
   choice explicitly. Use your own email. Check spam if you requested an account
   security link; a generic success message is not evidence of inbox delivery.
   The current production email pilot is restricted to its configured owner.
2. **Save your profile.** Add contact information and skills. With no skills, Ajiri
   asks you to add them; a match percentage describes shared listed skills and is
   not an employer decision or a restriction on browsing/applying.
3. **Build a CV.** Enter your real experience, education and other details. Save and
   preview; correct errors and read the entire revision. Ajiri must not invent
   qualifications. Approval freezes that revision. Download the approved DOCX;
   later profile edits do not change its saved bytes.
4. **Prepare an application.** Open a job, choose an approved CV and prepare its
   application. In My applications you can save a job-specific package, review its
   actual CV/letter, and approve the exact saved revision. Approval of documents is
   separate from permission to send them.
5. **Choose the next step.** For an employer website, download documents and follow
   the employer's instructions yourself; record external submission only after you
   submitted. For email, review the exact recipient, sender, Reply-To, subject,
   body and attachments before any separate sending authorization. A disabled Send
   control means managed sending is not activated; saving/approval does not send.
6. **Understand receipts.** Provider acceptance is not inbox delivery. An unknown
   outcome needs reconciliation, not another click or automatic retry. Never
   authorize sending information you have not reviewed. Dismiss unused drafts;
   restoring a dismissed application returns saved documents for review and clears
   its former sending permission.

Profile controls for in-app alerts and email alerts are separate. Account password
reset/verification emails are separate from optional job alerts. Do not interpret
an existing checked preference as recorded historical consent.

Keep downloaded CVs private. Direct `/media/` URLs are intentionally blocked; use
authenticated download buttons. For privacy/export/deletion requests, consult
the notice linked at registration/Profile. Draft policy wording is awaiting legal
review, and backup retention means deletion is not an immediate purge of every copy.

Search with job keywords, then narrow location/type if needed. Search relevance
and your skill-match percentage are different: a low match does not prevent an
application. Always read the employer's requirements yourself.

You can optionally install Ajiri from a compatible browser's menu. Offline mode
shows a generic connection message; reconnect for jobs, CVs and account actions.
It does not store private screens/documents or queue submissions. If a connection
fails during an action, check its current receipt/status online before retrying.
Phone installation varies by browser; see [installation guide](PWA_GUIDE.md).

The [managed application pilot](MANAGED_APPLICATION_PILOT.md) is a bounded synthetic
owner test, not general employer email delivery. Other users keep the reviewed
download/external-submission journey while broader sending remains closed.

## Saved searches

The deployed release adds **Saved searches** to navigation and **Save this search**
to job results. Save keywords, location and job type; choose Off, Daily or Every
seven days independently for in-app results and email preferences. Both start
Off. Saving a frequency does not grant email consent or send mail; saved-search
email delivery remains disabled. Profile alert choices still apply.

You can keep ten searches. Each due window collects up to fifty new, currently
eligible jobs; expired or unverified vacancies remain hidden. Checks follow the
existing sweep, so midnight in Nairobi is a window boundary, not a guaranteed
delivery time. Editing starts a new window; removing a search stops its future
checks. See [saved searches](SAVED_SEARCHES.md) for limits and release status.

## Employer vacancies and availability

The reviewed employer workflow is deployed. General employer onboarding still
depends on expanding the owner-only account-email pilot. Open **Post a job**,
submit your organisation, then enter the vacancy, official
application URL and closing date/time. Your current account email must be verified.
A separate staff reviewer checks the organisation and vacancy before publication.
Submitting a form does not publish a job. Refresh review status to see a decision;
use Withdraw when recruitment ends early. Staff use `/employers/review` and record
a reason for each decision. Review does not guarantee an employer's authenticity.

Job seekers pay nothing to browse or apply. A listing shows its source, closing
date and evidence time where available. RSS jobs without reliable availability
evidence are hidden; older evidence is archived even if the link still works.
A temporarily empty list is preferable to presenting unverified jobs as open.
Existing application documents remain available privately after a vacancy closes.
