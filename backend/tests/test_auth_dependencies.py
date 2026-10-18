from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.app.auth import require_admin_ref, require_seller_ref


app = FastAPI()


@app.get("/test/seller")
def seller_endpoint(seller_ref: str = Depends(require_seller_ref)) -> dict:
    return {"seller_ref": seller_ref}


@app.get("/test/admin")
def admin_endpoint(admin_ref: str = Depends(require_admin_ref)) -> dict:
    return {"admin_ref": admin_ref}


def test_session_dependency_can_be_used_directly_in_fastapi() -> None:
    client = TestClient(app)
    response = client.get("/test/seller")
    assert response.status_code in {401, 503}


def test_admin_dependency_rejects_missing_credentials() -> None:
    client = TestClient(app)
    response = client.get("/test/admin")
    assert response.status_code in {401, 503}
