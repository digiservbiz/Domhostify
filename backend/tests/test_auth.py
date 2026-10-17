from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app


def test_account_registration_login_me_logout_flow() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        registration = client.post(
            "/api/v1/account/register",
            json={"email": "seller@example.com", "password": "Correct-Horse-Battery-77", "role": "seller"},
        )
        assert registration.status_code == 201
        body = registration.json()
        token = body["access_token"]
        assert body["account"]["role"] == "seller"
        assert token

        duplicate = client.post(
            "/api/v1/account/register",
            json={"email": "seller@example.com", "password": "Correct-Horse-Battery-77", "role": "seller"},
        )
        assert duplicate.status_code == 409

        me = client.get("/api/v1/account/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "seller@example.com"

        logout = client.post("/api/v1/account/logout", headers={"Authorization": f"Bearer {token}"})
        assert logout.status_code == 200

        revoked = client.get("/api/v1/account/me", headers={"Authorization": f"Bearer {token}"})
        assert revoked.status_code == 401

        login = client.post(
            "/api/v1/account/login",
            json={"email": "seller@example.com", "password": "Correct-Horse-Battery-77"},
        )
        assert login.status_code == 200
        assert login.json()["access_token"] != token

        bad_login = client.post(
            "/api/v1/account/login",
            json={"email": "seller@example.com", "password": "wrong-password"},
        )
        assert bad_login.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_account_registration_rejects_admin_role_and_short_password() -> None:
    response = TestClient(app).post(
        "/api/v1/account/register",
        json={"email": "admin@example.com", "password": "short", "role": "admin"},
    )
    assert response.status_code == 422
