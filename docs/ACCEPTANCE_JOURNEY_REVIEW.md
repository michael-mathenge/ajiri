# Acceptance journey review

19 October 2026. C1, local Phase C only. Base: 4b6e99b; no deployment.

The real-endpoint Django journey now selects its approval, prepares an application,
reads the review list and downloads its independent snapshot. It proves byte
identity before/after Profile edits, cross-owner denial, no mail/provider call,
unchanged delivery attempts and no sent timestamp. Captured verification mail is
cleared before preparation. Existing JWT/CSRF behavior is exercised, not changed.
Vitest now follows selection through the real Applications component to review;
registration/login/profile/builder transitions retain their existing component
coverage. This is API integration plus mocked client coverage, not browser E2E.

Actual gates: Python 3.12.6 check passed; makemigrations --check --dry-run reported
no changes; full Django suite 210 passed in 112.762s, one existing Windows symlink
skip. Node 24.19.0 npm ci (0 advisories), lint, 67 tests and build passed. The first
frontend run exposed a new mock missing ?page=1; corrected. The second exposed an
existing animation-frame focus assertion; waitFor now waits without weakening it.
The final frontend run passed all 67. No application defect was found in this
journey. Generated assets are byte-identical to the pinned committed build after
index newline normalization. No dependencies, migrations or production actions.
