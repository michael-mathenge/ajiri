# AJ-44/45: durable sandbox boundary, inactive and blocked

31 October 2026. This supersedes implementation-status portions of
PAYMENTS_TEST_CONTRACT.md; the earlier memory lab remains historical test code.
No actual merchant access, provider call, charging, legal determination, production
transport or sandbox financial acceptance was performed.

jobs.0019/0020 add an empty inactive server offer catalogue and durable owner
checkouts. Exact terms-version consent, server price/term/capability snapshots,
unique decision UUIDs and one unresolved checkout per owner are enforced. A first
profile write serializes decisions. The checkout commits before network I/O;
wrapping transactions are refused. Timeouts/process death retain unknown or
handoff_started. Reusing an identity never repeats initiation; a new decision
cannot bypass an unresolved checkout. No automatic retry/reset/close API exists.

The real urllib adapter implements sandbox OAuth, Express initiation and explicit
status queries against the fixed official sandbox host. TLS checking stays on;
ambient proxies, redirects and retries are disabled. Responses are bounded to
16 KiB and ten seconds per blocking network operation. Errors exclude provider
bodies, credentials and payer data. Only a keyed payer fingerprint is persisted;
the phone is transient in request/transport. Host/proxy body logging must be
verified before activation. No credentials are entered or committed here.

Owner POST payments/checkouts/ rejects client amount/tier/extra fields. Owner GET
payments/checkouts/<uuid>/ works with initiation off. The public
payments/daraja/callback/ route is separately throttled and bounded to 8 KiB;
only a matching reference pair can set callback_seen_at once. No raw financial
payload, status authority, query, work enqueue or entitlement is produced.
Forged/replayed/out-of-order success/refund claims cannot settle or grant access.

reconcile_daraja_checkout --checkout-id UUID performs one explicit read-only query.
Matching Express success becomes evidence_required, not settled. Identity
disagreement remains blocked. Initiation can be off while reconciliation is
enabled; reviewed sandbox configuration remains required. No undocumented callback
signature/provider event revision is assumed.

## Remaining facts and blocked acceptance

Merchant ownership, product eligibility, private sandbox access and exact current
request/response acceptance remain external. Approve actual prices, terms, limits,
renewal/cancellation/refund/support, tax, privacy and retention facts. The catalogue
is empty; preview prices are not charging authority. Express PayBill sandbox is
a proposed reversible product path, not evidence of merchant eligibility. The
one-second to 366-day technical term bound is not a commercial offer.

Authenticated evidence must establish merchant, checkout, payer correlation,
amount/KES, unique receipt, settlement time and reversals. Express query success
alone is insufficient. There is no production writer to verified settlements
until the actual product mapping is evidenced. Do not turn callbacks, booleans or
manual database edits into payment verification. Real sandbox financial outcomes
and interrupted receipt recovery remain blocked; intercepted tests are not
provider transactions. Reconciliation/backups must survive uncertain responses.

Official sources checked 31 October: [Safaricom SDK](https://github.com/safaricom/mpesa-php-sdk/blob/master/src/Mpesa.php)
and [Daraja Express](https://developer.safaricom.co.ke/apis/MpesaExpressSimulate).
Endpoints/payload observations inform this adapter. Historical SDK TLS-disable
examples are not copied; actual merchant/product responses require sandbox proof.

## Activation and rollback

PAYMENTS_ENABLED, DARAJA_SANDBOX_ENABLED, DARAJA_RECONCILIATION_ENABLED and
DARAJA_MERCHANT_REVIEWED default false. Product review/private configuration are
empty. No production URL setting exists. Do not activate now. Before a future
authorized staging rollout: verified private backup/isolated restore, additive
migrations before activation, real sandbox acceptance, exact approved offers and
consent, host privacy/shared throttles/monitoring. Rollback disables initiation
while retaining owner status and reviewed reconciliation. Preserve all financial
records; never restore stale data over payments or prune without an approved
policy. Erasure blocks on payment records; verified owner export includes minimal
checkout metadata. No real-account action occurred.
