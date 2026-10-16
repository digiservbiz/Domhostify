# DomHostify — Project Status

**Last updated:** 2026-10-16  
**Current phase:** Phase 4 — Marketplace security foundation / payment safety boundary  
**Overall progress:** 90%

## Executive status
DomHostify has a tested persistent catalog/API foundation and marketplace listing, ownership, moderation, Make Offer, and Buy Now reservation flows. The latest previously verified CI run passed 56 tests and the clean migration round-trip. Payment foundation files and transaction state-machine guards have now been committed. Webhook signature parsing was hardened to reject malformed and non-ASCII signatures safely. Payment validation now rejects boolean/non-integer transaction IDs and oversized monetary amounts before normalization. New payment and trusted-actor tests still require CI verification, so the overall percentage remains 90% until results are confirmed.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Domain, hosting and marketplace pillars documented |
| Architecture and data boundaries | In progress | 82% | Payment contract added; provider and auth boundaries remain |
| Security, privacy, compliance | In progress | 81% | Bootstrap auth remains; provider-specific webhook/replay controls pending |
| API implementation | In progress | 98% | Catalog and marketplace APIs implemented; live checkout is not |
| Database and migrations | In progress | 97% | Migrations 0001–0009 previously passed CI round-trip |
| Frontend | In progress | 60% | Public catalog UI; browser smoke and authenticated dashboards pending |
| Provider/affiliate integrations | In progress | 32% | Safe payment abstraction added; no live payment or domain provider |
| Automated tests and CI | In progress | 98% | Previous 56-test run passed; new payment tests awaiting CI |
| Deployment and monitoring | Not started | 0% | No production deployment verified |

## Verified existing deliverables
- [x] Persistent domain, hosting, and approved marketplace catalog endpoints
- [x] Responsive public frontend with explicit unknown availability states
- [x] Seller listing lifecycle, ownership challenge, moderation, and audit events
- [x] Make Offer and Buy Now reservation/idempotency flows
- [x] Clean database migration round-trip in prior CI
- [x] No private bootstrap tokens embedded in frontend code
- [x] Provider-neutral payment request/result contract
- [x] Payment amount/currency/idempotency validation, including numeric bounds and strict transaction ID typing
- [x] Disabled-by-default payment provider that cannot report success
- [x] Generic HMAC-SHA256 webhook signature helper
- [x] Payment-related state transitions restricted to trusted system/provider/admin actors
- [x] Tests added for buyer/seller spoofing attempts against payment transitions
- [ ] New payment and transaction-guard tests confirmed by CI

## Remaining release blockers
- [ ] Browser/runtime smoke test against a running API
- [ ] Real per-user account/session/role authentication
- [ ] Seller dashboard connected to real sessions and full admin UI
- [ ] Real payment provider, checkout endpoint, provider-specific signed webhook handling, refunds/disputes/reconciliation
- [ ] Domain transfer workflow
- [ ] Live registrar availability and pricing adapters
- [ ] Live hosting provider feeds
- [ ] Production database, deployment, monitoring, and launch verification
- [ ] Auctions

## Next attack sequence
1. Verify new payment and trusted-actor tests and the complete CI run.
2. Implement real account/session/role authorization.
3. Add browser smoke automation for public frontend + API.
4. Integrate a chosen payment provider only after configuration and provider-specific webhook tests.
5. Connect live registrar/hosting providers.
6. Deploy staging, add monitoring/alerts, and complete production launch checks.

## Current limitations
- Domain availability is unknown until a live registrar adapter is connected.
- Hosting and marketplace inventory is database-supplied, not automatically live provider inventory.
- Seller/buyer/admin access remains bootstrap server-side tokens, not a multi-user account system.
- Buy Now creates a temporary reservation only; no payment is collected and no domain is transferred.
- The payment module is an integration boundary only, not live checkout.
- Browser smoke and live deployment have not been verified.

Progress reflects verified deliverables, not effort estimates. Do not mark external integrations or runtime behavior complete until verified.
