# Registration to approved CV journey

> Status as of 19 October 2026: document version included on merged main `4b6e99bac4995fd3e36e6fbe1c7e3176383b6214`. Deployment of this document version/package is not verified here. Historical statements/results below are preserved; see AGENTS.md section 4.

17 October 2026. Synthetic test data only. No production writes, mail, applications,
credential changes or pilot allowlist expansion were performed for this review.

## Automated integration journey

`profiles.test_registration_cv_journey` follows real API endpoints with CSRF
enforcement, JWT login/refresh and temporary private storage. It does not use
`force_authenticate` or create the account directly in the ORM. Real sending is
off; verification email is captured with the existing test-only locmem sink.

The journey verifies weak-password rejection, successful registration, automatic
Profile creation, login cookie protection, CSRF bootstrap after login rotation,
verification request/confirmation, profile/skills save without uploading a CV,
explicit draft start, invalid-entry rejection without revision advancement,
revision 2 save, prevention of download before approval, explicit approval consent,
download ownership, private/no-store response, byte-for-byte stored snapshot match,
exact normalized text/order against the saved preview, refresh and repeat download,
logout and anonymous download denial. No Application exists at the end; the only
email attempt is the captured verification. The focused test passed in 2.628s.

Frontend locked install, lint, all 64 tests and build passed on Node 24.19.0. The
build matches the already committed assets. Backend check and migration-drift
checks passed. The first full suite stopped at an existing concurrent pilot-budget
test after 123 tests; that test and this journey then passed together (2 tests,
3.219s). The full repeat passed: 210 tests, 133.369s, one existing Windows symlink
skip. The intermittent concurrency failure remains an open reliability concern;
no delivery code was changed or claimed fixed here. This is an API
integration journey plus component regression coverage, not a single automated
browser journey. Visual navigation, mobile interaction, actual mail delivery and
Word pagination still need manual verification.

## Finding requiring review

Fresh Profile rows currently default both `notify_email` and `notify_in_app` to
True. The first journey run exposed this mismatch with the agreed opt-in direction.
No real alert was sent. The continued test explicitly saves both False, exercising
the existing user preference path rather than concealing the default issue.

Proposed correction: alter both BooleanField defaults to False with an additive
AlterField migration, leaving existing rows untouched. No historical consent may
be inferred. This is a design proposal only: model/migration changes await review.
Separately review whether existing True rows need a consent confirmation workflow.

## Manual browser journey before applying

1. Keep the existing approved CV/account intact. Open a separate private browser
   session. Register using an owner-controlled test address and a new password,
   entered privately by Michael. Expect redirect to Login, no automatic email.
2. Log in, open Profile, record the initial alert checkbox states, switch both off
   and save synthetic headline, summary, location and skills. Do not upload a CV:
   confirm the builder supports users starting from information alone.
3. Open Build and review my CV. Expect no automatic draft until Start my CV.
   Start and verify the copied profile details, then fill synthetic experience,
   education, certification and project data. Leave unused optional sections empty.
4. Leave an added Employer blank and save. Expect validation without losing edits.
   On currently deployed 641cdfb the summary is above the form; the local feedback
   fix makes it scroll/focus automatically after its own reviewed deployment.
5. Correct the field and save. Compare every preview section with the inputs.
   Confirm approval is disabled until review consent is checked. Approve and
   download; compare Word text, order and layout with the saved revision.
6. Edit and save a new revision. Confirm it requires new approval and the earlier
   approved download remains unchanged. Reload only after saving, then log out/in
   and confirm the saved draft and version remain accessible to their owner.
7. Stop before Apply. Do not create applications, send employer mail or turn on
   alerts. A different signed-in owner must not access another user's CV download.

The live owner-only email pilot cannot verify a fresh account: it requires both the
existing approved owner ID and exact recipient. Do not widen the allowlist, reuse
the existing owner's identity or mark a test user verified in the database. The
verification leg above is proven with captured email; a fresh live inbox test
requires a separately reviewed pilot change. Browsing and personal CV preparation
remain available to unverified accounts.

## Status

Local test addition only, pending review. No push or deployment. No schema change.
