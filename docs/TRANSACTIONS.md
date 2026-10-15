# Marketplace transaction foundation

This document records the transaction boundary currently implemented in code.

## Current implementation

- `MarketplaceTransaction` stores the listing reference, opaque buyer/seller references, transaction type, fixed-precision amount, currency, state, optional expiry, and completion timestamp.
- `MarketplaceTransactionEvent` records each accepted state transition with previous/next status and actor metadata.
- Migration `0007_marketplace_transactions.py` creates both tables and the supporting indexes.
- `backend/app/transactions.py` enforces a state-transition allowlist and appends an event in the same database session. The caller remains responsible for committing the session.

## State machine

`offer_pending → accepted → payment_pending → paid → transfer_pending → completed`

Alternative outcomes are represented explicitly: `rejected`, `cancelled`, `disputed`, and `refunded`. Invalid transitions raise `ValueError`; terminal states cannot be advanced by the helper.

## Deliberate limits

This is **not a live checkout flow**. There is no public transaction-creation endpoint, payment collection, escrow, registrar transfer, refund execution, or automated domain ownership transfer. Do not mark a transaction paid based only on a browser callback; future payment integration must verify provider-signed events server-side and make webhook processing idempotent.

Amounts use decimal database precision. The transaction records contain no card numbers, bank details, passwords, or payment credentials. Buyer/seller references are opaque placeholders until real accounts and authorization are implemented.

## Before launch

1. Add authenticated buyer/seller transaction endpoints and verify both parties against the listing.
2. Add atomic listing reservation / concurrency control to prevent two successful purchases of one domain.
3. Add idempotency keys and provider webhook signature/replay checks.
4. Integrate an approved payment provider and define refunds, disputes, chargebacks, and reconciliation.
5. Define domain-transfer steps, timeout handling, manual review, and completion evidence.
6. Add end-to-end tests and complete a security/compliance review before enabling live payments or transfers.
