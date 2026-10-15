# Architecture

- Status: Proposed baseline, subject to implementation evidence
- Last updated: 2026-10-15

## 1. Principles
- Separate catalog data from provider adapters and affiliate attribution.
- Treat provider data as external, potentially stale, and sometimes unavailable.
- Keep marketplace purchases/transfers separate from affiliate referrals.
- Make demo data impossible to confuse with live offers.
- Start with a modular monolith, not premature microservices.

## 2. Logical modules
1. API application: routes, validation, errors, health/readiness.
2. Domain search: normalized query, availability abstraction, provider aggregation.
3. Registrar catalog: provider metadata and registration/renewal/transfer offers.
4. Hosting catalog: providers, plans, normalized features, pricing.
5. Affiliate attribution: approved destinations, opaque click IDs, reporting.
6. Aftermarket marketplace: domain listings, ownership checks, listing search/status.
7. AI recommendations: later; explain factors and disclose sponsorship.
8. Identity/admin: later; roles, audit trail, moderation, seller tools.

## 3. Initial deployment shape
- backend/: Python FastAPI application
- backend/tests/: pytest suite
- docs/: product and engineering documentation
- frontend/: planned web client after API contracts stabilize
- PostgreSQL for persistent production data, with migrations when introduced.

## 4. Provider adapter contract (planned)
Each adapter should return provider key/name, product type, requested domain or plan, availability status (available/unavailable/unknown/error), price and ISO currency where supplied, billing period, introductory/renewal/transfer distinctions, source reference where permitted, checked-at timestamp, freshness metadata, affiliate metadata, and structured errors.

Never turn timeouts, missing data, or stale data into a positive availability claim.

## 5. Planned data entities
Provider, AvailabilityCheck, RegistrarOffer, HostingProvider, HostingPlan, HostingOffer, AffiliateClick, MarketplaceListing, and later User, SellerPortfolio, Offer, Auction, Transaction, TransferCase, and AuditEvent.

Use migrations for schema changes. Monetary values require decimal-safe storage and explicit currency.

## 6. Planned API areas
- GET /health — liveness
- GET /ready — readiness when dependencies exist
- GET /api/v1/domains/search?q=... — provider-checked results or clearly labelled demo results
- GET /api/v1/hosting/plans — filterable hosting catalog
- GET /api/v1/marketplace/listings — aftermarket browse/search
- GET /r/{provider_key} — safe configured affiliate redirect and click event

These are targets, not claims that endpoints already exist. Redirect destinations must come from trusted server configuration, never arbitrary user input.

## 7. External dependencies
Registrar APIs/data feeds, hosting catalogs, affiliate programs, affiliate reporting, and later identity, payment/escrow, transfer, email, and analytics providers.

Select integrations based on access, commercial terms, region, price freshness, rate limits, and attribution support.

## 8. Security boundaries
- No secrets in Git.
- Strict allowlist for affiliate destinations.
- Rate limits and timeouts on search and redirects.
- Validate domains; guard against open redirects and server-side request forgery.
- Minimize click metadata and define retention.
- Authenticate and authorize seller/admin writes.
- Audit privileged changes.
