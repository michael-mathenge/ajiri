# Payments: requirements and offline contract, not live checkout

24 October 2026. AJ-44/45/46 first-scope preparation follows Michael's choice
of requirements and test integrations before live services. No merchant account,
credentials, customer phone number, HTTP payment request, callback endpoint,
subscription database or premium UI is introduced. Browsing, applying and existing
document downloads remain free. Displayed plan prices are previews, not authority
to collect a payment or start a subscription.

## Decisions that remain open

| Requirement | Current evidence / required owner action |
|---|---|
| Merchant ownership and settlement | No verified Ajiri merchant ownership, shortcode/product eligibility or settlement access. Owner must establish the actual merchant and permitted product. |
| Sandbox | Official Daraja portal documents sandbox applications/credentials. No signed-in sandbox app/access was verified; do not create credentials or accept terms for the owner. |
| Commercial offer | Exact price, term, limits, renewal/cancellation, customer support and refunds require an explicit offer; no recurring payment assumption. The lab's KES100/30-day term is synthetic only. |
| Legal/tax | Qualified review of consumer disclosures, receipts/tax treatment, refund disputes and payment-provider agreements remains required; this package supplies no legal determination. |
| Privacy | Define purpose, minimal payer fields, processor roles, retention, access and deletion/backup handling before collecting real payer data. Never put phone numbers or credentials in logs/artifacts. |
| Provider reconciliation | Confirm the chosen product's authenticated evidence can establish checkout, merchant, payer correlation, amount, currency, receipt and reversals. Missing fields or disagreement must remain unresolved. |
| Production | Durable repository, additive reviewed schema, crash recovery, signature/access strategy, strict callback bounds, monitoring and sandbox evidence precede a separately approved bounded live transaction. |

## Provider observations (official sources checked 24 October)

Safaricom's [M-Pesa Express simulator documentation](https://developer.safaricom.co.ke/apis/MpesaExpressSimulate)
distinguishes request acceptance from the later processing result and returns a
checkout identifier. An accepted initiation is therefore insufficient evidence
of payment. The [Transaction Status documentation](https://developer.safaricom.co.ke/apis/TransactionStatus)
describes asynchronous reconciliation using a transaction or originator identifier.
It is not proof that every chosen Express status flow supplies all the financial
fields Ajiri needs. Product/account eligibility and the exact evidence mapping
must be demonstrated in the owner's sandbox. No undocumented callback signature
or provider-side event sequence is assumed.

## Executable offline contract

`jobs/payment_test_contract.py` has no production imports/callers. Only an exact
`SyntheticGateway` may be injected. Immutable checkout records use UUID owner and
decision IDs; a server-owned test catalogue supplies amount/currency. Concurrent
retries of the same decision produce one initiation. A timeout remains unknown;
the same decision cannot initiate again. A future durable implementation must
persist the decision before handoff and recover a process crash without retrying
an uncertain transaction.

Callbacks are untrusted hints and cannot mutate an entitlement. An authoritative
synthetic query must match owner, checkout, amount/currency and a unique receipt.
The internal revision is a lab evidence sequence, not a claimed Daraja field.
Older evidence is ignored; a reconciled refund is terminal for that checkout.
Successful query replay never extends the term. Status uncertainty suspends the
synthetic paid capability, while free browsing/applying/document access continues.
No payment receipt or client plan label can grant another owner's capability.

The memory repository serializes concurrent starts and receipt/entitlement commits
under one lock. Injected write failure commits neither receipt nor entitlement;
query reconciliation can resume without initiation. This proves the contract,
not multi-process locking, durable transactions, real crash recovery or provider
integration. Future production persistence must use database constraints and
atomic receipts, plus explicit handling of crashes before/after external handoff.

The fake status interface includes success, failure, cancellation, pending,
unknown and refund outcomes. A callback itself is deliberately not a trusted
input adapter. A real Daraja adapter, credential handling, network retry policy
and callback authentication remain unimplemented until sandbox access and the
specific provider evidence contract are established.

## Verification and rollback

Focused12 synthetic tests passed in0.007s; Ruff passed. Cases cover owner denial,
server pricing, concurrent duplicate initiation, ambiguous handoff, status mismatch,
callback spoofing, expiry, refunds, stale evidence, duplicate receipt and interrupted
write recovery. Full414 Django tests passed327.067s (one known platform skip),
system/drift and all-backend Ruff passed. Node24.19 locked install audited364
with zero vulnerabilities; lint/build1.98s and exact unchanged36-file comparison
passed. CI/release remain pending. No live payment test ran.

There are no migrations, routes or flags to activate. Removing the unused lab
cannot change an account's balance, tier or documents. Future live rollback must
stop new initiations while retaining receipt/reconciliation access; it must not
discard settled transactions or restore stale account state over new payments.
Do not mark AJ-45/46 live or Done on the strength of these fake tests.
