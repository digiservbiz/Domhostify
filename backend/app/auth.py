"""Password and opaque-session authentication for DomHostify accounts."""
import hashlib
import hmac
import os
import secrets
from datetime import timedelta

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.app.database import UserAccount, UserSession, get_db, utc_now

PASSWORD_ITERATIONS = 310_000
SESSION_TTL_HOURS = 24
ALLOWED_ROLES = {"buyer", "seller", "admin"}


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if len(email) > 320 or "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError("Enter a valid email address.")
    local, domain = email.rsplit("@", 1)
    if not local or not domain or "." not in domain or any(ch.isspace() for ch in email):
        raise ValueError("Enter a valid email address.")
    return email


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        raise ValueError("Password must contain between 12 and 128 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(expected.hex(), digest_hex)
    except (AttributeError, ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, user: UserAccount) -> tuple[str, UserSession]:
    raw_token = secrets.token_urlsafe(48)
    session = UserSession(user_id=user.id, token_hash=_token_hash(raw_token), expires_at=utc_now() + timedelta(hours=SESSION_TTL_HOURS))
    db.add(session)
    return raw_token, session


def authenticate_request(authorization: str | None, db: Session, *, required_role: str | None = None) -> UserAccount:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer session authentication required.")
    token = authorization[7:].strip()
    if not token or len(token) > 256:
        raise HTTPException(status_code=401, detail="Invalid session credentials.")
    try:
        session = db.scalar(select(UserSession).where(UserSession.token_hash == _token_hash(token)))
        if session is None or session.revoked_at is not None:
            raise HTTPException(status_code=401, detail="Invalid or revoked session.")
        if session.expires_at <= utc_now():
            session.revoked_at = utc_now()
            db.commit()
            raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
        user = db.get(UserAccount, session.user_id)
        if user is None or not user.active:
            raise HTTPException(status_code=401, detail="Account is unavailable.")
        if required_role is not None and user.role != required_role and user.role != "admin":
            raise HTTPException(status_code=403, detail="Insufficient account permissions.")
        return user
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Account database is not initialized. Apply database migrations first.") from exc


def _bootstrap_or_session_ref(authorization: str | None, db: Session, role: str) -> str:
    configured = os.getenv(f"DOMHOSTIFY_{role.upper()}_API_TOKEN", "").strip()
    if configured and authorization and authorization.startswith("Bearer "):
        supplied = authorization[7:].strip()
        if supplied and hmac.compare_digest(supplied, configured):
            return hashlib.sha256(supplied.encode("utf-8")).hexdigest()[:32]
    user = authenticate_request(authorization, db, required_role=role)
    return user.public_ref


def require_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> UserAccount:
    return authenticate_request(authorization, db)


def require_seller(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> UserAccount:
    return authenticate_request(authorization, db, required_role="seller")


def require_buyer(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> UserAccount:
    return authenticate_request(authorization, db, required_role="buyer")


def require_admin(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> UserAccount:
    return authenticate_request(authorization, db, required_role="admin")


def require_seller_ref(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> str:
    return _bootstrap_or_session_ref(authorization, db, "seller")


def require_buyer_ref(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> str:
    return _bootstrap_or_session_ref(authorization, db, "buyer")


def require_admin_ref(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> str:
    return _bootstrap_or_session_ref(authorization, db, "admin")
