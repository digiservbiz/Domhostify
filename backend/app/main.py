"""DomHostify API bootstrap.

All catalog entries are illustrative demo data. Live provider adapters are not
configured, so domain availability must remain unknown.
"""
import hashlib
import hmac
import os
import re
import uuid
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.app.database import AffiliateClick as DBAffiliateClick, HostingPlanRecord as DBHostingPlan, MarketplaceListing as DBMarketplaceListing, OwnershipChallenge as DBOwnershipChallenge, RegistrarOffer as DBRegistrarOffer, get_db, utc_now
from backend.app.marketplace import add_listing_audit_event
from backend.app.providers import DemoRegistrarProvider
from backend.app.ownership_api import router as ownership_router
from backend.app.transactions_api import router as transactions_router

app = FastAPI(title="DomHostify API", description="Domain discovery, hosting comparison, and domain marketplace API. Catalog entries currently use illustrative demo data, not live offers.", version="0.3.0")
app.include_router(ownership_router)
app.include_router(transactions_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5500,http://127.0.0.1:5500").split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_DEMO_REGISTRAR = DemoRegistrarProvider()


def normalize_domain_query(value: str) -> str:
    candidate = value.strip().lower().rstrip(".")
    if not candidate or len(candidate) > 253:
        raise ValueError("Enter a valid domain name.")
    if any(char.isspace() for char in candidate) or any(char in candidate for char in "/\\:@?#"):
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


class PersistentMarketplaceListing(BaseModel):
    id: int
    domain: str
    asking_price: float = Field(ge=0)
    currency: str
    sale_type: str
    listing_status: str
    ownership_status: str
    moderation_status: str
    updated_at: str | None = None
    data_status: str = "database"


class SellerListingCreate(BaseModel):
    domain: str = Field(min_length=3, max_length=253)
    asking_price: float = Field(ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    sale_type: str = Field(default="make_offer", min_length=1, max_length=30)


class AdminListingReview(BaseModel):
    decision: str = Field(min_length=1, max_length=20)
    note: str | None = Field(default=None, max_length=500)


class SellerListingUpdate(BaseModel):
    asking_price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    sale_type: str | None = Field(default=None, min_length=1, max_length=30)


class PersistentHostingPlan(BaseModel):
    id: int
    provider_key: str
    plan_name: str
    site_type: str
    introductory_price: float = Field(ge=0)
    renewal_price: float | None = Field(default=None, ge=0)
    currency: str
    billing_period: str
    storage: str
    support: str
    checked_at: str | None = None
    source_status: str = "verified"
    data_status: str = "database"


class RegistrarOfferResult(BaseModel):
    id: int
    domain: str
    registrar_key: str
    availability: str
    registration_price: float = Field(ge=0)
    renewal_price: float | None = Field(default=None, ge=0)
    currency: str
    checked_at: str | None = None
    source_status: str = "verified"
    data_status: str = "database"


DEMO_HOSTING_PLANS = [
    HostingPlan(provider="ExampleHost", plan_name="Starter Web", site_type="Portfolio or small business", introductory_price=3.99, renewal_price=7.99, billing_period="month", storage="20 GB SSD (illustrative)", support="Email support (illustrative)"),
    HostingPlan(provider="ExampleCloud", plan_name="Business Managed", site_type="Business site or growing store", introductory_price=9.99, renewal_price=14.99, billing_period="month", storage="50 GB SSD (illustrative)", support="Priority support (illustrative)"),
]
DEMO_LISTINGS = [
    MarketplaceListing(domain="examplebrand.com", asking_price=2500.00, sale_type="buy_now"),
    MarketplaceListing(domain="sampleproject.io", asking_price=850.00, sale_type="make_offer"),
]


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "domhostify-api"}


@app.get("/ready", tags=["operations"])
def ready() -> dict[str, str]:
    return {"status": "ready", "dependencies": "no external dependencies configured"}


@app.get("/api/v1/domains/search", response_model=list[DomainSearchResult], tags=["domains"])
def search_domains(q: str = Query(min_length=2, max_length=253)) -> list[DomainSearchResult]:
    try:
        candidate = normalize_domain_query(q)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result = _DEMO_REGISTRAR.check_domain(candidate)
    return [DomainSearchResult(domain=result.domain, availability=result.availability, source_status=result.source_status, provider_key=result.provider_key, checked_at=result.checked_at, note=result.note)]


@app.get("/api/v1/domains/suggestions", response_model=list[DomainSearchResult], tags=["domains"])
def suggest_domain_extensions(q: str = Query(min_length=1, max_length=63), extensions: str = Query(default="com,net,org,io", max_length=100)) -> list[DomainSearchResult]:
    base = q.strip().lower()
    if not _LABEL_RE.fullmatch(base):
        raise HTTPException(status_code=422, detail="Enter a single domain label without an extension or URL components.")
    requested = [item.strip().lower().lstrip(".") for item in extensions.split(",")]
    if not requested or len(requested) > 10 or any(not item or not _LABEL_RE.fullmatch(item) for item in requested):
        raise HTTPException(status_code=422, detail="Choose between 1 and 10 valid domain extensions.")
    results = []
    for extension in list(dict.fromkeys(requested)):
        domain = normalize_domain_query(f"{base}.{extension}")
        result = _DEMO_REGISTRAR.check_domain(domain)
        results.append(DomainSearchResult(domain=result.domain, availability=result.availability, source_status=result.source_status, provider_key=result.provider_key, checked_at=result.checked_at, note=result.note))
    return results


_AFFILIATE_ENV_KEYS = {"examplehost": "AFFILIATE_URL_EXAMPLEHOST", "examplecloud": "AFFILIATE_URL_EXAMPLECLOUD"}


def _approved_affiliate_destination(provider_key: str) -> str | None:
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


def _require_admin_auth(authorization: str | None = Header(default=None)) -> str:
    """Bootstrap admin boundary; disabled until a distinct server-side token is configured."""
    configured = os.getenv("DOMHOSTIFY_ADMIN_API_TOKEN", "").strip()
    if not configured:
        raise HTTPException(status_code=503, detail="Admin authentication is not configured.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer authentication required.")
    supplied = authorization[7:].strip()
    if not supplied or not hmac.compare_digest(supplied, configured):
        raise HTTPException(status_code=401, detail="Invalid admin credentials.")
    return hashlib.sha256(supplied.encode("utf-8")).hexdigest()[:32]


def _require_seller_auth(authorization: str | None = Header(default=None)) -> str:
    """Bootstrap seller boundary; disabled until a server-side token is configured."""
    configured = os.getenv("DOMHOSTIFY_SELLER_API_TOKEN", "").strip()
    if not configured:
        raise HTTPException(status_code=503, detail="Seller authentication is not configured.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer authentication required.")
    supplied = authorization[7:].strip()
    if not supplied or not hmac.compare_digest(supplied, configured):
        raise HTTPException(status_code=401, detail="Invalid seller credentials.")
    return hashlib.sha256(supplied.encode("utf-8")).hexdigest()[:32]


@app.get("/api/v1/affiliate/{provider_key}", tags=["affiliate"])
def affiliate_redirect(provider_key: str, db: Session = Depends(get_db)) -> RedirectResponse:
    normalized_key = provider_key.strip().lower()
    destination = _approved_affiliate_destination(normalized_key)
    if destination is None:
        raise HTTPException(status_code=503, detail="Affiliate destination is not configured or is invalid.")
    click = DBAffiliateClick(click_id=str(uuid.uuid4()), provider_key=normalized_key)
    try:
        db.add(click)
        db.commit()
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Affiliate tracking database is not initialized. Apply database migrations first.") from exc
    return RedirectResponse(url=destination, status_code=302)


@app.post("/api/v1/marketplace/seller/listings", response_model=PersistentMarketplaceListing, status_code=201, tags=["marketplace"])
def submit_seller_listing(payload: SellerListingCreate, seller_ref: str = Depends(_require_seller_auth), db: Session = Depends(get_db)) -> PersistentMarketplaceListing:
    """Submit a seller listing into review; never auto-approves or verifies ownership."""
    try:
        domain = normalize_domain_query(payload.domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    currency = payload.currency.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise HTTPException(status_code=422, detail="Currency must be a three-letter ISO-style code.")
    sale_type = payload.sale_type.strip().lower()
    if sale_type not in {"buy_now", "make_offer"}:
        raise HTTPException(status_code=422, detail="Sale type must be buy_now or make_offer.")
    listing = DBMarketplaceListing(domain=domain, asking_price=payload.asking_price, currency=currency, sale_type=sale_type, listing_status="pending_review", ownership_status="unverified", moderation_status="pending", seller_ref=seller_ref, active=False)
    try:
        db.add(listing)
        db.flush()
        add_listing_audit_event(db, listing_id=listing.id, event_type="seller_listing_submitted", actor_type="seller", actor_ref=seller_ref)
        db.commit()
        db.refresh(listing)
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
    return PersistentMarketplaceListing(id=listing.id, domain=listing.domain, asking_price=listing.asking_price, currency=listing.currency, sale_type=listing.sale_type, listing_status=listing.listing_status, ownership_status=listing.ownership_status, moderation_status=listing.moderation_status, updated_at=listing.updated_at.isoformat() if listing.updated_at else None)


@app.get("/api/v1/marketplace/seller/listings", response_model=list[PersistentMarketplaceListing], tags=["marketplace"])
def list_seller_listings(seller_ref: str = Depends(_require_seller_auth), db: Session = Depends(get_db)) -> list[PersistentMarketplaceListing]:
    """Return only listings belonging to the authenticated bootstrap seller identity."""
    statement = select(DBMarketplaceListing).where(DBMarketplaceListing.seller_ref == seller_ref).order_by(DBMarketplaceListing.created_at.desc()).limit(100)
    try:
        records = db.scalars(statement).all()
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
    return [
        PersistentMarketplaceListing(
            id=r.id,
            domain=r.domain,
            asking_price=r.asking_price,
            currency=r.currency,
            sale_type=r.sale_type,
            listing_status=r.listing_status,
            ownership_status=r.ownership_status,
            moderation_status=r.moderation_status,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
        )
        for r in records
    ]


@app.patch("/api/v1/marketplace/seller/listings/{listing_id}", response_model=PersistentMarketplaceListing, tags=["marketplace"])
def update_seller_listing(
    listing_id: int,
    payload: SellerListingUpdate,
    seller_ref: str = Depends(_require_seller_auth),
    db: Session = Depends(get_db),
) -> PersistentMarketplaceListing:
    """Edit an owned listing; changes unpublish it and require a fresh moderation decision."""
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide at least one field to update.")
    if any(value is None for value in changes.values()):
        raise HTTPException(status_code=422, detail="Updated fields cannot be null.")
    if "currency" in changes:
        changes["currency"] = changes["currency"].strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", changes["currency"]):
            raise HTTPException(status_code=422, detail="Currency must be a three-letter ISO-style code.")
    if "sale_type" in changes:
        changes["sale_type"] = changes["sale_type"].strip().lower()
        if changes["sale_type"] not in {"buy_now", "make_offer"}:
            raise HTTPException(status_code=422, detail="Sale type must be buy_now or make_offer.")
    try:
        listing = db.scalar(select(DBMarketplaceListing).where(
            DBMarketplaceListing.id == listing_id,
            DBMarketplaceListing.seller_ref == seller_ref,
        ))
        if listing is None:
            raise HTTPException(status_code=404, detail="Marketplace listing not found.")
        if listing.listing_status == "withdrawn":
            raise HTTPException(status_code=409, detail="Withdrawn listings cannot be edited.")
        for field, value in changes.items():
            setattr(listing, field, value)
        listing.active = False
        listing.listing_status = "pending_review"
        listing.moderation_status = "pending"
        add_listing_audit_event(
            db, listing_id=listing.id, event_type="seller_listing_updated",
            actor_type="seller", actor_ref=seller_ref,
            event_note="Listing changes submitted for renewed moderation",
        )
        db.commit()
        db.refresh(listing)
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
    return PersistentMarketplaceListing(
        id=listing.id, domain=listing.domain, asking_price=listing.asking_price,
        currency=listing.currency, sale_type=listing.sale_type,
        listing_status=listing.listing_status, ownership_status=listing.ownership_status,
        moderation_status=listing.moderation_status,
        updated_at=listing.updated_at.isoformat() if listing.updated_at else None,
    )


@app.delete("/api/v1/marketplace/seller/listings/{listing_id}", response_model=PersistentMarketplaceListing, tags=["marketplace"])
def withdraw_seller_listing(
    listing_id: int,
    seller_ref: str = Depends(_require_seller_auth),
    db: Session = Depends(get_db),
) -> PersistentMarketplaceListing:
    """Withdraw an owned listing without deleting its audit history or transaction references."""
    try:
        listing = db.scalar(select(DBMarketplaceListing).where(
            DBMarketplaceListing.id == listing_id,
            DBMarketplaceListing.seller_ref == seller_ref,
        ))
        if listing is None:
            raise HTTPException(status_code=404, detail="Marketplace listing not found.")
        if listing.listing_status == "withdrawn":
            return PersistentMarketplaceListing(
                id=listing.id, domain=listing.domain, asking_price=listing.asking_price,
                currency=listing.currency, sale_type=listing.sale_type,
                listing_status=listing.listing_status, ownership_status=listing.ownership_status,
                moderation_status=listing.moderation_status,
                updated_at=listing.updated_at.isoformat() if listing.updated_at else None,
            )
        listing.active = False
        listing.listing_status = "withdrawn"
        listing.moderation_status = "withdrawn"
        pending_challenges = db.scalars(select(DBOwnershipChallenge).where(
            DBOwnershipChallenge.listing_id == listing.id,
            DBOwnershipChallenge.status == "pending",
        )).all()
        for challenge in pending_challenges:
            challenge.status = "superseded"
        add_listing_audit_event(
            db, listing_id=listing.id, event_type="seller_listing_withdrawn",
            actor_type="seller", actor_ref=seller_ref,
        )
        db.commit()
        db.refresh(listing)
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
    return PersistentMarketplaceListing(
        id=listing.id, domain=listing.domain, asking_price=listing.asking_price,
        currency=listing.currency, sale_type=listing.sale_type,
        listing_status=listing.listing_status, ownership_status=listing.ownership_status,
        moderation_status=listing.moderation_status,
        updated_at=listing.updated_at.isoformat() if listing.updated_at else None,
    )


@app.post("/api/v1/admin/marketplace/listings/{listing_id}/review", response_model=PersistentMarketplaceListing, tags=["admin"])
def review_marketplace_listing(
    listing_id: int,
    payload: AdminListingReview,
    admin_ref: str = Depends(_require_admin_auth),
    db: Session = Depends(get_db),
) -> PersistentMarketplaceListing:
    """Approve only verified ownership; rejection always removes public visibility."""
    decision = payload.decision.strip().lower()
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=422, detail="Decision must be approve or reject.")
    try:
        listing = db.get(DBMarketplaceListing, listing_id)
        if listing is None:
            raise HTTPException(status_code=404, detail="Marketplace listing not found.")
        if decision == "approve":
            if listing.ownership_status != "verified":
                raise HTTPException(status_code=409, detail="Ownership must be verified before approval.")
            listing.moderation_status = "approved"
            listing.listing_status = "active"
            listing.active = True
            event_type = "admin_listing_approved"
        else:
            listing.moderation_status = "rejected"
            listing.listing_status = "rejected"
            listing.active = False
            event_type = "admin_listing_rejected"
        add_listing_audit_event(
            db,
            listing_id=listing.id,
            event_type=event_type,
            actor_type="admin",
            actor_ref=admin_ref,
            event_note=payload.note.strip() if payload.note else None,
        )
        db.commit()
        db.refresh(listing)
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
    return PersistentMarketplaceListing(
        id=listing.id,
        domain=listing.domain,
        asking_price=listing.asking_price,
        currency=listing.currency,
        sale_type=listing.sale_type,
        listing_status=listing.listing_status,
        ownership_status=listing.ownership_status,
        moderation_status=listing.moderation_status,
        updated_at=listing.updated_at.isoformat() if listing.updated_at else None,
    )


@app.get("/api/v1/hosting/plans", response_model=list[HostingPlan], tags=["hosting"])
def list_hosting_plans(site_type: str | None = Query(default=None, max_length=80), max_price: float | None = Query(default=None, ge=0)) -> list[HostingPlan]:
    plans = DEMO_HOSTING_PLANS
    if site_type:
        needle = site_type.casefold().strip()
        plans = [plan for plan in plans if needle in plan.site_type.casefold()]
    if max_price is not None:
        plans = [plan for plan in plans if plan.introductory_price <= max_price]
    return plans


@app.get("/api/v1/marketplace/listings", response_model=list[MarketplaceListing], tags=["marketplace"])
def list_marketplace_listings(q: str | None = Query(default=None, max_length=253), max_price: float | None = Query(default=None, ge=0)) -> list[MarketplaceListing]:
    listings = DEMO_LISTINGS
    if q:
        needle = q.casefold().strip()
        listings = [item for item in listings if needle in item.domain.casefold()]
    if max_price is not None:
        listings = [item for item in listings if item.asking_price <= max_price]
    return listings


@app.get("/api/v1/hosting/persistent-plans", response_model=list[PersistentHostingPlan], tags=["hosting"])
def list_persistent_hosting_plans(site_type: str | None = Query(default=None, max_length=120), max_price: float | None = Query(default=None, ge=0), db: Session = Depends(get_db)) -> list[PersistentHostingPlan]:
    statement = select(DBHostingPlan).where(DBHostingPlan.active.is_(True), DBHostingPlan.source_status == "verified", DBHostingPlan.introductory_price.is_not(None))
    if site_type and site_type.strip():
        statement = statement.where(DBHostingPlan.site_type.ilike(f"%{site_type.strip()}%"))
    if max_price is not None:
        statement = statement.where(DBHostingPlan.introductory_price <= max_price)
    try:
        records = db.scalars(statement.order_by(DBHostingPlan.introductory_price.asc()).limit(100)).all()
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Hosting catalog database is not initialized. Apply database migrations first.") from exc
    return [PersistentHostingPlan(id=r.id, provider_key=r.provider_key, plan_name=r.plan_name, site_type=r.site_type, introductory_price=r.introductory_price, renewal_price=r.renewal_price, currency=r.currency, billing_period=r.billing_period, storage=r.storage, support=r.support, checked_at=r.checked_at.isoformat() if r.checked_at else None, source_status=r.source_status) for r in records]


@app.get("/api/v1/marketplace/persistent-listings", response_model=list[PersistentMarketplaceListing], tags=["marketplace"])
def list_persistent_marketplace_listings(q: str | None = Query(default=None, max_length=253), max_price: float | None = Query(default=None, ge=0), db: Session = Depends(get_db)) -> list[PersistentMarketplaceListing]:
    statement = select(DBMarketplaceListing).where(DBMarketplaceListing.active.is_(True), DBMarketplaceListing.listing_status == "active", DBMarketplaceListing.ownership_status == "verified", DBMarketplaceListing.moderation_status == "approved")
    if q and q.strip():
        statement = statement.where(DBMarketplaceListing.domain.ilike(f"%{q.strip()}%"))
    if max_price is not None:
        statement = statement.where(DBMarketplaceListing.asking_price <= max_price)
    try:
        records = db.scalars(statement.order_by(DBMarketplaceListing.created_at.desc()).limit(100)).all()
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
    return [PersistentMarketplaceListing(id=r.id, domain=r.domain, asking_price=r.asking_price, currency=r.currency, sale_type=r.sale_type, listing_status=r.listing_status, ownership_status=r.ownership_status, moderation_status=r.moderation_status, updated_at=r.updated_at.isoformat() if r.updated_at else None) for r in records]


@app.get("/api/v1/marketplace/persistent-listings/{listing_id}", response_model=PersistentMarketplaceListing, tags=["marketplace"])
def get_persistent_marketplace_listing(listing_id: int, db: Session = Depends(get_db)) -> PersistentMarketplaceListing:
    statement = select(DBMarketplaceListing).where(DBMarketplaceListing.id == listing_id, DBMarketplaceListing.active.is_(True), DBMarketplaceListing.listing_status == "active", DBMarketplaceListing.ownership_status == "verified", DBMarketplaceListing.moderation_status == "approved")
    try:
        record = db.scalar(statement)
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
    if record is None:
        raise HTTPException(status_code=404, detail="Marketplace listing not found.")
    return PersistentMarketplaceListing(id=record.id, domain=record.domain, asking_price=record.asking_price, currency=record.currency, sale_type=record.sale_type, listing_status=record.listing_status, ownership_status=record.ownership_status, moderation_status=record.moderation_status, updated_at=record.updated_at.isoformat() if record.updated_at else None)


@app.get("/api/v1/domains/offers", response_model=list[RegistrarOfferResult], tags=["domains"])
def list_verified_registrar_offers(domain: str = Query(min_length=4, max_length=253), db: Session = Depends(get_db)) -> list[RegistrarOfferResult]:
    try:
        normalized_domain = normalize_domain_query(domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    statement = select(DBRegistrarOffer).where(DBRegistrarOffer.domain == normalized_domain, DBRegistrarOffer.source_status == "verified", DBRegistrarOffer.registration_price.is_not(None)).order_by(DBRegistrarOffer.registration_price.asc()).limit(100)
    try:
        records = db.scalars(statement).all()
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Registrar catalog database is not initialized. Apply database migrations first.") from exc
    return [RegistrarOfferResult(id=r.id, domain=r.domain, registrar_key=r.registrar_key, availability=r.availability, registration_price=r.registration_price, renewal_price=r.renewal_price, currency=r.currency, checked_at=r.checked_at.isoformat() if r.checked_at else None, source_status=r.source_status) for r in records]
