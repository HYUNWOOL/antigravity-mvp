from typing import Any

import httpx
from fastapi import HTTPException, status


class CreemClient:
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def create_checkout(
        self,
        creem_product_id: str,
        request_id: str,
        success_url: str,
        customer_email: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.api_key:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Creem unavailable")

        payload = {
            "product_id": creem_product_id,
            "request_id": request_id,
            "success_url": success_url,
            "customer": {"email": customer_email},
            "metadata": metadata,
        }

        headers = {"x-api-key": self.api_key}
        url = f"{self.base_url}/v1/checkouts"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to create checkout",
            ) from exc

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to create checkout",
            )

        data = response.json()
        checkout_url = data.get("checkout_url")
        if not checkout_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Missing checkout URL",
            )

        return data
