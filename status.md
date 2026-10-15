# DomHostify — Project Status

**Last updated:** 2026-10-15  
**Current phase:** Phase 4 — Marketplace security foundation  
**Overall progress:** 70% (seller/admin workflow and one-time ownership-proof validation helper are committed; live DNS resolver wiring, real account auth, runtime verification, providers, transactions, and deployment remain outstanding)

## Executive status
The marketplace now has separate fail-closed bootstrap boundaries for seller writes/inventory and admin moderation, plus authenticated seller listing submission/inventory reads. Submissions are normalized, stored as `pending_review`, remain unverified/inactive, and create an audit event. Inventory reads filter by the opaque SHA-256-derived seller reference. The seller token is never stored directly. This is a bootstrap boundary, not yet a full user/account identity system.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Core marketplace and comparison pillars documented |
| PRD and user journeys | In progress | 80% | Seller submission/review lifecycle now represented |
| Architecture and data boundaries | In progress | 78% | Seller auth boundary and marketplace trust gates defined |
| Roadmap and project governance | In progress | 90% | Status and migration sequence maintained |
| Security, privacy, compliance | In progress | 75% | Seller/admin bootstrap boundaries, audit trail, hashed ownership proof, and one-time proof consumption; full auth/abuse remain |
| API implementation | In progress | 88% | Public reads gated; seller submission/inventory and admin moderation implemented; ownership helper not wired to API |
| Database and migrations | In progress | 80% | Lifecycle, audit, and ownership-challenge storage committed; execution remains unverified |
| Frontend | In progress | 35% | Responsive comparison prototype; seller UI not connected |
| Provider/affiliate integrations | In progress | 30% | Safe affiliate redirect foundation; no live provider access verified |
| Automated tests and CI | In progress | 70% | One-time ownership proof test added; runtime/CI result still unverified |
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
- [x] Ownership proof helper validates hash, expiry, pending state, one-time consumption, and audit trail
- [x] Test added for successful ownership proof and replay refusal
- [x] Tests cover marketplace lifecycle schema, audit schema, ownership-challenge schema, and helper behavior
- [x] Bootstrap seller authentication boundary fails closed when no server-side token is configured
- [x] Seller listing submission requires Bearer authentication
- [x] Seller listing submission creates `pending_review` + `unverified` + inactive listings
- [x] Seller listing submission creates a seller audit event
- [x] Seller identity persistence uses an opaque SHA-256-derived reference, not the raw token
- [x] Seller API tests cover disabled auth, invalid credentials, review lifecycle, audit creation, and public invisibility
- [x] Authenticated seller inventory endpoint filters records by seller reference
- [x] Seller inventory tests cover missing authentication and cross-reference isolation
- [x] Admin moderation boundary fails closed without a configured server-side token
- [x] Admin approval refuses listings without verified ownership
- [x] Admin approve/reject transitions append audit events and preserve public visibility gates
- [x] Admin moderation tests cover unverified approval refusal, approval publication, and rejection privacy
- [x] Domain validation/search/suggestion foundation
- [x] Registrar and hosting persistent read catalogs
- [x] HTTPS-only allowlisted affiliate redirects with opaque click tracking
- [x] Responsive frontend prototype
- [ ] Runtime pytest suite verified
- [ ] Alembic upgrade/downgrade verified from a clean database
- [ ] GitHub Actions result verified
- [ ] API/frontend smoke test verified
- [ ] Full user/account authentication and authorization implemented
- [ ] Real DNS/registrar ownership verification implemented (validation helper exists; authenticated endpoints/resolver flow still pending)
- [ ] Seller listing editing/deletion implemented
- [ ] Real per-user seller identities implemented (current bootstrap token maps to one seller identity)
- [ ] Seller dashboard implemented
- [ ] Full moderation/admin operations implemented
- [x] Bootstrap admin review endpoint supports approve/reject with audit events
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
- Ownership challenge generation and a one-time proof-validation helper exist. Authenticated challenge creation, live DNS resolver wiring, and verification endpoints are not yet implemented.
- Seller editing/deletion and full admin tooling are not implemented. A bootstrap approve/reject endpoint exists; it requires a separate admin token and refuses approval until ownership is marked verified.
- Seller inventory currently uses a single configured bootstrap token; do not issue it to multiple sellers. A real account/session/role system is required for multi-seller production use.
- Payments, transfers, abuse prevention, and auctions remain unimplemented.

## Next actions
1. Wire authenticated seller endpoints to challenge generation and bounded live DNS TXT resolution; cover expiry and replay in tests.
2. Replace bootstrap seller/admin tokens with real account/session/role boundaries before production.
3. Connect marketplace frontend to seller submission and public inventory.
4. Verify migrations/tests/CI and add smoke coverage.
5. Build transaction/payment/transfer abstractions, then live registrar/hosting integrations.

## Update discipline
Progress must reflect verified repository deliverables, not effort estimates. Never mark an external integration or runtime test as complete until it has actually been verified.
