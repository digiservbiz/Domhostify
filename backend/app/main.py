"""DomHostify API bootstrap.

The current catalog is illustrative demo data, not live provider pricing.
Replace demo repositories with provider-backed adapters only after access and
affiliate terms have been verified.
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="DomHostify API",
    description=(
        "Domain discovery, hosting comparison, and domain marketplace API. "
        "Catalog entries currently use illustrative demo data, not live offers."
    ),
    version="0.1.0",
)


class DomainSearchResult(BaseModel):
    domain: str
    availability: str = Field(description="Demo result only; never a live availability claim.")
    source_status: str
    checked_at: str | None = None
    note: str


class HostingPlan(BaseModel):
    provider: str
    plan_name: str
    site_type: str
    introductory_price: float
    renewal_price: float | None
    currency: str = "EUR"
    billing_period: str = "month"
    storage: str
    support: str
    data_status: str = "demo"
    affiliate_link_available: bool = False


class MarketplaceListing(BaseModel):
    domain: str
    asking_price: float
    currency: str = "EUR"
    sale_type: str
    listing_status: str = "demo"
    data_status: str = "demo"


DEMO_HOSTING_PLANS = [
    HostingPlan(
        provider="ExampleHost",
        plan_name="Starter Web",
        site_type="Portfolio or small business",
        introductory_price=3.99,
        renewal_price=7.99,
        billing_period="month",
        storage="20 GB SSD (illustrative)",
        support="Email support (illustrative)",
    ),
    HostingPlan(
        provider="ExampleCloud",
        plan_name="Business Managed",
        site_type="Business site or growing store",
        introductory_price=9.99,
        renewal_price=14.99,
        billing_period="month",
        storage="50 GB SSD (illustrative)",
        support="Priority support (illustrative)",
    ),
]

DEMO_LISTINGS = [
    MarketplaceListing(
        domain="examplebrand.com",
        asking_price=2500.00,
        sale_type="buy_now",
    ),
    MarketplaceListing(
        domain="sampleproject.io",
        asking_price=850.00,
        sale_type="make_offer",
    ),
]


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    """Liveness check; does not claim external providers are available."""
    return {"status": "ok", "service": "domhostify-api"}


@app.get("/ready", tags=["operations"])
def ready() -> dict[str, str]:
    """Readiness check for the current stateless demo API."""
    return {"status": "ready", "dependencies": "no external dependencies configured"}


@app.get("/api/v1/domains/search", response_model=list[DomainSearchResult], tags=["domains"])
def search_domains(
    q: str = Query(min_length=3, max_length=253, description="Domain name or candidate name"),
) -> list[DomainSearchResult]:
    """Return a clearly labelled demo response until live registrar adapters exist."""
    candidate = q.strip().lower().rstrip(".")
    if not candidate or any(char.isspace() for char in candidate) or "/" in candidate:
        raise HTTPException(status_code=422, detail="Enter a domain name without spaces or paths.")

    if "." not in candidate:
        candidate = f"{candidate}.com"

    # This endpoint intentionally does not pretend to verify availability.
    return [
        DomainSearchResult(
            domain=candidate,
            availability="unknown",
            source_status="demo_only",
            checked_at=None,
            note="Demo response. Availability and pricing have not been checked with a registrar.",
        )
    ]


@app.get("/api/v1/hosting/plans", response_model=list[HostingPlan], tags=["hosting"])
def list_hosting_plans(
    site_type: str | None = Query(default=None, max_length=80),
    max_price: float | None = Query(default=None, ge=0),
) -> list[HostingPlan]:
    """List illustrative plans; these are not real provider offers."""
    plans = DEMO_HOSTING_PLANS
    if site_type:
        needle = site_type.casefold()
        plans = [plan for plan in plans if needle in plan.site_type.casefold()]
    if max_price is not None:
        plans = [plan for plan in plans if plan.introductory_price <= max_price]
    return plans


@app.get(
    "/api/v1/marketplace/listings",
    response_model=list[MarketplaceListing],
    tags=["marketplace"],
)
def list_marketplace_listings(
    q: str | None = Query(default=None, max_length=253),
    max_price: float | None = Query(default=None, ge=0),
) -> list[MarketplaceListing]:
    """Browse illustrative aftermarket listings; no real seller inventory is connected."""
    listings = DEMO_LISTINGS
    if q:
        needle = q.casefold().strip()
        listings = [item for item in listings if needle in item.domain.casefold()]
    if max_price is not None:
        listings = [item for item in listings if item.asking_price <= max_price]
    return listings
