# DomHostify — Project Status

**Last updated:** 2026-10-18  
**Current phase:** Phase 5 — Account/session security and marketplace release hardening  
**Overall progress:** 95%

## Executive status
DomHostify has a persistent catalog/API foundation and marketplace listing, ownership, moderation, Make Offer, and Buy Now reservation flows. Payment foundation and transaction state-machine guards are committed. A real account/session foundation is implemented with PBKDF2 password hashing, opaque hashed sessions, buyer/seller/admin role checks, registration, login, logout, and `/me`. Ownership and transaction APIs now use the session-backed role dependency bridge while retaining legacy bootstrap-token compatibility. Main marketplace routes still need the same dependency migration. Runtime verification of the newest account work still requires CI.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Domain, hosting and marketplace pillars documented |
| Architecture and data boundaries | In progress | 92% | Account/session boundary and payment contract added |
| Security, privacy, compliance | In progress | 92% | Password hashing, opaque sessions, role checks, ownership/transaction auth bridge; provider-specific controls pending |
| API implementation | In progress | 99% | Catalog and marketplace APIs implemented; live checkout is not |
| Database and migrations | In progress | 98% | Migrations 0001–0010 committed; prior 0001–0009 round-trip passed CI |
| Frontend | In progress | 60% | Public catalog UI; account/dashboard UI and browser smoke pending |
| Provider/affiliate integrations | In progress | 32% | Safe payment abstraction; no live payment or domain provider |
| Automated tests and CI | In progress | 98% | Account flow, session role-boundary, admin role, and bootstrap compatibility tests committed; newest auth migration awaits CI |
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
- [x] Account tests cover registration/login/logout and session role-boundary behavior
- [x] Auth bridge regression tests cover admin resolution and legacy bootstrap compatibility
- [ ] New account/auth tests confirmed by CI
- [ ] Transaction auth migration confirmed by CI

## Remaining release blockers
- [ ] Replace bootstrap seller/buyer/admin dependencies in the remaining main marketplace routes while preserving compatibility
- [ ] Seller dashboard connected to real sessions and full admin UI
- [ ] Browser/runtime smoke test against a running API
- [ ] Real payment provider, checkout endpoint, provider-specific signed webhook handling, refunds/disputes/reconciliation
- [ ] Domain transfer workflow
- [ ] Live registrar availability and pricing adapters
- [ ] Live hosting provider feeds
- [ ] Production database, deployment, monitoring, and launch verification
- [ ] Auctions

## Next attack sequence
1. Migrate the remaining main marketplace dependencies to session-backed role references.
2. Add account-aware frontend login/register/session handling and seller/admin dashboard foundations.
3. Add focused transaction/session integration tests and verify migrations 0001–0010 in CI.
4. Add browser smoke automation for public + authenticated flows.
5. Integrate selected live providers and payment infrastructure only after access, terms, and provider-specific verification.
6. Deploy staging, monitoring/alerts, and complete production launch checks.

## Current limitations
- Domain availability is unknown until a live registrar adapter is connected.
- Hosting and marketplace inventory is database-supplied, not automatically live provider inventory.
- Main marketplace endpoints still contain the legacy bootstrap dependency layer and need migration.
- Buy Now creates a temporary reservation only; no payment is collected and no domain is transferred.
- The payment module is an integration boundary only, not live checkout.
- Browser smoke and live deployment have not been verified.

Progress reflects verified deliverables, not effort estimates. Do not mark external integrations or runtime behavior complete until verified.
