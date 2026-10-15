# DomHostify

**Domain discovery, registrar and hosting comparison, and domain aftermarket marketplace.**

DomHostify helps people move from a business idea to an online presence: find a domain, compare registration providers, compare hosting plans, and discover registered domains listed for sale. AI-assisted recommendations will help users choose based on their needs, budget, and transparent product data.

## Product pillars
1. Domain search with availability and registration, renewal, and transfer pricing.
2. Hosting plan comparison with renewal costs, resources, support, and suitability.
3. Domain aftermarket listings, with Buy Now and Make Offer foundations.
4. Affiliate attribution and reporting where partner programs permit it.
5. AI-guided business-launch recommendations with clear sponsorship disclosures.
6. Seller portfolio, listing management, pricing guidance, and analytics.

## Current delivery stage
**Phase 0 — Product and engineering foundation.** The repository was essentially empty at kickoff. See [status.md](status.md), [PRD](docs/PRD.md), and [roadmap](docs/ROADMAP.md).

## Project documentation
- [Product requirements (PRD)](docs/PRD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Status and progress](status.md)
- [Testing strategy](docs/TESTING.md)
- [Security and privacy](docs/SECURITY.md)
- [Development guide](CONTRIBUTING.md)
- [Architecture decision log](docs/DECISIONS.md)

## Proposed initial stack
- API: Python + FastAPI
- Database: PostgreSQL with SQLAlchemy and Alembic migrations
- Tests: pytest
- Frontend: planned web client; choose and scaffold after API contracts stabilize
- Deployment: container-ready, after local tests pass

These are proposed choices until validated during implementation. Keep secrets in environment variables; never commit credentials.

## Product principles
- Distinguish verified live data from estimates, cached data, and demo data.
- Show introductory and renewal prices separately whenever available.
- Label sponsored placements and affiliate links clearly.
- Recommendations should reflect user requirements, not affiliate payout alone.
- Never claim domain availability without a provider check.
- Do not hold buyer funds ourselves in the MVP; payments, escrow, and transfers require additional security and compliance work.

## Development
Start with the PRD, roadmap, and [development guide](CONTRIBUTING.md). Exact local commands will be added with the runnable API scaffold.

## License
No license has been selected. A public repository is not automatically open-source licensed.
