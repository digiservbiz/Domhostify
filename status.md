# DomHostify — Project Status

**Last updated:** 2026-10-19  
**Current phase:** Phase 5 — Staging deployment and release hardening  
**Implementation progress:** 95% (estimate based on implemented scope; not a production-readiness score)

## Executive status

The core authenticated marketplace path is implemented: persistent listings, seller lifecycle management, DNS ownership challenges, admin moderation and audit visibility, Make Offer and Buy Now reservation flows, and buyer/seller/admin session authorization. The last previously verified CI run (#261) passed 95 tests plus migration round-trip checks and runtime-smoke script compilation.

**New deployment work:** a Render staging Blueprint now defines an API service and temporary PostgreSQL database. The repository now includes the psycopg 3 driver and normalizes common managed-Postgres URL schemes. Three focused tests cover URL normalization. These latest changes still need a fresh CI result and the Blueprint has not yet been deployed or validated in Render.

## Workstream tracker

| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 82% | Domain, hosting and marketplace pillars documented |
| Architecture and data boundaries | In progress | 96% | Account/session boundary, payment contract, marketplace auth and admin moderation boundaries added |
| Security, privacy, compliance | In progress | 96% | PBKDF2, opaque sessions, role checks, ownership verification, audit trail and protected admin queue; browser token hardening remains |
| API implementation | In progress | 100% | Core catalog, account, seller, ownership, moderation and transaction APIs implemented; live checkout is not |
| Database and migrations | In progress | 98% | Migrations 0001–0010 committed; managed PostgreSQL URL support added, needs CI/runtime validation |
| Frontend | In progress | 86% | Public catalog, account/seller workspace, ownership controls and admin moderation/audit UI |
| Provider/affiliate integrations | In progress | 32% | Safe affiliate and payment abstractions; no live payment or registrar provider |
| Automated tests and CI | In progress | 100% | Last verified CI #261 had 95 passing tests; new PostgreSQL URL tests are pending fresh CI |
| Deployment and monitoring | In progress | 15% | Render Blueprint and deployment guide committed; service is not yet deployed and monitoring is not configured |

## Verified existing deliverables

- [x] Persistent domain, hosting, and approved marketplace catalog endpoints
- [x] Responsive public frontend with explicit unknown availability states
- [x] Seller listing lifecycle, ownership challenge, moderation, and audit events
- [x] Make Offer and Buy Now reservation/idempotency flows
- [x] Provider-neutral payment request/result contract; no live checkout
- [x] PBKDF2 password hashing and opaque hashed session storage
- [x] Buyer/seller registration, login, logout, session expiry/revocation, and account /me
- [x] Ownership and transaction APIs use session-backed role authorization with legacy bootstrap compatibility
- [x] Focused authenticated seller/buyer/admin marketplace integration coverage
- [x] Opt-in live HTTP runtime smoke script at scripts/runtime_smoke.py
- [x] Dedicated authenticated admin moderation queue and audit endpoints
- [x] Admin UI status filtering, approve/reject actions, refresh and audit display
- [x] Session-aware account frontend with seller listing management and ownership controls
- [x] Render staging Blueprint at render.yaml
- [x] Deployment instructions at docs/DEPLOYMENT.md
- [x] PostgreSQL URL normalization and three focused unit tests

## Current verification gates

- [x] Previous CI run #261 passed migration upgrade/downgrade, smoke-script compilation, and 95 tests
- [ ] Fresh CI run for Render/PostgreSQL deployment changes
- [ ] Apply the Render Blueprint and verify successful build, migration, and healthy service
- [ ] Execute scripts/runtime_smoke.py against the actual staging URL and record results
- [ ] Separate browser end-to-end test for DNS publication/verification, admin moderation, and public listing
- [ ] Production deployment, monitoring, and launch verification

## Remaining release blockers

- [ ] Secure HttpOnly-cookie browser sessions and CSRF protections; deployment-aware CORS/cookie configuration
- [ ] Real payment provider, checkout endpoint, signed webhook handling, refunds/disputes/reconciliation
- [ ] Domain transfer workflow
- [ ] Live registrar availability and pricing adapters
- [ ] Live hosting provider feeds
- [ ] Production database, deployment, monitoring, alerts, and launch verification
- [ ] Auctions

## Next attack sequence

1. Wait for and inspect fresh CI for the staging deployment changes.
2. Deploy the Blueprint in Render, then use the actual service URL to run the runtime smoke script.
3. Fix any deployment or runtime failures and update this file with verified evidence.
4. Harden browser authentication with HttpOnly cookies and CSRF protection while preserving API compatibility where needed.
5. Add a browser end-to-end test for the ownership/moderation/public-listing lifecycle.
6. Select and integrate live registrar, hosting, and payment providers; only then plan production launch and auctions.

## Current limitations

- Domain availability remains unknown until a live registrar adapter is connected.
- Hosting and marketplace inventory is database-supplied, not automatically live provider inventory.
- Buy Now creates a temporary reservation only; no payment is collected and no domain is transferred.
- The payment module is an integration boundary, not live checkout.
- The Render Blueprint is a staging starting point only; it has not been deployed or verified.
- The runtime smoke test creates a temporary seller account, listing, and ownership challenge. It withdraws the listing and revokes the session but does not delete the account or challenge.
- Free staging resources have provider-defined limits and must not be used for production data.

Progress reflects implemented and verified deliverables, not effort estimates. Do not mark external integrations or runtime behavior complete until verified.
