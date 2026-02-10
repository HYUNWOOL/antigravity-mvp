import json

from app.config import get_settings
from app.utils.crypto import hmac_sha256_hex


def _signed_headers(raw: bytes) -> dict[str, str]:
    signature = hmac_sha256_hex(get_settings().creem_webhook_secret, raw)
    return {"creem-signature": signature, "content-type": "application/json"}


def test_webhook_missing_signature(client):
    response = client.post("/api/webhooks/creem", json={"eventType": "checkout.completed"})
    assert response.status_code == 400


def test_webhook_invalid_signature(client):
    payload = {"eventType": "checkout.completed"}
    response = client.post(
        "/api/webhooks/creem",
        data=json.dumps(payload),
        headers={"creem-signature": "invalid", "content-type": "application/json"},
    )
    assert response.status_code == 400


def test_webhook_paid_event_marks_order_and_grants_entitlement(client, fake_repo):
    product_id = next(iter(fake_repo.products.keys()))
    request_id = "req_test_123"
    fake_repo.create_order_pending(
        user_id="user_test",
        product_id=product_id,
        request_id=request_id,
    )

    payload = {
        "id": "evt_1",
        "eventType": "checkout.completed",
        "object": {
            "id": "chk_1",
            "request_id": request_id,
            "order": {
                "id": "ord_1",
                "status": "paid",
                "amount": 1500,
                "currency": "USD",
            },
        },
    }
    raw = json.dumps(payload).encode("utf-8")

    response = client.post("/api/webhooks/creem", data=raw, headers=_signed_headers(raw))
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    order = fake_repo.get_order_by_request_id(request_id)
    assert order is not None
    assert order["status"] == "paid"
    assert order["creem_checkout_id"] == "chk_1"
    assert order["creem_order_id"] == "ord_1"
    assert ("user_test", product_id) in fake_repo.entitlements

    second = client.post("/api/webhooks/creem", data=raw, headers=_signed_headers(raw))
    assert second.status_code == 200
    assert second.json() == {"ok": True}
    assert len(fake_repo.entitlements) == 1
