# AJ-24: registration privacy notice

20 October 2026. Local package, not yet deployed.

New public registrations require an unchecked explicit agreement and current
`privacy-draft-v1` policy version. Missing, declined or stale agreement is rejected
before account creation. An atomic account/profile write stores server time and
version; profile responses expose this only to its owner and make it read-only.
Existing accounts and admin-created accounts acquire no historical agreement.

`profiles.0006_privacy_notice` adds nullable timestamp and blank version only.
No User changes, existing-row data update, historical consent inference or email
permission is introduced. Old registration tabs must reload. Deploy the reviewed
server/client pair after the migration, with writers paused; rollback to the
preceding pair while retaining the additive fields and newer account records.

The public notice describes actual account/profile/document processing, current
providers, separate alert/application choices and backup limits. It stays DRAFT
for legal review; code approval is not legal certification. The statement must be
reviewed again when retention/providers/sending change. Registration agreement is
not a universal legal basis for every future use.

References: [ODPC rights](https://www.odpc.go.ke/rights-of-a-data-subject/) and
[ODPC consent guidance](https://www.odpc.go.ke/wp-content/uploads/2024/02/ODPC-Guidance-Notes-on-Consent.pdf).

Focused backend: 16 tests passed, including actual registration-to-approved-CV
journey; migration-drift check passed. Full backend: 286 passed, one Windows skip. Updated frontend: 100 tests, lint and build passed; exact commands and platform limitations are recorded in the roadmap progress report.
