"""Public account/session endpoints for the DomHostify marketplace."""
import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from backend.app.auth import create_session, hash_password, normalize_email, require_user, verify_password
from backend.app.database import UserAccount, UserSession, get_db, utc_now

router = APIRouter(prefix="/api/v1/account", tags=["account"])


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=128)
    role: str = Field(default="buyer", min_length=5, max_length=10)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


def _account_payload(user: UserAccount) -> dict:
    return {"public_ref": user.public_ref, "email": user.email, "role": user.role, "active": user.active}


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    try:
        email = normalize_email(payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    role = payload.role.strip().lower()
    if role not in {"buyer", "seller"}:
        raise HTTPException(status_code=422, detail="New accounts may only register as buyer or seller.")
    try:
        user = UserAccount(
            public_ref=hashlib.sha256(hmac.digest(b"domhostify-public-ref", email.encode("utf-8"), "sha256")).hexdigest()[:32],
            email=email,
            password_hash=hash_password(payload.password),
            role=role,
            active=True,
        )
        # Add a random suffix to prevent the public reference from becoming an email-derived identifier.
        user.public_ref = user.public_ref[:20] + hashlib.sha256(user.public_ref.encode()).hexdigest()[:12]
        db.add(user)
        db.flush()
        token, session = create_session(db, user)
        db.commit()
        db.refresh(user)
        return {"account": _account_payload(user), "access_token": token, "token_type": "bearer", "expires_at": session.expires_at.isoformat()}
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with that email already exists.") from exc
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Account database is not initialized. Apply database migrations first.") from exc


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    try:
        email = normalize_email(payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        user = db.scalar(select(UserAccount).where(UserAccount.email == email))
        if user is None or not user.active or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        token, session = create_session(db, user)
        db.commit()
        return {"account": _account_payload(user), "access_token": token, "token_type": "bearer", "expires_at": session.expires_at.isoformat()}
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Account database is not initialized. Apply database migrations first.") from exc


@router.get("/me")
def me(user: UserAccount = Depends(require_user)) -> dict:
    return _account_payload(user)


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer session authentication required.")
    token = authorization[7:].strip()
    session = db.scalar(select(UserSession).where(UserSession.token_hash == hashlib.sha256(token.encode("utf-8")).hexdigest()))
    if session is None or session.revoked_at is not None:
        return {"logged_out": True}
    session.revoked_at = utc_now()
    db.commit()
    return {"logged_out": True}
