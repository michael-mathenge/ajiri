# AJ-46: durable capability core; commercial activation blocked

jobs.0021 adds real database settlements and one grant per settlement, with unique
provider receipts, protected financial references and positive fixed expiry.
Settlement defaults unverified. No HTTP, callback, admin registration, CLI or
production provider mapper creates verified rows. The missing authenticated
settlement/reversal evidence mapping in DURABLE_PAYMENTS.md remains explicit;
synthetic fixtures are tests, not production verification or stand-in services.

materialize_grant is an internal atomic projection from that trusted boundary.
It serializes through the owner profile, checks exact merchant/payer fingerprint,
amount/KES, receipt, evidence hash/version and chronological verification time,
and binds owner/capability/expiry to the checkout's immutable server offer snapshot.
Interrupted grant/checkout commits roll back together and can be projected again
without provider I/O. Replaying a successful receipt never extends expiry. Unique
constraints prevent receipt or grant duplication. Two upgrades have independent
paid-at terms; this does not invent stacking/proration/recurring billing rules.

The evaluator checks current settlement evidence/revocation and exact grant
snapshot every time. Refund/reversal is terminal for that settlement. An older
receipt cannot revive it or revoke an independent newer valid grant. Disabled,
expired, unapproved, mismatched or missing evidence falls back to Free. Approved
paid capability names default empty; there is no tier/client-label authority.
Browsing, applying and existing document access remain free and unchanged.

This core does not invent commercial features, limits, prices, tax, renewal,
refund adjudication, retention or proration. There is no paid-feature enforcement
hook until exact purchased capabilities and protected action boundaries are
approved. A future protected service must check the evaluator at its actual
mutation/handoff boundary, using the same owner serialization for races. Actual
verified settlement/reversal writers must take that owner lock and preserve
terminal reversal history. Database edits and hash strings are not provider proof.

ENTITLEMENTS_ENABLED=False, PAYMENT_EVIDENCE_VERSION empty and
ENTITLEMENT_APPROVED_CAPABILITIES empty independently deny paid capabilities.
The source verification version identifies a reviewed actual mapping, not a
switch to bless arbitrary records. Financial export inventory includes the new
records; erasure remains blocked pending actual financial/privacy retention facts.
No real-account export/erasure, charging, provider call or paid enforcement ran.

Before future activation: approve exact offer/capabilities/terms/retention facts;
implement and accept the actual authenticated merchant receipt/amount/reversal
mapping; run real authorized sandbox outcomes and atomic interrupted reconciliation
acceptance; verified private backup/off-server isolated restore; apply jobs.0019–0021
before paired code; then explicitly approve flags and protected-service hooks.
Rollback disables paid capabilities/initiations, retains Free access and financial
reconciliation, and preserves all newer records. Never reverse populated financial
migrations or restore stale grants over refunds. No pruning policy is implied.
