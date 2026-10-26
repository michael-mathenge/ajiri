# PythonAnywhere showcase â€” 26 October 2026

Verified live runtime: `d91da4752a887bc38429cbb88c3b201c61974a8b` (PR69).
All six checks passed; production health,38 asset hashes, authenticated CV navigation
and an existing private approved-CV download passed. Sending/public jobs remain off.

PythonAnywhere remains the current host, with SQLite and private local media.
A public introduction explains the actual CV workflow before registration. Signed-in
users still land on jobs; `/about` allows previewing the introduction while signed in.
`/employer-guide` explains the reviewed posting process without exposing private data.
These static pages make no account/job API requests. All private routes remain protected.

## Scope and limits

Registration, profile, CV preview, explicit approval and private DOCX download form
the initial demonstration. CV building does not require email verification; application
preparation still requires the existing eligibility and verification gates. Account
security mail remains an owner-only pilot. General application sending is disabled.
There may be no eligible active vacancies; never seed fake vacancies or restore
unverified archived jobs for a demonstration. Public vacancy publication remains off.
No employment guarantee or applicant payment requirement is introduced.

Use [employer review plan](EMPLOYER_REVIEW_PLAN.md) for the next live onboarding step.
Daraja and commercial decisions come last. Wider mail, scanning, queue and storage
services retain their separate operational gates; synthetic rehearsals are not live services.

## Verification and release

Component regressions cover public navigation, anonymous private-route redirects,
signed-in jobs and absence of API calls. Chromium checks phone layout, signed-in
navigation and no mail/ledger effects. Axe covers the new public pages in both themes.
The full registration-to-approved-CV/application journey remains a separate browser test.
Actual command results and release revisions belong in JIRA_ROADMAP_PROGRESS.md.

No schema/configuration changes are required. Verify the private backup receipt,
pass required CI, deploy the merged source and reload the existing WSGI app. Check
public root/about/employer-guide and authenticated jobs/CV access. Roll back to the
previous reviewed source/build and reload; preserve all private documents and records.
