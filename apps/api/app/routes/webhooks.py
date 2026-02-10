import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import Settings, get_settings
from app.deps import get_repo
from app.repo import Repo
from app.utils.crypto import hmac_sha256_hex, secure_compare, sha256_hex

router = APIRouter()


def _to_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@router.post("/webhooks/creem")
async def creem_webhook(
    request: Request,
    repo: Repo = Depends(get_repo),
    settings: Settings = Depends(get_settings),
) -> dict[str, bool]:
    raw = await request.body()
    provided_signature = request.headers.get("creem-signature")
    if not provided_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature")

    expected_signature = hmac_sha256_hex(settings.creem_webhook_secret, raw)
    if not secure_compare(expected_signature, provided_signature):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        ) from exc

    event_key = payload.get("id") or payload.get("eventId") or sha256_hex(raw)
    event_key = str(event_key)

    if repo.webhook_event_seen(event_key):
        return {"ok": True}

    repo.webhook_event_mark_seen(event_key)

    if payload.get("eventType") == "checkout.completed":
        obj = payload.get("object") or {}
        request_id = obj.get("request_id")
        order_obj = obj.get("order") or {}

        paid_status = order_obj.get("status")
        creem_order_id = order_obj.get("id")
        creem_checkout_id = obj.get("id") or obj.get("checkout_id")
        amount_cents = _to_optional_int(order_obj.get("amount") or order_obj.get("amount_cents"))
        currency = order_obj.get("currency")

        if request_id and paid_status == "paid":
            local_order = repo.get_order_by_request_id(str(request_id))
            if local_order:
                repo.mark_order_paid(
                    request_id=str(request_id),
                    creem_checkout_id=str(creem_checkout_id) if creem_checkout_id else None,
                    creem_order_id=str(creem_order_id) if creem_order_id else None,
                    amount_cents=amount_cents,
                    currency=str(currency) if currency else None,
                )
                repo.grant_entitlement(
                    user_id=str(local_order["user_id"]),
                    product_id=str(local_order["product_id"]),
                )

    return {"ok": True}
