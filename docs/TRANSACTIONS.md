# Marketplace transaction foundation

This document records the transaction boundary currently implemented in code.

## Current implementation

- `MarketplaceTransaction` stores the listing reference, opaque buyer/seller references, transaction type, fixed-precision amount, currency, state, optional expiry, and completion timestamp.
- `MarketplaceTransactionEvent` records each accepted state transition with previous/next status and actor metadata.
- Migration `0007_marketplace_transactions.py` creates both tables and the supporting indexes.
- `backend/app/transactions.py` enforces a state-transition allowlist and appends an event in the same database session. The caller remains responsible for committing the session.
- `backend/app/transactions_api.py` exposes bootstrap-authenticated make-offer submission, buyer offer history/cancellation, seller offer inventory, accept/reject decisions, and a Buy Now reservation intent. New offers/intents require a currently public listing; each action is scoped to the matching opaque buyer/seller reference.
- Migration `0008_listing_reservations.py` adds `reservation_transaction_id` and `reserved_until` to listings.
- Migration `0009_transaction_idempotency.py` adds a nullable buyer-scoped idempotency key with a unique index.
- Buy Now requires an `Idempotency-Key` header. Replaying the same key for the same active reservation returns that reservation; reusing it for another listing or a closed/expired reservation returns a conflict.
- Admin-authenticated `POST /api/v1/admin/marketplace/reservations/expire` cancels stale unpaid Buy Now intents, clears matching listing holds, and records transaction events. It can be invoked by a scheduled job; scheduling and monitoring are not yet configured.
- Buy Now intents use a conditional database `UPDATE` as the atomic reservation gate. The reservation lasts ten minutes, blocks competing intents, and is released when the buyer cancels that intent.

## State machine

`offer_pending → accepted → payment_pending → paid → transfer_pending → completed`

Alternative outcomes are represented explicitly: `rejected`, `cancelled`, `disputed`, and `refunded`. Invalid transitions raise `ValueError`; terminal states cannot be advanced by the helper.

## Deliberate limits

This is **not a live checkout flow**. The Buy Now endpoint creates only a temporary reservation intent. It does not collect payment, mark the transaction paid, or transfer the domain. There is no payment collection, escrow, registrar transfer, refund execution, or automated domain ownership transfer. Do not mark a transaction paid based only on a browser callback; future payment integration must verify provider-signed events server-side and make webhook processing idempotent.

Amounts use decimal database precision. The transaction records contain no card numbers, bank details, passwords, or payment credentials. Buyer/seller references are opaque placeholders until real accounts and authorization are implemented.

## Before launch

1. Replace bootstrap buyer/seller tokens with real account/session/role authorization and add stronger buyer/seller abuse controls.
2. Extend reservation/concurrency testing on the production database engine and wire the admin expiry endpoint to a monitored scheduled job.
3. Add idempotency keys and provider webhook signature/replay checks.
4. Integrate an approved payment provider and define refunds, disputes, chargebacks, and reconciliation.
5. Define domain-transfer steps, timeout handling, manual review, and completion evidence.
6. Add end-to-end tests and complete a security/compliance review before enabling live payments or transfers.
