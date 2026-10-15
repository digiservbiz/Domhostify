# DomHostify — Project Status

**Last updated:** 2026-10-15  
**Current phase:** Phase 4 — Marketplace security foundation  
**Overall progress:** 61% (marketplace lifecycle gates, audit events, ownership-challenge storage, and security helpers are now committed; runtime execution, CI verification, live providers, authentication, and production deployment remain outstanding)

## Executive status
The repository now has a stronger marketplace foundation: public inventory requires verified ownership and approved moderation, lifecycle events can be audited without request fingerprint data, and ownership challenges persist only token hashes. Seller write routes remain disabled until authentication/authorization and real ownership verification integrations exist.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Core marketplace and comparison pillars documented |
| PRD and user journeys | In progress | 78% | Marketplace lifecycle requirements expanded |
| Architecture and data boundaries | In progress | 73% | Marketplace trust boundaries and lifecycle storage defined |
| Roadmap and project governance | In progress | 88% | Status and migration sequence maintained |
| Security, privacy, compliance | In progress | 62% | Visibility gates, audit foundation, hashed ownership challenges, and privacy-conscious tracking implemented; auth/abuse/compliance remain |
| API implementation | In progress | 78% | Public marketplace reads are gated; secure seller writes intentionally not exposed yet |
| Database and migrations | In progress | 78% | Migrations now cover lifecycle metadata, audit events, and ownership challenges; execution remains unverified |
| Frontend | In progress | 35% | Responsive comparison prototype; seller UI not connected |
| Provider/affiliate integrations | In progress | 30% | Safe affiliate redirect foundation; no live provider access verified |
| Automated tests and CI | In progress | 60% | Schema and marketplace helper tests committed; runtime/CI result still unverified |
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
- [x] Domain validation/search/suggestion foundation
- [x] Registrar and hosting persistent read catalogs
- [x] HTTPS-only allowlisted affiliate redirects with opaque click tracking
- [x] Responsive frontend prototype
- [ ] Runtime pytest suite verified
- [ ] Alembic upgrade/downgrade verified from a clean database
- [ ] GitHub Actions result verified
- [ ] API/frontend smoke test verified
- [ ] Authentication and authorization implemented
- [ ] Real DNS/registrar ownership verification implemented
- [ ] Seller listing creation/editing implemented
- [ ] Seller dashboard implemented
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
- [ ] M4.2 Authentication + seller listing workflow
- [ ] M4.3 Real ownership verification
- [ ] M5 Transaction workflows
- [ ] M6 Live provider integrations
- [ ] M7 Production staging and launch verification

## Current limitations
- Runtime tests and Alembic migrations could not be executed from the current environment because external GitHub network access is unavailable to the execution container.
- CI has not been verified as passing.
- Domain availability remains unknown because no live registrar is queried.
- Hosting and aftermarket catalog records remain illustrative/database-supplied until verified feeds are connected.
- Ownership challenge generation exists as an internal helper only; DNS lookup/verification is not implemented.
- No public seller write route exists yet, intentionally.
- Authentication, authorization, abuse prevention, payments, transfers, and auctions remain unimplemented.

## Next actions
1. Build authentication/authorization boundary for seller and admin operations.
2. Add authenticated seller listing submission with draft → review lifecycle.
3. Implement DNS ownership verification against the stored challenge hash.
4. Add moderation/admin operations behind authorization.
5. Connect marketplace frontend to authenticated seller workflows and public inventory.
6. Verify migrations/tests/CI, then move into transaction and live-provider integrations.

## Update discipline
Progress must reflect verified repository deliverables, not effort estimates. Never mark an external integration or runtime test as complete until it has actually been verified.
