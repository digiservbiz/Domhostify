# DomHostify — Project Status

**Last updated:** 2026-10-15  
**Current phase:** Phase 2 — Domain and hosting comparison prototype  
**Overall progress:** 54% (persistent marketplace, registrar pricing, hosting plans, and privacy-conscious affiliate click persistence are implemented with isolated tests committed; runtime tests/CI still require verification)

## Executive status
The repository contains product/engineering documentation, a FastAPI demo API, domain validation tests, a responsive frontend, a registrar adapter contract, an allowlisted affiliate redirect foundation, persistent SQLAlchemy catalog models, and privacy-conscious affiliate click tracking. Tests and CI have not yet been verified. Persistent catalog endpoints remain database reads only; listing creation/authentication, live provider checks, and production deployment remain unimplemented.

## Workstream tracker
| Workstream | Status | Progress | Notes |
|---|---|---:|---|
| Product vision and scope | In progress | 80% | Core product pillars and MVP documented |
| PRD and user journeys | In progress | 75% | Initial requirements and acceptance criteria drafted |
| Architecture and data boundaries | In progress | 65% | API/frontend boundary, demo-data trust rules, and registrar adapter contract documented |
| Roadmap and project governance | In progress | 85% | Core project docs and status tracker maintained |
| Security, privacy, compliance | In progress | 50% | HTTPS-only affiliate destinations, opaque UUID click IDs, no IP/user-agent persistence; broader abuse controls remain |
| API implementation | In progress | 73% | Catalog reads plus affiliate click persistence committed; not runtime-verified |
| Database and migrations | In progress | 65% | Sequential migrations now cover registrar offers, hosting plans, marketplace listings, and affiliate clicks; execution remains unverified |
| Frontend | In progress | 35% | Responsive prototype now calls extension suggestions for bare names and domain search for full domains; not smoke-tested |
| Provider/affiliate integrations | In progress | 30% | Safe redirect plus persistent click foundation; no live provider integration or affiliate approval verified |
| Automated tests and CI | In progress | 52% | Affiliate persistence, safe missing-schema behavior, hosting catalog, marketplace, registrar, validation, and CORS tests committed; execution result not verified |
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
- [x] Alembic configuration, revision template, and initial catalog migration committed
- [x] README documents database initialization and deployment configuration
- [x] Database model safety tests committed, including database-side defaults and nullable provider pricing
- [x] Read-only persistent marketplace listing endpoint filters to active, published records
- [x] Read-only registrar offer endpoint filters to verified, priced records, sorts by registration price, and caps responses at 100 records
- [x] Read-only persistent hosting plan endpoint filters to active, verified, priced records, supports site-type/price filters, sorts by introductory price, and caps responses at 100
- [x] Additive Alembic migration `0002_hosting_plans.py` creates the hosting catalog without rewriting the initial migration
- [x] Additive Alembic migration `0003_affiliate_clicks.py` creates privacy-conscious click tracking
- [x] Affiliate redirects persist opaque UUID click IDs without IP address or user-agent fields
- [x] Isolated SQLite API tests cover affiliate persistence and safe failure when tracking schema is missing
- [x] Isolated SQLite API tests cover persistent hosting catalog filtering, price ordering, missing-schema handling, and response-size cap
- [x] Persistent marketplace listing responses are capped at 100 records
- [x] Isolated SQLite API tests cover active-only database listing reads, price filtering, and safe failure when schema is missing
- [x] Isolated SQLite API tests cover registrar offer verification filters, price ordering, malformed domain rejection, missing-schema handling, and catalog response-size caps
- [x] Registrar provider contract and safe demo adapter committed
- [x] Provider adapter safety tests committed
- [x] Provider integration requirements documented
- [x] Domain query normalization/validation helper and malformed-input tests committed
- [x] Hosting-plan catalog endpoint and filters
- [x] Marketplace listing endpoint and filters
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
- [ ] M4.1 Expand marketplace listing foundations.
- [ ] M5.1 Deploy a test environment and verify end-to-end.

## Current limitations
- Runtime tests and Alembic migrations have not been executed in this work session.
- Domain search does not contact registrars; availability remains unknown.
- Hosting plans and aftermarket listings are fictional illustrative records until real provider/catalog feeds are connected.
- Affiliate redirects require configured allowlisted HTTPS destinations; click tracking stores only an opaque UUID, provider key, and timestamp. No IP address or user-agent is stored.
- Persistent marketplace, registrar, and hosting endpoints do not contact external providers; no seller listing creation/editing or authentication exists yet. Accounts, seller dashboard, payments, transfers, and auctions are not implemented.
- Browser prototype assumes the API is running at http://127.0.0.1:8000.
- CI workflow is committed but must run before its status can be claimed as passing.
- CORS is configured for local development only; production origins must be configured deliberately.

## Next actions
1. Trigger/verify GitHub Actions and fix any failures.
2. Smoke-test API endpoints and frontend together.
3. Run Alembic upgrade/downgrade verification from a clean database.
4. Add real provider adapter interfaces and provider configuration boundaries without enabling unverified live claims.
5. Build secure seller listing foundations: authentication, ownership verification, moderation state, and audit events.

## Update discipline
Update this file when milestones change. Progress must reflect verified deliverables, not effort estimates.
