from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.creem_client import CreemClient
from app.deps import get_creem_client, get_repo
from app.deps_auth import get_current_user
from app.repo import Repo

router = APIRouter()


class CheckoutRequest(BaseModel):
    product_id: str


class CheckoutResponse(BaseModel):
    checkout_url: str


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    repo: Repo = Depends(get_repo),
    creem: CreemClient = Depends(get_creem_client),
    user: dict[str, Any] = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    product = repo.get_product(body.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    request_id = uuid4().hex
    repo.create_order_pending(
        user_id=str(user["id"]),
        product_id=body.product_id,
        request_id=request_id,
    )

    try:
        checkout = await creem.create_checkout(
            creem_product_id=str(product["creem_product_id"]),
            request_id=request_id,
            success_url=f"{settings.frontend_base_url.rstrip('/')}/success",
            customer_email=str(user.get("email", "")),
            metadata={
                "user_id": str(user["id"]),
                "product_id": body.product_id,
                "request_id": request_id,
            },
        )
        repo.update_order_checkout_ids(request_id=request_id, creem_checkout_id=checkout.get("id"))
    except Exception as exc:
        repo.update_order_failed(request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create checkout",
        ) from exc

    checkout_url = checkout.get("checkout_url")
    if not checkout_url:
        repo.update_order_failed(request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create checkout",
        )

    return {"checkout_url": str(checkout_url)}
