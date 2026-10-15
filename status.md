# DomHostify — Project Status

**Last updated:** 2026-10-15  
**Current phase:** Phase 4 — Marketplace security foundation  
**Overall progress:** 66% (authenticated seller submission boundary and review lifecycle are now committed; real account auth, DNS verification, moderation controls, runtime verification, live providers, transactions, and production deployment remain outstanding)

## Executive status
The marketplace now has a bootstrap authentication boundary for seller writes and an authenticated seller listing-submission workflow. Submissions are normalized, stored as `pending_review`, remain unverified/inactive, and create an audit event. The seller token is never stored directly; an opaque SHA-256-derived seller reference is persisted. This is a security boundary, not yet a full user/account identity system.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Core marketplace and comparison pillars documented |
| PRD and user journeys | In progress | 80% | Seller submission/review lifecycle now represented |
| Architecture and data boundaries | In progress | 78% | Seller auth boundary and marketplace trust gates defined |
| Roadmap and project governance | In progress | 90% | Status and migration sequence maintained |
| Security, privacy, compliance | In progress | 70% | Authenticated seller boundary, visibility gates, audit foundation, hashed challenges; full auth/abuse/compliance remain |
| API implementation | In progress | 84% | Public reads gated and authenticated seller submission implemented |
| Database and migrations | In progress | 80% | Lifecycle, audit, and ownership-challenge storage committed; execution remains unverified |
| Frontend | In progress | 35% | Responsive comparison prototype; seller UI not connected |
| Provider/affiliate integrations | In progress | 30% | Safe affiliate redirect foundation; no live provider access verified |
| Automated tests and CI | In progress | 65% | Seller API tests committed; runtime/CI result still unverified |
| Deployment and monitoring | Not started | 0% | No deployment verified |

## Verified repository deliverables
- [x] Persistent marketplace visibility requires active listing + active status + verified ownership + approved moderation
- [x] Marketplace listing detail endpoint enforces the same public visibility gates
- [x] Marketplace lifecycle migration `0004_marketplace_lifecycle.py`
- [x] Listing audit-event model and migration `0005_listing_audit_events.py`
- [x] Audit events avoid IP address and user-agent storage
- [x] Ownership challenge model stores a SHA-256 token hash rather than a raw token
- [x] Ownership challenge migration `0006_ownership_challenges.py`
- [x] Marketplace lifecycle helpers create bounded DNS-TXT challenges and append audit events
- [x] Tests cover marketplace lifecycle schema, audit schema, ownership-challenge schema, and helper behavior
- [x] Bootstrap seller authentication boundary fails closed when no server-side token is configured
- [x] Seller listing submission requires Bearer authentication
- [x] Seller listing submission creates `pending_review` + `unverified` + inactive listings
- [x] Seller listing submission creates a seller audit event
- [x] Seller identity persistence uses an opaque SHA-256-derived reference, not the raw token
- [x] Seller API tests cover disabled auth, invalid credentials, review lifecycle, audit creation, and public invisibility
- [x] Domain validation/search/suggestion foundation
- [x] Registrar and hosting persistent read catalogs
- [x] HTTPS-only allowlisted affiliate redirects with opaque click tracking
- [x] Responsive frontend prototype
- [ ] Runtime pytest suite verified
- [ ] Alembic upgrade/downgrade verified from a clean database
- [ ] GitHub Actions result verified
- [ ] API/frontend smoke test verified
- [ ] Full user/account authentication and authorization implemented
- [ ] Real DNS/registrar ownership verification implemented
- [ ] Seller listing editing/deletion implemented
- [ ] Seller dashboard implemented
- [ ] Moderation/admin operations implemented
- [ ] Buy Now / Make Offer transaction flow implemented
- [ ] Payments/transfer workflow implemented
- [ ] Auctions implemented
- [ ] Live registrar/hosting provider integrations verified
- [ ] Production deployment and monitoring verified

## Milestones
- [x] M0 Foundation documentation and repository
- [x] M1 Runnable API/test baseline committed
- [x] M2 Domain/hosting comparison prototype committed
- [x] M3 Registrar adapter contract and affiliate safety foundation
- [x] M4 Marketplace visibility lifecycle gates
- [x] M4.1 Audit-event and ownership-challenge storage foundation
- [x] M4.2 Bootstrap authentication + seller listing workflow
- [ ] M4.3 Real ownership verification
- [ ] M4.4 Moderation/admin workflow
- [ ] M5 Transaction workflows
- [ ] M6 Live provider integrations
- [ ] M7 Production staging and launch verification

## Current limitations
- Runtime tests and Alembic migrations could not be executed from the current environment because external GitHub network access is unavailable to the execution container.
- CI has not been verified as passing.
- The current seller token is a bootstrap server-side credential, not a complete multi-user account/session/role system.
- Domain availability remains unknown because no live registrar is queried.
- Hosting and aftermarket catalog records remain illustrative/database-supplied until verified feeds are connected.
- Ownership challenge generation exists as an internal helper only; DNS lookup/verification is not implemented.
- Seller editing/deletion and admin moderation are not implemented.
- Payments, transfers, abuse prevention, and auctions remain unimplemented.

## Next actions
1. Implement DNS ownership verification against the stored challenge hash, including expiry/replay protection.
2. Add authenticated admin/moderation operations with explicit state transitions and audit events.
3. Replace bootstrap seller token with a real account/session/role boundary before production.
4. Connect marketplace frontend to seller submission and public inventory.
5. Verify migrations/tests/CI and add smoke coverage.
6. Build transaction/payment/transfer abstractions, then live registrar/hosting integrations.

## Update discipline
Progress must reflect verified repository deliverables, not effort estimates. Never mark an external integration or runtime test as complete until it has actually been verified.
