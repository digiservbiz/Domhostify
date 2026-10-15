# DomHostify — Project Status

**Last updated:** 2026-10-15  
**Current phase:** Phase 2 — Domain and hosting comparison prototype  
**Overall progress:** 56% (persistent marketplace visibility now requires ownership and moderation approval, with a listing-detail endpoint and isolated lifecycle tests; runtime tests/CI still require verification)

## Executive status
The repository contains product/engineering documentation, a FastAPI demo API, domain validation tests, a responsive frontend, a registrar adapter contract, an allowlisted affiliate redirect foundation, persistent SQLAlchemy catalog models, privacy-conscious affiliate click tracking, and marketplace lifecycle metadata. Tests and CI have not yet been verified. Persistent catalog endpoints remain database reads only; listing creation/authentication, live provider checks, and production deployment remain unimplemented.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 80% | Core product pillars and MVP documented |
| PRD and user journeys | In progress | 75% | Initial requirements and acceptance criteria drafted |
| Architecture and data boundaries | In progress | 68% | API/frontend boundary, demo-data trust rules, provider contract, and marketplace visibility gates documented in code |
| Roadmap and project governance | In progress | 85% | Core project docs and status tracker maintained |
| Security, privacy, compliance | In progress | 53% | HTTPS-only affiliate destinations, opaque UUID click IDs, ownership/moderation visibility gates; broader abuse controls remain |
| API implementation | In progress | 76% | Catalog reads, affiliate click persistence, marketplace lifecycle visibility, and listing detail reads committed; not runtime-verified |
| Database and migrations | In progress | 68% | Sequential migrations cover registrar offers, hosting plans, affiliate clicks, and marketplace lifecycle metadata; execution remains unverified |
| Frontend | In progress | 35% | Responsive prototype calls comparison APIs; marketplace lifecycle UI not yet connected |
| Provider/affiliate integrations | In progress | 30% | Safe redirect plus persistent click foundation; no live provider integration or affiliate approval verified |
| Automated tests and CI | In progress | 55% | Marketplace ownership/moderation visibility tests plus prior catalog, affiliate, registrar, validation, and CORS tests committed; execution result not verified |
| Deployment and monitoring | Not started | 0% | No deployment verified |

## Verified repository deliverables
- [x] README and project entry point
- [x] PRD, architecture, roadmap, decision log, status, testing, security, and contribution docs
- [x] Python dependency list, environment example, and ignore rules
- [x] FastAPI health and readiness endpoints
- [x] Domain search returns explicit unknown availability and demo source status
- [x] Domain extension suggestions endpoint and tests committed
- [x] Allowlisted affiliate redirect endpoint with HTTPS validation and safety tests committed
- [x] Initial SQLAlchemy registrar-offer and marketplace-listing models committed
- [x] Alembic configuration, revision template, and sequential catalog migrations committed
- [x] Database model safety tests committed
- [x] Read-only persistent marketplace listing endpoint now exposes only active listings with verified ownership and approved moderation status
- [x] Marketplace listing-detail endpoint returns a single publicly visible approved listing or 404
- [x] Marketplace lifecycle fields added for ownership status, moderation status, seller reference, and update timestamp
- [x] Alembic migration `0004_marketplace_lifecycle.py` adds lifecycle fields without rewriting earlier migrations
- [x] Isolated SQLite tests cover marketplace visibility gates and hidden unverified/pending listings
- [x] Read-only registrar offer endpoint filters to verified, priced records, sorts by registration price, and caps responses at 100
- [x] Read-only persistent hosting plan endpoint filters to active, verified, priced records, supports site-type/price filters, sorts by introductory price, and caps responses at 100
- [x] Affiliate redirects persist opaque UUID click IDs without IP address or user-agent fields
- [x] Responsive frontend prototype committed
- [x] Local development CORS origins restricted to common localhost ports
- [x] Production CORS origins can be configured through an environment variable
- [x] pytest suite and GitHub Actions workflow committed
- [ ] Tests executed successfully
- [ ] CI result verified
- [ ] API and frontend smoke-tested together
- [ ] Production origin configuration documented and tested

## Milestones
- [x] M0.1 Confirm product direction and repository access.
- [x] M0.2 Create project documentation structure.
- [ ] M0.3 Finalize MVP acceptance criteria.
- [x] M1.1 Commit API scaffold and health endpoint.
- [x] M1.2 Commit automated tests and CI workflow.
- [x] M1.3 Commit domain validation and comparison endpoints.
- [x] M2.1 Commit demo comparison APIs.
- [x] M2.2 Commit first responsive comparison prototype.
- [ ] M2.3 Run and verify API/frontend end-to-end.
- [x] M3.0 Define registrar adapter contract and safe demo implementation.
- [ ] M3.1 Integrate and verify a real provider after confirming API access and terms.
- [x] M4.0 Add marketplace visibility lifecycle gates.
- [ ] M4.1 Add secure seller listing creation/authentication and ownership verification.
- [ ] M5.1 Deploy a test environment and verify end-to-end.

## Current limitations
- Runtime tests and Alembic migrations have not been executed in this work session.
- Domain search does not contact registrars; availability remains unknown.
- Hosting plans and aftermarket listings are fictional illustrative records until real provider/catalog feeds are connected.
- Affiliate redirects require configured allowlisted HTTPS destinations; click tracking stores only an opaque UUID, provider key, and timestamp.
- Marketplace visibility now requires `active`, `listing_status=active`, `ownership_status=verified`, and `moderation_status=approved`; there is deliberately no public seller write route yet.
- Accounts, seller dashboard, ownership challenges, payments, transfers, and auctions are not implemented.
- Browser prototype assumes the API is running at http://127.0.0.1:8000.
- CI workflow is committed but must run before its status can be claimed as passing.

## Next actions
1. Trigger/verify GitHub Actions and fix any failures.
2. Smoke-test API endpoints and frontend together.
3. Run Alembic upgrade/downgrade verification from a clean database.
4. Build secure seller listing foundations: authentication boundary, ownership verification challenge records, and audit events.
5. Connect marketplace UI to the public approved-listing read endpoints.

## Update discipline
Update this file when milestones change. Progress must reflect verified deliverables, not effort estimates.
