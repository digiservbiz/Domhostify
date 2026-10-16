# Payment integration boundary

Status: foundation only; live payment processing is disabled.

The module `backend/app/payment.py` defines provider-neutral request/result types, validates positive fixed-precision amounts, normalizes three-letter currency codes, validates idempotency keys, and exposes a `PaymentProvider` protocol. `DisabledPaymentProvider` is the default safe behavior: it reports `ready = False` and raises `PaymentNotConfigured` instead of creating a successful intent.

The module also contains an HMAC-SHA256 helper for validating a signature against the exact raw webhook body. This is a generic primitive, not a provider integration. Each selected provider's documented signature format, timestamp/replay policy, event identifiers, and event schema still need provider-specific implementation.

## Required before live checkout

- Select and configure an approved payment provider using server-side secrets.
- Create hosted checkout intents from transaction amounts read from the database.
- Make checkout and webhook processing idempotent.
- Verify webhook signatures and event authenticity before state changes.
- Never mark a transaction paid from a browser redirect or unverified client callback.
- Implement refund, dispute, reconciliation, and audit workflows.
- Keep payment credentials and card data out of DomHostify records.
- Add integration tests using provider sandbox fixtures, then verify a staging deployment.

No payment is currently collected, and this module must not be represented as a live checkout integration.
