# Product Requirements Document (PRD)

- Product: DomHostify
- Version: 0.1
- Status: Initial draft
- Last updated: 2026-10-15

## 1. Vision
Help individuals, creators, founders, and domain investors find, compare, register, and buy domains; choose suitable hosting; and discover premium domains from one transparent platform.

## 2. Problem
Registration, renewal pricing, hosting plans, and premium-domain listings are fragmented across providers. Introductory pricing can obscure renewal costs, and new business owners may not know which option fits.

## 3. Target users
- Entrepreneurs launching a first website or online business.
- Small businesses and creators comparing domain and hosting options.
- Developers and agencies comparing providers.
- Domain investors managing portfolios.
- Buyers searching for registered premium domains.

## 4. Product pillars
1. Domain search and registrar comparison.
2. Hosting plan comparison.
3. Aftermarket domain search and listings.
4. Affiliate attribution and reporting.
5. AI-guided recommendations and launch checklist.
6. Seller portfolio and listing management in a later phase.

## 5. MVP scope
### Must have
- Responsive search experience with domain and hosting entry points.
- Domain search API contract that can return provider-sourced availability and prices.
- Hosting comparison catalog and API.
- Demo data explicitly labelled as illustrative, not live.
- Currency, billing period, introductory price, renewal price when known, source, and last-checked timestamp.
- Affiliate click tracking foundation, with outbound destinations controlled by server-side provider configuration.
- Basic domain aftermarket listing model and browse/search API foundation.
- Health endpoint, input validation, automated tests, environment configuration, and CI.
- Privacy-conscious logging and affiliate disclosures.

### Out of scope for the first MVP
- Holding money, operating escrow, or processing marketplace payouts.
- Automatic domain registration or transfers.
- Live auctions and automated negotiation.
- Unapproved scraping or bypassing provider restrictions.
- Real-time claims without a verified provider check.
- Complex subscriptions and brokerage operations.

## 6. Key user journeys
### A. Find and register a domain
1. User searches a name.
2. System validates and normalizes input.
3. Availability is shown only where a provider checked it; otherwise status remains unknown.
4. Offers compare registration price and renewal/transfer prices when available.
5. User selects a provider and sees an affiliate disclosure.
6. Click is logged with minimal necessary metadata and a safe provider identifier.

### B. Compare hosting
1. User optionally selects site type, traffic, budget, region, and technical needs.
2. Results compare plan features and total costs.
3. Introductory and renewal prices are distinct; missing facts remain unknown.
4. Filters and sorting explain their criteria.
5. User follows a disclosed provider link.

### C. Find a premium domain
1. User searches a domain or keyword.
2. Results distinguish unverified registered domains from verified marketplace listings.
3. Listings show asking price, currency, sale method, and status.
4. Transaction workflows follow only after the marketplace foundation is secure.

### D. AI business-launch guidance (later phase)
The user describes business type, budget, and technical comfort. AI explains domain, hosting, and website-builder options with trade-offs. Sponsorship is disclosed, and the user controls all purchases.

## 7. Functional requirements
- FR-01: Normalize domain input using standards-aware parsing; reject malformed input.
- FR-02: Model provider checks with status, source, timestamp, and freshness rules.
- FR-03: Store offers with currency, billing term, initial price, renewal price, and verification time.
- FR-04: Compare hosting plans using structured features.
- FR-05: Track outbound clicks with opaque IDs; never expose partner secrets to clients.
- FR-06: Support marketplace listing search and listing status.
- FR-07: Validate API inputs and return consistent errors.
- FR-08: Avoid unnecessary personal data in logs.
- FR-09: Provide deployment health/readiness checks.
- FR-10: Test validation, price representation, redirect safety, and comparison behavior.

## 8. Non-functional requirements
- Security: secrets in environment/secret manager; least privilege; safe redirects; patched dependencies.
- Reliability: timeouts and graceful provider failures.
- Transparency: data freshness and uncertainty visible.
- Accessibility: keyboard navigation, labels, readable contrast.
- Performance: pagination, bounded timeouts, and explicit cache freshness.
- Maintainability: typed schemas, migrations, tests, API docs, and architecture decisions.

## 9. Success metrics
- CI tests pass on every change.
- Comparison results include source and freshness metadata.
- Provider failure is shown clearly, not replaced by fabricated results.
- Users can complete a demo domain search and hosting comparison without an account.
- Track search-to-provider-click and qualified conversions where partner reporting exists.
- Track marketplace supply and sales only after those features exist.

## 10. Acceptance criteria for the first usable demo
- API runs locally using documented steps.
- Health endpoint returns the documented success response.
- Search/compare endpoints return validated demo records clearly labelled as demo data.
- Invalid input produces a useful client error.
- Automated tests pass.
- No live-data, affiliate-approval, or availability claims are made without verification.
- README and status reflect actual implementation.
