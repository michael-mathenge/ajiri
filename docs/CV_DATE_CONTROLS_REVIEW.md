# CV date controls review

17 October 2026. Local batch branch `codex/cv-save-feedback`. Suggested estimate:
2 points for date controls; certificate uploads are a separate proposed package.

The browser-dependent month picker is replaced for employment, education and
certification dates with a named month dropdown and numeric year input. Users can
type an older year directly without paging through calendars, or clear both parts
explicitly. Blank optional dates remain supported. Partial input stays in unsaved
state and browser validation requires the missing part rather than silently
discarding it. Server date/order validation remains unchanged. Selecting current
work/study clears and disables its end date and shows Present.

No API, stored date format, model, migration, dependency or production setting
changed. Complete dates still save as YYYY-MM. Existing approved CV documents are
not regenerated. Certificate uploads are not implemented: see the separate schema
and storage proposal in CERTIFICATE_UPLOAD_DESIGN.md.

## Verification

Backend check passed, migration drift reported no changes, and the full Django
suite passed: 210 tests in 148.715s, one existing Windows symlink skip. Node 24.19.0
locked npm ci, lint, all 66 frontend tests and production build passed. Generated
frontend_build refreshed once, with index.html normalized to LF. git diff --check
passed. Added component regressions cover
named month choices, typing a historical year, preventing partial-date submission,
unchanged YYYY-MM payloads, current-work end-date clearing/disabling, clear action,
loading existing certificate dates and preserving an independent expiry date.

## Manual checklist after review

1. In a test CV, choose September and type 2018. Save and verify 2018-09 in the
   preview. Reload a saved draft and confirm both controls retain the date.
2. Choose a month without a year, then try Save. Expect focus at the missing year
   with a browser validation message; typed CV information remains intact.
3. Set an end date, select currently work/study here, then save. End controls should
   be disabled/empty and preview should say Present. Unchecking re-enables them.
4. Clear dates; save and confirm they are omitted. Try an end before the start;
   expect the existing server validation summary and retained input.
5. Check issue/expiry separately, mobile widths, touch selection and keyboard tab
   order. Real-browser/mobile visual QA remains unverified in this package.

No push/deployment. Roll back the paired frontend source/build together. No data
rollback or migration is needed. Original-checkout changes/stash/config preserved.
