import uuid

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app import deps_auth
from app.deps import get_creem_client, get_repo
from app.main import app
from app.repo import FakeRepo


class FakeCreemClient:
    async def create_checkout(
        self,
        creem_product_id: str,
        request_id: str,
        success_url: str,
        customer_email: str,
        metadata: dict[str, str],
    ) -> dict[str, str]:
        _ = (creem_product_id, success_url, customer_email, metadata)
        return {
            "id": "chk_test",
            "checkout_url": f"https://checkout.test/{request_id}",
        }


@pytest.fixture
def fake_repo() -> FakeRepo:
    product_id = str(uuid.uuid4())
    return FakeRepo(
        products=[
            {
                "id": product_id,
                "name": "Starter Pack",
                "price_cents": 1500,
                "currency": "USD",
                "creem_product_id": "creem_prod_test",
                "active": True,
            }
        ]
    )


@pytest.fixture
def client(fake_repo: FakeRepo, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app.dependency_overrides[get_repo] = lambda: fake_repo
    app.dependency_overrides[get_creem_client] = lambda: FakeCreemClient()

    async def fake_fetch_user(token: str, settings: object) -> dict[str, str]:
        _ = settings
        if token == "good-token":
            return {"id": "user_test", "email": "user@example.com"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    monkeypatch.setattr(deps_auth, "supabase_fetch_user", fake_fetch_user)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
