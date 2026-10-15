# DomHostify — Project Status

**Last updated:** 2026-10-15  
**Current phase:** Phase 4 — Marketplace security foundation  
**Overall progress:** 78% (seller listing edit/withdraw lifecycle is committed and GitHub Actions now passes all 41 tests; migrations, real account auth, providers, transactions, and deployment remain outstanding)

## Executive status
The marketplace now has separate fail-closed bootstrap boundaries for seller writes/inventory and admin moderation, plus authenticated seller listing submission/inventory reads. Submissions are normalized, stored as `pending_review`, remain unverified/inactive, and create an audit event. Inventory reads filter by the opaque SHA-256-derived seller reference. The seller token is never stored directly. This is a bootstrap boundary, not yet a full user/account identity system.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Core marketplace and comparison pillars documented |
| PRD and user journeys | In progress | 80% | Seller submission/review lifecycle now represented |
| Architecture and data boundaries | In progress | 78% | Seller auth boundary and marketplace trust gates defined |
| Roadmap and project governance | In progress | 90% | Status and migration sequence maintained |
| Security, privacy, compliance | In progress | 78% | Seller/admin bootstrap boundaries, hashed one-time DNS proof, bounded DNS lookup, audit trail; full auth/abuse controls remain |
| API implementation | In progress | 94% | Seller submission/inventory, edit/withdraw lifecycle, admin moderation, and authenticated DNS ownership endpoints committed; runtime verification outstanding |
| Database and migrations | In progress | 80% | Lifecycle, audit, and ownership-challenge storage committed; execution remains unverified |
| Frontend | In progress | 35% | Responsive comparison prototype; seller UI not connected |
| Provider/affiliate integrations | In progress | 30% | Safe affiliate redirect foundation; no live provider access verified |
| Automated tests and CI | In progress | 84% | GitHub Actions passed 41 tests on 2026-10-15; one warning remains, and migration/smoke verification is pending |
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
- [x] Runtime pytest suite verified in GitHub Actions: 41 passed, 1 warning (2026-10-15)
- [ ] Alembic upgrade/downgrade verified from a clean database
- [x] GitHub Actions CI passed on commit `152d7dad33a59508554950ca076880afc3e0c416`
- [ ] API/frontend smoke test verified
- [ ] Full user/account authentication and authorization implemented
- [x] Authenticated seller DNS TXT challenge and verification endpoints committed (runtime and live DNS behavior still unverified)
- [x] Seller listing editing and soft withdrawal endpoints committed; changes require renewed moderation, withdrawal preserves audit history, and seller isolation is tested
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
- [x] M4.3 Ownership verification API committed; mocked DNS verification test passes, live DNS checks remain pending
- [x] M4.3.1 Seller listing edit/withdraw lifecycle committed and CI-tested
- [ ] M4.4 Moderation/admin workflow (bootstrap approve/reject exists; seller listing edit/withdraw now committed)
- [ ] M5 Transaction workflows
- [ ] M6 Live provider integrations
- [ ] M7 Production staging and launch verification

## Current limitations
- Runtime tests and Alembic migrations could not be executed from the current environment because external GitHub network access is unavailable to the execution container.
- CI has not been verified as passing.
- The current seller token is a bootstrap server-side credential, not a complete multi-user account/session/role system.
- Domain availability remains unknown because no live registrar is queried.
- Hosting and aftermarket catalog records remain illustrative/database-supplied until verified feeds are connected.
- Authenticated seller ownership-challenge and verification endpoints now exist in code. They issue a 30-minute TXT token, resolve TXT with a 4-second DNS lifetime, consume a valid challenge once, and keep listings unpublished pending moderation. Runtime tests and live DNS behavior remain unverified.
- Seller listing editing and soft withdrawal endpoints are committed. Edits unpublish the listing and reset moderation to pending; withdrawal preserves the record/audit history. Runtime behavior remains unverified. Full admin tooling is still incomplete; bootstrap approve/reject requires a separate admin token and refuses approval until ownership is verified.
- Seller inventory currently uses a single configured bootstrap token; do not issue it to multiple sellers. A real account/session/role system is required for multi-seller production use.
- Payments, transfers, abuse prevention, and auctions remain unimplemented.

## Next actions
1. Run the full test suite and verify the new DNS endpoint tests; confirm resolver behavior against a controlled DNS zone.
2. Replace bootstrap seller/admin tokens with real account/session/role boundaries before production.
3. Connect marketplace frontend to seller submission and public inventory.
4. Verify migrations/tests/CI and add smoke coverage.
5. Build transaction/payment/transfer abstractions, then live registrar/hosting integrations.

## Update discipline
Progress must reflect verified repository deliverables, not effort estimates. Never mark an external integration or runtime test as complete until it has actually been verified.
