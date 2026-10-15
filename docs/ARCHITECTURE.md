# Architecture

- Status: Baseline with registrar adapter contract implemented; broader modules remain proposed
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
6. Aftermarket marketplace: domain listings, ownership checks, listing search/status. Seller ownership endpoints issue hashed one-time DNS TXT challenges and verify through a bounded DNS lookup; verified listings remain pending admin moderation.
7. AI recommendations: later; explain factors and disclose sponsorship.
8. Identity/admin: later; roles, audit trail, moderation, seller tools.

## 3. Initial deployment shape
- backend/: Python FastAPI application
- backend/tests/: pytest suite
- docs/: product and engineering documentation
- frontend/: planned web client after API contracts stabilize
- SQLAlchemy persistence layer with Alembic migrations; use PostgreSQL for production data.

## 4. Provider adapter contract (partially implemented)
Each adapter should return provider key/name, product type, requested domain or plan, availability status (available/unavailable/unknown/error), price and ISO currency where supplied, billing period, introductory/renewal/transfer distinctions, source reference where permitted, checked-at timestamp, freshness metadata, affiliate metadata, and structured errors.

Never turn timeouts, missing data, or stale data into a positive availability claim.

## 5. Planned data entities
Provider, AvailabilityCheck, RegistrarOffer, HostingProvider, HostingPlan, HostingOffer, AffiliateClick, MarketplaceListing, and later User, SellerPortfolio, Offer, Auction, Transaction, TransferCase, and AuditEvent.

Use migrations for schema changes. Monetary values require decimal-safe storage and explicit currency.

## 6. Planned API areas
- GET /health — liveness
- GET /ready — readiness when dependencies exist
- GET /api/v1/domains/search?q=... — clearly labelled demo results
- GET /api/v1/domains/offers?domain=... — persisted registrar pricing records marked verified; no live provider check until a provider is connected
- GET /api/v1/domains/offers?domain=... — persisted verified registrar pricing records; does not perform a live check
- GET /api/v1/hosting/plans — filterable illustrative hosting catalog
- GET /api/v1/hosting/persistent-plans — read-only database catalog of active, verified, priced hosting plans (no live provider calls)
- GET /api/v1/marketplace/listings — demo aftermarket browse/search
- GET /api/v1/marketplace/persistent-listings — read-only database-backed browse of explicitly active listings
- GET /r/{provider_key} — safe configured affiliate redirect and click event

The persistent listing, registrar offer, and hosting-plan endpoints require the Alembic migrations to be applied. The listing endpoint exposes only rows where `active=true` and `listing_status=active`; the hosting endpoint exposes only rows where `active=true`, `source_status=verified`, and introductory price is present. Seller write flows and authorization are not implemented yet. Redirect destinations must come from trusted server configuration, never arbitrary user input.

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


## Marketplace trust workflow
1. Seller submits a listing through the authenticated bootstrap seller endpoint.
2. Listing remains inactive, pending review, and ownership-unverified.
3. Admin review requires the separate `DOMHOSTIFY_ADMIN_API_TOKEN`.
4. Approval is rejected unless ownership is already marked verified; successful approval activates the listing and records an audit event.
5. Rejection sets the listing inactive and non-public, also recording an audit event.
6. DNS challenge generation exists internally, but live DNS lookup/verification is still pending. Never manually mark ownership verified in production without evidence from the verification service.


## Ownership verification service boundary
The repository now includes a validation helper that accepts TXT values obtained by a trusted resolver, checks the challenge status and expiry, compares the SHA-256 proof using constant-time comparison, and consumes a successful challenge exactly once. A successful proof marks the listing ownership as verified and appends an audit event. This helper is not itself a DNS resolver or a public endpoint; live resolver wiring and authenticated challenge/verification routes remain incomplete until tested.
