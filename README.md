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
**Phase 2 — Comparison prototype.** The API scaffold, domain input validation, demo endpoints, expanded tests, CI workflow, and responsive HTML/JavaScript prototype are committed. Runtime and CI results are not yet verified. See [status.md](status.md), [PRD](docs/PRD.md), and [roadmap](docs/ROADMAP.md).

## Project documentation
- [Product requirements (PRD)](docs/PRD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Status and progress](status.md)
- [Testing strategy](docs/TESTING.md)
- [Security and privacy](docs/SECURITY.md)
- [Development guide](CONTRIBUTING.md)
- [Architecture decision log](docs/DECISIONS.md)

## Stack
- API: Python + FastAPI
- Tests: pytest + FastAPI TestClient
- CI: GitHub Actions
- Frontend prototype: plain HTML/CSS/JavaScript in `frontend/index.html`
- Planned persistence: PostgreSQL + SQLAlchemy/Alembic after data contracts stabilize

## Run locally
Use Python 3.11 or newer.

1. Create and activate a virtual environment.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Start the API from the repository root: `python -m uvicorn backend.app.main:app --reload`
4. Open `http://127.0.0.1:8000/docs` to explore the API.
5. Serve `frontend/index.html` using a local static server on port 5500 or 5173, or open it directly if your browser allows local fetches.
6. Run tests: `python -m pytest -q`

The frontend expects the API at `http://127.0.0.1:8000`. CORS currently permits common localhost development origins only. Update this intentionally before deployment.

Domain, hosting, and marketplace records are illustrative demo data. Domain search explicitly returns availability as unknown and does not contact a registrar.

## Product principles
- Distinguish verified live data from estimates, cached data, and demo data.
- Show introductory and renewal prices separately whenever available.
- Label sponsored placements and affiliate links clearly.
- Recommendations should reflect user requirements, not affiliate payout alone.
- Never claim domain availability without a provider check.
- Do not hold buyer funds ourselves in the MVP; payments, escrow, and transfers require additional security and compliance work.

## License
No license has been selected. A public repository is not automatically open-source licensed.
