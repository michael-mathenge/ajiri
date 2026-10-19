# Phase C UI polish and download names

19 October 2026. C3, local only; no deployment or schema change.

The existing empty-skills branch now uses the exact text "Add skills to see
matches". True zero scores remain visible when skills exist; failed/unknown
profiles do not imply no skills. FormErrors maps known keys to readable labels,
capitalizes fallback labels, spaces field groups and displays each message as its
own list item. Existing field error IDs/associations remain unchanged.

## Download naming decision implemented

Previous behavior mixed Ajiri_CV.docx, generic browser fallbacks and private UUID
storage filenames in application response headers. Browser code already honored
Content-Disposition; new regressions verify plain and UTF-8 headers and fallback.

New headers use all name parts: Name_CV.docx, Name_CV_Company.docx and
Name_Cover_Letter_Company.docx. Personal name comes from the approved contact
snapshot. Application name comes from the current account, with current company
last. Components use Unicode NFKC, remove controls/unsafe punctuation/path
separators, normalize whitespace to underscores and cap each at 60 characters.
Empty names/company become Applicant/Company. Windows device-name components are
disambiguated. Django safely encodes Unicode Content-Disposition.

Existing uploaded CVs use neutral Uploaded_CV.pdf/.doc/.docx, preserving the
supported file extension; unexpected legacy extensions use .bin safely. Storage
names, ownership, bytes and approval hashes are unchanged. Application labels may
change after account/company edits; that does not rewrite their documents. No
storage IDs are needed in visible download labels. Filename metadata is not a
historical provenance guarantee. Duplicate human names may cause the browser to
add its ordinary local duplicate suffix.

## Verification and manual review

Focused backend: three tests passed (0.542s); focused/full frontend run: 71 tests
passed. Full package check/drift/Django/npm ci/lint/test/build results are recorded
in CHECKPOINT4_PHASE_C_REVIEW.md. Real phone/browser visual layout is UNVERIFIED.

1. In local Ajiri, clear skills and save. Job cards offer the profile link; add a
   nonmatching skill and confirm the genuine zero score returns.
2. Submit registration with several server errors. Verify Password/Email labels,
   readable spacing, every message, keyboard focus and input associations. Repeat
   with a nested CV entry error; entered content must remain intact.
3. Download a personal approved CV with a multi-part name. Confirm company-last
   names for both application documents and a neutral label for an uploaded PDF.
4. Change the account name and download an existing application again: its label
   may change, but Get-FileHash against the earlier download must match.
5. Check a Unicode name, punctuation-only company, narrow screen and light/dark
   modes. Never put real personal document contents into the review report.

Rollback paired server/client/build. Retain all files, approvals and newer writes;
no database rollback is needed. Reverting headers reintroduces old naming only.
