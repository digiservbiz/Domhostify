# DomHostify — Project Status

**Last updated:** 2026-10-18  
**Current phase:** Phase 5 — Account/session security and marketplace release hardening  
**Overall progress:** 98%

## Executive status
DomHostify has a persistent catalog/API foundation and marketplace listing, ownership, moderation, Make Offer, and Buy Now reservation flows. Payment foundation and transaction state-machine guards are committed. A real account/session foundation is implemented with PBKDF2 password hashing, opaque hashed sessions, buyer/seller/admin role checks, registration, login, logout, and `/me`. Ownership, transaction, and main marketplace APIs use the session-backed role dependency bridge while retaining legacy bootstrap-token compatibility. The frontend now provides session-aware buyer/seller account access, seller listing creation/listing management, DNS ownership challenge/verification controls, edit/withdraw controls, and an authenticated admin moderation dashboard foundation. Runtime verification still requires CI and browser smoke testing.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Domain, hosting and marketplace pillars documented |
| Architecture and data boundaries | In progress | 94% | Account/session boundary, payment contract, and marketplace auth boundary added |
| Security, privacy, compliance | In progress | 94% | Password hashing, opaque sessions, role checks, ownership/transaction/marketplace auth bridge; provider-specific controls pending |
| API implementation | In progress | 99% | Catalog and marketplace APIs implemented; live checkout is not |
| Database and migrations | In progress | 98% | Migrations 0001–0010 committed; prior 0001–0009 round-trip passed CI |
| Frontend | In progress | 80% | Public catalog plus session-aware account, seller management and admin moderation foundation |
| Provider/affiliate integrations | In progress | 32% | Safe payment abstraction; no live payment or domain provider |
| Automated tests and CI | In progress | 98% | Auth and dependency tests committed; newest account/auth migration still awaits CI verification |
| Deployment and monitoring | Not started | 0% | No production deployment verified |

## Verified existing deliverables
- [x] Persistent domain, hosting, and approved marketplace catalog endpoints
- [x] Responsive public frontend with explicit unknown availability states
- [x] Seller listing lifecycle, ownership challenge, moderation, and audit events
- [x] Make Offer and Buy Now reservation/idempotency flows
- [x] Clean database migration round-trip in prior CI for migrations 0001–0009
- [x] Provider-neutral payment request/result contract
- [x] Payment amount/currency/idempotency validation and trusted-actor guards
- [x] PBKDF2 password hashing and opaque hashed session storage
- [x] Buyer/seller account registration with role restrictions
- [x] Login, logout, session expiry/revocation, and `/me` account endpoints
- [x] Migration 0010 for user accounts and sessions
- [x] Ownership endpoints use the session-backed seller reference dependency with legacy bootstrap compatibility
- [x] Transaction endpoints use the session-backed buyer/seller/admin reference bridge with legacy bootstrap compatibility
- [x] Main marketplace seller/admin routes use the session-backed seller/admin reference bridge with legacy bootstrap compatibility
- [x] Account tests cover registration/login/logout and session role-boundary behavior
- [x] Auth bridge regression tests cover admin resolution and legacy bootstrap compatibility
- [x] FastAPI dependency integration smoke tests committed
- [x] Session-aware account frontend foundation with registration, login, logout, `/me`, and seller listing creation/listing view
- [x] Seller UI controls for listing price updates, withdrawal, DNS TXT challenge creation and ownership verification
- [x] Authenticated admin moderation dashboard foundation
- [ ] New account/auth tests confirmed by CI
- [ ] Transaction/main marketplace auth migration confirmed by CI
- [ ] Browser/runtime smoke testing

## Remaining release blockers
- [ ] Full admin workflow polish and audit visibility
- [ ] Browser/runtime smoke test against a running API
- [ ] Real payment provider, checkout endpoint, provider-specific signed webhook handling, refunds/disputes/reconciliation
- [ ] Domain transfer workflow
- [ ] Live registrar availability and pricing adapters
- [ ] Live hosting provider feeds
- [ ] Production database, deployment, monitoring, and launch verification
- [ ] Auctions

## Next attack sequence
1. Add focused authenticated integration tests for seller ownership/listing and admin moderation boundaries.
2. Verify migrations 0001–0010 and the newest auth work in CI.
3. Add browser smoke automation for registration → login → seller listing → ownership challenge → admin review.
4. Polish admin audit/review UX.
5. Integrate selected live domain/hosting/payment providers.
6. Deploy staging, monitoring/alerts, and complete production launch checks.
7. Design auctions after the authenticated marketplace path is runtime-verified.

## Current limitations
- Domain availability is unknown until a live registrar adapter is connected.
- Hosting and marketplace inventory is database-supplied, not automatically live provider inventory.
- Buy Now creates a temporary reservation only; no payment is collected and no domain is transferred.
- The payment module is an integration boundary only, not live checkout.
- Browser smoke and live deployment have not been verified.

Progress reflects verified deliverables, not effort estimates. Do not mark external integrations or runtime behavior complete until verified.
