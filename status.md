# DomHostify — Project Status

**Last updated:** 2026-10-15  
**Current phase:** Phase 4 — Marketplace security foundation  
**Overall progress:** 88% (Buy Now reservations now have buyer-scoped idempotency and admin-controlled expiry cleanup; GitHub Actions passes 54 tests; payment, real accounts, providers, and deployment remain outstanding)

## Executive status
The marketplace now has fail-closed bootstrap boundaries for seller, buyer, and admin actions. Sellers can submit, edit, withdraw, verify ownership, and review offers; buyers can submit, inspect, and cancel make-offers. Offers are only accepted on publicly approved listings and every state change is audited. Opaque SHA-256-derived references are used, but the tokens still represent one bootstrap identity each—not real multi-user accounts.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Core marketplace and comparison pillars documented |
| PRD and user journeys | In progress | 80% | Seller submission/review lifecycle now represented |
| Architecture and data boundaries | In progress | 78% | Seller auth boundary and marketplace trust gates defined |
| Roadmap and project governance | In progress | 90% | Status and migration sequence maintained |
| Security, privacy, compliance | In progress | 78% | Seller/admin bootstrap boundaries, hashed one-time DNS proof, bounded DNS lookup, audit trail; full auth/abuse controls remain |
| API implementation | In progress | 98% | Seller lifecycle, DNS verification, admin moderation, Make Offer, atomic Buy Now reservations, idempotent retries, and admin expiry cleanup are CI-tested |
| Database and migrations | In progress | 96% | Migrations `0008_listing_reservations` and `0009_transaction_idempotency` pass the clean-database round-trip; production database verification remains pending |
| Frontend | In progress | 35% | Responsive comparison prototype; seller UI not connected |
| Provider/affiliate integrations | In progress | 30% | Safe affiliate redirect foundation; no live provider access verified |
| Automated tests and CI | In progress | 97% | GitHub Actions passed migration round-trip and 54 tests on 2026-10-15 with one warning; API/frontend smoke tests remain pending |
| Deployment and monitoring | Not started | 0% | No deployment verified |

## Verified repository deliverables
- [x] Persistent marketplace visibility requires active listing + active status + verified ownership + approved moderation
- [x] Marketplace listing detail endpoint enforces the same public visibility gates
- [x] Marketplace lifecycle migration `0004_marketplace_lifecycle.py`
- [x] Listing audit-event model and migration `0005_listing_audit_events.py`
- [x] Audit events avoid IP address and user-agent storage
- [x] Ownership challenge model stores a SHA-256 token hash rather than a raw token
- [x] Ownership challenge migration `0006_ownership_challenges.py`
- [x] Transaction state and append-only event models plus migration `0007_marketplace_transactions.py`
- [x] Buy Now listing reservation fields and migration `0008_listing_reservations.py`
- [x] Buyer-scoped idempotency key and unique index migration `0009_transaction_idempotency.py`
- [x] Admin-authenticated expiry cleanup cancels stale unpaid reservations, clears listing holds, and records an audit event
- [x] Buy Now requires `Idempotency-Key`; retrying the same request returns the same active reservation instead of creating a duplicate
- [x] Buy Now intent endpoint atomically reserves a public Buy Now listing for ten minutes; no payment is collected
- [x] Buyer cancellation releases the matching reservation; CI tests confirm a second intent is blocked until release
- [x] Guarded transaction state-machine helper with allowed-transition checks and event recording
- [x] Transaction tests cover legal transition, illegal transition, completion timestamp, and actor/note validation
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
- [x] Runtime pytest suite verified in GitHub Actions: 54 passed, 1 warning (2026-10-15)
- [x] Alembic clean-database upgrade → downgrade → upgrade verified in GitHub Actions (2026-10-15)
- [x] GitHub Actions CI passed on Buy Now reservation code: 51 passed, 1 warning (2026-10-15)
- [ ] API/frontend smoke test verified
- [ ] Full user/account authentication and authorization implemented
- [x] Authenticated seller DNS TXT challenge and verification endpoints committed (runtime and live DNS behavior still unverified)
- [x] Seller listing editing and soft withdrawal endpoints committed; changes require renewed moderation, withdrawal preserves audit history, and seller isolation is tested
- [ ] Real per-user seller identities implemented (current bootstrap token maps to one seller identity)
- [ ] Seller dashboard implemented
- [ ] Full moderation/admin operations implemented
- [x] Bootstrap admin review endpoint supports approve/reject with audit events
- [x] Bootstrap-authenticated Make Offer submission, buyer offer history/cancellation, seller offer inventory, accept/reject decisions, and transaction audit events committed and CI-tested
- [x] Temporary Buy Now reservation, cancellation release, buyer-scoped idempotency, and admin expiry cleanup implemented and CI-tested
- [ ] Payment-backed Buy Now checkout and real multi-user buyer/seller authorization implemented
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
- [x] M5.0 Transaction schema, event log, and guarded state-machine foundation committed and CI-tested
- [x] M5.1 Bootstrap-authenticated Make Offer API, buyer/seller offer views, decisions, cancellation, and audit trail (CI-tested)
- [x] M5.2 Temporary Buy Now reservation with atomic availability gate and cancellation release (51 tests passing)\n- [ ] M5.3 Payment-backed checkout, idempotency, and registrar transfer workflow
- [ ] M4.4 Moderation/admin workflow (bootstrap approve/reject exists; seller listing edit/withdraw now committed)
- [ ] M5 Transaction workflows
- [ ] M6 Live provider integrations
- [ ] M7 Production staging and launch verification

## Current limitations
- GitHub Actions is green: 49 tests passed with one warning, and Alembic clean-database upgrade → downgrade → upgrade succeeded. Local runtime access and live deployment are not verified.
- The current seller token is a bootstrap server-side credential, not a complete multi-user account/session/role system.
- Domain availability remains unknown because no live registrar is queried.
- Hosting and aftermarket catalog records remain illustrative/database-supplied until verified feeds are connected.
- Authenticated seller ownership-challenge and verification endpoints now exist in code. They issue a 30-minute TXT token, resolve TXT with a 4-second DNS lifetime, consume a valid challenge once, and keep listings unpublished pending moderation. Runtime tests and live DNS behavior remain unverified.
- Seller listing editing and soft withdrawal endpoints are committed. Edits unpublish the listing and reset moderation to pending; withdrawal preserves the record/audit history. Runtime behavior remains unverified. Full admin tooling is still incomplete; bootstrap approve/reject requires a separate admin token and refuses approval until ownership is verified.
- Seller inventory currently uses a single configured bootstrap token; do not issue it to multiple sellers. A real account/session/role system is required for multi-seller production use.
- Make-offer API endpoints and a ten-minute Buy Now reservation intent are implemented using one bootstrap buyer token and one bootstrap seller token. The reservation blocks another intent and is released on buyer cancellation or can be replaced after expiry. No payment obligation is settled, no payment is processed, and no domain is transferred. Payment webhooks, escrow, refunds, disputes, real account auth, abuse prevention, and auctions remain unimplemented.

## Next actions
1. Add API/frontend smoke tests and verify DNS TXT behavior against a controlled authoritative DNS zone.
2. Replace bootstrap buyer/seller/admin tokens with real account/session/role boundaries before production.
3. Connect marketplace frontend to seller management and Make Offer endpoints.
4. Build Buy Now with atomic listing reservation and idempotency.
5. Integrate verified payment webhooks and domain-transfer workflows, then live registrar/hosting providers.

## Update discipline
Progress must reflect verified repository deliverables, not effort estimates. Never mark an external integration or runtime test as complete until it has actually been verified.
