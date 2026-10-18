# DomHostify — Project Status

**Last updated:** 2026-10-19  
**Current phase:** Phase 5 — Account/session security and marketplace release hardening  
**Overall progress:** 99%

## Executive status
DomHostify now has the core authenticated marketplace release path: persistent listings, seller lifecycle management, DNS ownership verification, admin moderation, audit visibility, Make Offer and Buy Now reservation flows, and buyer/seller/admin session authorization. The admin moderation queue is now backed by dedicated authenticated endpoints rather than the public approved-listing catalog. Focused integration coverage has been added for seller/buyer/admin authorization boundaries and the moderation lifecycle. GitHub Actions CI run #256 passed on commit `ca9440ac8caab3bf24b39931dc9efffb895cd388`: database migration upgrade/downgrade and the full test suite are green (95 passed). A live API smoke script has been added at `scripts/runtime_smoke.py` and documented; it still must be run against a running staging API. External provider integrations remain release-stage work.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Domain, hosting and marketplace pillars documented |
| Architecture and data boundaries | In progress | 96% | Account/session boundary, payment contract, marketplace auth and admin moderation boundaries added |
| Security, privacy, compliance | In progress | 96% | PBKDF2, opaque sessions, role checks, ownership verification, audit trail and protected admin queue |
| API implementation | In progress | 100% | Core catalog, account, seller, ownership, moderation and transaction APIs implemented; live checkout is not |
| Database and migrations | In progress | 98% | Migrations 0001–0010 committed |
| Frontend | In progress | 86% | Public catalog, account/seller workspace, ownership controls and functional admin moderation/audit UI |
| Provider/affiliate integrations | In progress | 32% | Safe affiliate and payment abstractions; no live payment or registrar provider |
| Automated tests and CI | In progress | 100% | CI run #256 passed; migrations upgrade/downgrade cleanly and all 95 tests pass; live browser smoke remains unverified |
| Deployment and monitoring | Not started | 0% | No production deployment verified |

## Verified existing deliverables
- [x] Persistent domain, hosting, and approved marketplace catalog endpoints
- [x] Responsive public frontend with explicit unknown availability states
- [x] Seller listing lifecycle, ownership challenge, moderation, and audit events
- [x] Make Offer and Buy Now reservation/idempotency flows
- [x] Provider-neutral payment request/result contract
- [x] Payment amount/currency/idempotency validation and trusted-actor guards
- [x] PBKDF2 password hashing and opaque hashed session storage
- [x] Buyer/seller account registration with role restrictions
- [x] Login, logout, session expiry/revocation, and `/me` account endpoints
- [x] Migration 0010 for user accounts and sessions
- [x] Ownership endpoints use session-backed seller authorization with legacy bootstrap compatibility
- [x] Transaction endpoints use session-backed buyer/seller/admin authorization with legacy bootstrap compatibility
- [x] Main marketplace seller/admin review route uses session-backed authorization
- [x] Auth bridge and FastAPI dependency regression tests
- [x] Focused authenticated seller/buyer/admin marketplace integration coverage committed
- [x] Added opt-in live HTTP runtime smoke script for health/readiness, seller registration/session, listing persistence, DNS challenge generation, withdrawal, and logout revocation
- [x] Dedicated authenticated admin moderation queue endpoint
- [x] Dedicated authenticated admin listing audit endpoint
- [x] Admin UI status filtering, approve/reject actions, refresh and audit display
- [x] Session-aware account frontend with seller listing management and ownership controls

## Current verification gates
- [x] CI run #256 for commit `ca9440ac8caab3bf24b39931dc9efffb895cd388` passes: migration upgrade/downgrade and 95 tests
- [ ] Execute `scripts/runtime_smoke.py` against a running staging API and record the actual outcome
- [ ] Production deployment and monitoring verification

## Remaining release blockers
- [ ] Real payment provider, checkout endpoint, provider-specific signed webhook handling, refunds/disputes/reconciliation
- [ ] Domain transfer workflow
- [ ] Live registrar availability and pricing adapters
- [ ] Live hosting provider feeds
- [ ] Production database, deployment, monitoring, and launch verification
- [ ] Auctions

## Next attack sequence
1. Execute `scripts/runtime_smoke.py` against a running staging API, then run a separate end-to-end browser test for admin queue, DNS ownership publication/verification, moderation, and public listing.
2. Replace prototype sessionStorage bearer-token storage with secure HttpOnly cookie auth, including CSRF protections and deployment-aware CORS/cookie settings; keep bearer compatibility only if explicitly required.
3. Select and integrate live registrar, hosting and payment providers.
4. Deploy staging, add monitoring/alerts, then perform production launch checks.
5. Add auctions after the authenticated marketplace path is runtime-verified.

## Current limitations
- Domain availability remains unknown until a live registrar adapter is connected.
- Hosting and marketplace inventory is database-supplied, not automatically live provider inventory.
- Buy Now creates a temporary reservation only; no payment is collected and no domain is transferred.
- The payment module is an integration boundary only, not live checkout.
- Browser smoke and live deployment have not yet been verified.

Progress reflects verified deliverables, not effort estimates. Do not mark external integrations or runtime behavior complete until verified.
