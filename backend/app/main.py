"""DomHostify API bootstrap.

All catalog entries are illustrative demo data. Live provider adapters are not
configured, so domain availability must remain unknown.
"""
import os
import re
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from backend.app.providers import DemoRegistrarProvider

app = FastAPI(
    title="DomHostify API",
    description=(
        "Domain discovery, hosting comparison, and domain marketplace API. "
        "Catalog entries currently use illustrative demo data, not live offers."
    ),
    version="0.2.0",
)

# Restrict browser access to common local development origins. Production origins
# must be explicitly configured before deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5500,http://127.0.0.1:5500",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)

_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_DEMO_REGISTRAR = DemoRegistrarProvider()


def normalize_domain_query(value: str) -> str:
    """Normalize a domain candidate and reject malformed hostnames.

    Bare names default to .com for the demo UX. This is not an availability check.
    """
    candidate = value.strip().lower().rstrip(".")
    if not candidate or len(candidate) > 253:
        raise ValueError("Enter a valid domain name.")

    if any(char.isspace() for char in candidate) or any(
        char in candidate for char in "/\\:@?#"
    ):
        raise ValueError("Enter a domain name without spaces, paths, or URL components.")

    if "." not in candidate:
        candidate = f"{candidate}.com"

    labels = candidate.split(".")
    if len(labels) < 2 or any(not _LABEL_RE.fullmatch(label) for label in labels):
        raise ValueError("Enter a valid domain name with valid label characters.")

    tld = labels[-1]
    if len(tld) < 2 and not tld.startswith("xn--"):
        raise ValueError("The domain extension must contain at least two characters.")

    return candidate


class DomainSearchResult(BaseModel):
    domain: str
    availability: str = Field(description="Unknown until a registrar has checked it.")
    source_status: str
    provider_key: str = "demo"
    checked_at: str | None = None
    note: str


class HostingPlan(BaseModel):
    provider: str
    plan_name: str
    site_type: str
    introductory_price: float = Field(ge=0)
    renewal_price: float | None = Field(default=None, ge=0)
    currency: str = "EUR"
    billing_period: str = "month"
    storage: str
    support: str
    data_status: str = "demo"
    affiliate_link_available: bool = False


class MarketplaceListing(BaseModel):
    domain: str
    asking_price: float = Field(ge=0)
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
    MarketplaceListing(domain="examplebrand.com", asking_price=2500.00, sale_type="buy_now"),
    MarketplaceListing(domain="sampleproject.io", asking_price=850.00, sale_type="make_offer"),
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
    q: str = Query(min_length=2, max_length=253, description="Domain name or candidate name"),
) -> list[DomainSearchResult]:
    """Return a demo result; it does not query a registrar."""
    try:
        candidate = normalize_domain_query(q)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result = _DEMO_REGISTRAR.check_domain(candidate)
    return [
        DomainSearchResult(
            domain=result.domain,
            availability=result.availability,
            source_status=result.source_status,
            provider_key=result.provider_key,
            checked_at=result.checked_at,
            note=result.note,
        )
    ]


@app.get("/api/v1/domains/suggestions", response_model=list[DomainSearchResult], tags=["domains"])
def suggest_domain_extensions(
    q: str = Query(min_length=1, max_length=63, description="Single-label brand candidate"),
    extensions: str = Query(default="com,net,org,io", max_length=100),
) -> list[DomainSearchResult]:
    """Return clearly labelled demo checks for a bounded list of extensions."""
    base = q.strip().lower()
    if not _LABEL_RE.fullmatch(base):
        raise HTTPException(
            status_code=422,
            detail="Enter a single domain label without an extension or URL components.",
        )

    requested = [item.strip().lower().lstrip(".") for item in extensions.split(",")]
    if not requested or len(requested) > 10 or any(
        not item or not _LABEL_RE.fullmatch(item) for item in requested
    ):
        raise HTTPException(
            status_code=422,
            detail="Choose between 1 and 10 valid domain extensions.",
        )

    # Preserve order while removing duplicate extensions.
    candidates = list(dict.fromkeys(requested))
    results: list[DomainSearchResult] = []
    for extension in candidates:
        try:
            domain = normalize_domain_query(f"{base}.{extension}")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        result = _DEMO_REGISTRAR.check_domain(domain)
        results.append(
            DomainSearchResult(
                domain=result.domain,
                availability=result.availability,
                source_status=result.source_status,
                provider_key=result.provider_key,
                checked_at=result.checked_at,
                note=result.note,
            )
        )
    return results


_AFFILIATE_ENV_KEYS = {
    "examplehost": "AFFILIATE_URL_EXAMPLEHOST",
    "examplecloud": "AFFILIATE_URL_EXAMPLECLOUD",
}


def _approved_affiliate_destination(provider_key: str) -> str | None:
    """Return a configured HTTPS destination for an allowlisted provider only."""
    env_key = _AFFILIATE_ENV_KEYS.get(provider_key)
    if env_key is None:
        raise HTTPException(status_code=404, detail="Unknown affiliate provider.")
    destination = os.getenv(env_key, "").strip()
    if not destination:
        return None
    parsed = urlparse(destination)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    return destination


@app.get("/api/v1/affiliate/{provider_key}", tags=["affiliate"])
def affiliate_redirect(provider_key: str) -> RedirectResponse:
    """Redirect only to a server-configured, allowlisted HTTPS partner URL."""
    destination = _approved_affiliate_destination(provider_key.strip().lower())
    if destination is None:
        raise HTTPException(
            status_code=503,
            detail="Affiliate destination is not configured or is invalid.",
        )
    return RedirectResponse(url=destination, status_code=302)


@app.get("/api/v1/hosting/plans", response_model=list[HostingPlan], tags=["hosting"])
def list_hosting_plans(
    site_type: str | None = Query(default=None, max_length=80),
    max_price: float | None = Query(default=None, ge=0),
) -> list[HostingPlan]:
    """List illustrative plans; these are not real provider offers."""
    plans = DEMO_HOSTING_PLANS
    if site_type:
        needle = site_type.casefold().strip()
        plans = [plan for plan in plans if needle in plan.site_type.casefold()]
    if max_price is not None:
        plans = [plan for plan in plans if plan.introductory_price <= max_price]
    return plans


@app.get("/api/v1/marketplace/listings", response_model=list[MarketplaceListing], tags=["marketplace"])
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
