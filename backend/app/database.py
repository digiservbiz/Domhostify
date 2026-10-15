"""Initial persistent records for DomHostify catalog data."""
import os
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class RegistrarOffer(Base):
    __tablename__ = "registrar_offers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(String(253), index=True)
    registrar_key: Mapped[str] = mapped_column(String(80), index=True)
    availability: Mapped[str] = mapped_column(String(20), default="unknown", server_default="unknown")
    registration_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    renewal_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", server_default="EUR")
    source_status: Mapped[str] = mapped_column(String(30), default="unverified", server_default="unverified")
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(String(253), index=True)
    asking_price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", server_default="EUR")
    sale_type: Mapped[str] = mapped_column(String(30), default="make_offer", server_default="make_offer")
    listing_status: Mapped[str] = mapped_column(String(30), default="draft", server_default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./domhostify.db")
_engine_options = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, **_engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_schema() -> None:
    """Create tables for local development; production should use migrations."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Yield a short-lived database session for read-only API dependencies."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
