# DomHostify — Project Status

**Last updated:** 2026-10-16  
**Current phase:** Phase 4 — Marketplace security foundation / public catalog hardening  
**Overall progress:** 90%

## Executive status
DomHostify now has a tested persistent catalog/API foundation for domains, hosting, and marketplace inventory. Marketplace seller, ownership, moderation, Make Offer, and Buy Now reservation flows are implemented behind bootstrap authentication boundaries. The public frontend reads only verified/approved persistent data and does not expose private credentials.

The latest GitHub Actions run for commit `c4917b0d5b0232a4c580d58a3f5506e7e170a323` passed the clean Alembic upgrade → downgrade → upgrade cycle and **56 tests**. One Starlette/httpx deprecation warning remains. citeturn734file0

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Core domain, hosting and marketplace pillars documented |
| PRD and user journeys | In progress | 82% | Seller/listing/offer lifecycle represented |
| Architecture and data boundaries | In progress | 80% | Public/private boundaries and marketplace trust gates defined |
| Roadmap and governance | In progress | 92% | Status and migration sequence maintained |
| Security, privacy, compliance | In progress | 80% | Auth boundaries, ownership proof, audit trail; real accounts/abuse controls remain |
| API implementation | In progress | 98% | Persistent catalogs, seller lifecycle, ownership, moderation, offers, reservations and idempotency tested |
| Database and migrations | In progress | 97% | Migrations 0001–0009 pass clean round-trip in CI |
| Frontend | In progress | 60% | Responsive public catalog UI with domain suggestions, stored registrar offers, hosting and marketplace sections |
| Provider/affiliate integrations | In progress | 30% | Affiliate safety foundation; live providers not connected |
| Automated tests and CI | In progress | 98% | 56 tests + migration round-trip passing on latest commit |
| Deployment and monitoring | Not started | 0% | No production deployment verified |

## Verified deliverables
- [x] Domain validation, search and suggestion foundation
- [x] Stored verified registrar-offer comparison endpoint
- [x] Persistent hosting catalog endpoint with verified/active gating
- [x] Persistent marketplace endpoint with active + verified ownership + approved moderation gates
- [x] Marketplace listing detail endpoint with identical public visibility gates
- [x] HTTPS-only allowlisted affiliate redirects with opaque click tracking
- [x] Responsive public frontend
- [x] Frontend domain search displays stored verified registrar offers and keeps live availability explicitly unknown
- [x] Frontend hosting section reads only verified persistent plans
- [x] Frontend marketplace section reads only approved ownership-verified listings
- [x] Frontend configurable API base URL; no private tokens embedded in browser code
- [x] Marketplace lifecycle and audit-event migrations
- [x] Ownership challenge storage with SHA-256 token hashes
- [x] DNS TXT ownership challenge/verification workflow with mocked resolver tests
- [x] Seller listing submission, inventory isolation, editing and soft withdrawal
- [x] Admin approve/reject moderation boundary
- [x] Make Offer workflow, buyer/seller views, decisions, cancellation and transaction audit events
- [x] Buy Now temporary reservation with atomic availability gate
- [x] Buy Now idempotency key and duplicate-request protection
- [x] Admin expiry cleanup for stale unpaid reservations
- [x] Clean database migration round-trip verified in CI
- [x] Latest CI: 56 tests passed, 1 warning

## Not yet implemented / verified
- [ ] Browser/runtime smoke test against a running API
- [ ] Real per-user account/session/role authentication
- [ ] Seller dashboard connected to real user sessions
- [ ] Full admin dashboard and moderation UI
- [ ] Payment-backed checkout
- [ ] Payment webhooks, refunds, disputes and settlement
- [ ] Domain transfer workflow
- [ ] Auctions
- [ ] Live registrar availability and pricing adapters
- [ ] Live hosting provider feeds
- [ ] Production database/deployment/monitoring

## Milestones
- [x] M0 Foundation documentation and repository
- [x] M1 Runnable API/test baseline
- [x] M2 Domain/hosting comparison prototype
- [x] M3 Registrar adapter contract and affiliate safety foundation
- [x] M4 Marketplace visibility lifecycle gates
- [x] M4.1 Audit + ownership challenge foundation
- [x] M4.2 Bootstrap seller listing workflow
- [x] M4.3 Ownership verification API
- [x] M4.3.1 Seller edit/withdraw lifecycle
- [x] M5 Transaction schema and guarded state machine
- [x] M5.1 Make Offer workflow
- [x] M5.2 Buy Now reservation + cancellation
- [x] M5.2.1 Idempotent Buy Now retry protection + expiry cleanup
- [x] M5.4 Public frontend persistent catalogs
- [ ] M5.3 Payment-backed checkout + transfer
- [ ] M6 Live provider integrations
- [ ] M7 Production staging and launch verification

## Next attack sequence
1. Build the seller dashboard UI around a future session-based auth boundary; do not expose bootstrap secrets in frontend code.
2. Add browser smoke automation for the public frontend + API.
3. Replace bootstrap identities with real account/session/role authorization.
4. Add payment-backed Buy Now with webhook/idempotency/refund handling.
5. Connect live registrar/hosting providers and verify external runtime behavior.
6. Deploy staging, add monitoring/alerts, then production launch checks.

## Current limitations
- Domain availability is still unknown until a live registrar adapter is connected.
- Hosting and marketplace inventory is database-supplied and must not be represented as live provider inventory unless verified feeds are connected.
- Seller/buyer/admin credentials are bootstrap server-side tokens, not a multi-user account system.
- Buy Now currently creates a reservation intent only; it does not charge money or transfer a domain.
- Ownership verification has automated mocked-DNS coverage but no controlled live DNS-zone verification yet.
- Browser smoke and live deployment have not been verified.
- CI has one Starlette/httpx deprecation warning; it is non-blocking but should be cleaned up during dependency/test modernization.

## Update discipline
Progress reflects verified repository deliverables, not effort estimates. External integrations and runtime behavior are never marked complete until actually verified.
