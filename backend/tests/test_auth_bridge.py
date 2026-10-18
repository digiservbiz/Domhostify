import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.auth import create_session, require_admin_ref, require_buyer_ref, require_seller_ref
from backend.app.database import Base, UserAccount


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return engine, Session


def test_session_role_refs_are_stable_and_role_scoped() -> None:
    engine, Session = _session()
    try:
        with Session() as db:
            seller = UserAccount(email="seller-bridge@example.com", password_hash="unused", role="seller", active=True)
            buyer = UserAccount(email="buyer-bridge@example.com", password_hash="unused", role="buyer", active=True)
            admin = UserAccount(email="admin-bridge@example.com", password_hash="unused", role="admin", active=True)
            db.add_all([seller, buyer, admin])
            db.flush()
            seller_token, _ = create_session(db, seller)
            buyer_token, _ = create_session(db, buyer)
            admin_token, _ = create_session(db, admin)
            db.commit()

            assert require_seller_ref(f"Bearer {seller_token}", db) == seller.public_ref
            assert require_buyer_ref(f"Bearer {buyer_token}", db) == buyer.public_ref
            assert require_admin_ref(f"Bearer {admin_token}", db) == admin.public_ref

            try:
                require_seller_ref(f"Bearer {buyer_token}", db)
            except Exception as exc:
                assert getattr(exc, "status_code", None) == 403
            else:
                raise AssertionError("buyer session unexpectedly passed seller authorization")
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_bootstrap_role_ref_compatibility_remains_available(monkeypatch) -> None:
    engine, Session = _session()
    try:
        monkeypatch.setenv("DOMHOSTIFY_SELLER_API_TOKEN", "legacy-seller-token")
        with Session() as db:
            expected = hashlib.sha256(b"legacy-seller-token").hexdigest()[:32]
            assert require_seller_ref("Bearer legacy-seller-token", db) == expected
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
