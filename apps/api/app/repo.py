from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

import httpx

from app.config import Settings


class Repo(Protocol):
    def get_product(self, product_id: str) -> dict[str, Any] | None:
        ...

    def create_order_pending(
        self,
        user_id: str,
        product_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        ...

    def update_order_failed(self, request_id: str) -> None:
        ...

    def update_order_checkout_ids(self, request_id: str, creem_checkout_id: str | None) -> None:
        ...

    def get_order_by_request_id(self, request_id: str) -> dict[str, Any] | None:
        ...

    def mark_order_paid(
        self,
        request_id: str,
        creem_checkout_id: str | None,
        creem_order_id: str | None,
        amount_cents: int | None,
        currency: str | None,
    ) -> None:
        ...

    def grant_entitlement(self, user_id: str, product_id: str) -> None:
        ...

    def webhook_event_seen(self, event_key: str) -> bool:
        ...

    def webhook_event_mark_seen(self, event_key: str) -> None:
        ...


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SupabaseRepo:
    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError("Supabase settings are missing")

        self.base_url = settings.supabase_url.rstrip("/")
        self.service_role_key = settings.supabase_service_role_key

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _request(
        self,
        method: str,
        table: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        prefer: str | None = None,
    ) -> httpx.Response:
        url = f"{self.base_url}/rest/v1/{table}"
        with httpx.Client(timeout=10.0) as client:
            return client.request(
                method=method,
                url=url,
                headers=self._headers(prefer=prefer),
                params=params,
                json=payload,
            )

    @staticmethod
    def _ensure_success(response: httpx.Response, action: str) -> None:
        if response.status_code >= 400:
            detail = response.text[:300]
            raise RuntimeError(
                f"Supabase request failed for {action} "
                f"(status={response.status_code}, detail={detail})"
            )

    def _select_one(self, table: str, params: dict[str, str]) -> dict[str, Any] | None:
        response = self._request("GET", table, params=params)
        self._ensure_success(response, f"select {table}")

        rows = response.json()
        if not isinstance(rows, list) or not rows:
            return None
        return rows[0]

    def get_product(self, product_id: str) -> dict[str, Any] | None:
        return self._select_one(
            "products",
            params={
                "select": "*",
                "id": f"eq.{product_id}",
                "active": "eq.true",
                "limit": "1",
            },
        )

    def create_order_pending(
        self,
        user_id: str,
        product_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        payload = {
            "user_id": user_id,
            "product_id": product_id,
            "status": "pending",
            "request_id": request_id,
        }
        response = self._request(
            "POST",
            "orders",
            payload=payload,
            prefer="return=representation",
        )
        self._ensure_success(response, "insert orders")

        rows = response.json()
        if isinstance(rows, list) and rows:
            return rows[0]
        if isinstance(rows, dict):
            return rows
        return payload

    def update_order_failed(self, request_id: str) -> None:
        response = self._request(
            "PATCH",
            "orders",
            params={"request_id": f"eq.{request_id}"},
            payload={"status": "failed", "updated_at": _now_iso()},
        )
        self._ensure_success(response, "update orders failed")

    def update_order_checkout_ids(self, request_id: str, creem_checkout_id: str | None) -> None:
        response = self._request(
            "PATCH",
            "orders",
            params={"request_id": f"eq.{request_id}"},
            payload={
                "creem_checkout_id": creem_checkout_id,
                "updated_at": _now_iso(),
            },
        )
        self._ensure_success(response, "update orders checkout id")

    def get_order_by_request_id(self, request_id: str) -> dict[str, Any] | None:
        return self._select_one(
            "orders",
            params={
                "select": "*",
                "request_id": f"eq.{request_id}",
                "limit": "1",
            },
        )

    def mark_order_paid(
        self,
        request_id: str,
        creem_checkout_id: str | None,
        creem_order_id: str | None,
        amount_cents: int | None,
        currency: str | None,
    ) -> None:
        payload = {
            "status": "paid",
            "creem_checkout_id": creem_checkout_id,
            "creem_order_id": creem_order_id,
            "amount_cents": amount_cents,
            "currency": currency,
            "updated_at": _now_iso(),
        }
        response = self._request(
            "PATCH",
            "orders",
            params={"request_id": f"eq.{request_id}"},
            payload=payload,
        )
        self._ensure_success(response, "mark order paid")

    def grant_entitlement(self, user_id: str, product_id: str) -> None:
        response = self._request(
            "POST",
            "entitlements",
            params={"on_conflict": "user_id,product_id"},
            payload={"user_id": user_id, "product_id": product_id},
            prefer="resolution=ignore-duplicates,return=minimal",
        )
        if response.status_code == 409:
            return
        self._ensure_success(response, "upsert entitlements")

    def webhook_event_seen(self, event_key: str) -> bool:
        row = self._select_one(
            "webhook_events",
            params={
                "select": "id",
                "event_key": f"eq.{event_key}",
                "limit": "1",
            },
        )
        return row is not None

    def webhook_event_mark_seen(self, event_key: str) -> None:
        response = self._request(
            "POST",
            "webhook_events",
            params={"on_conflict": "event_key"},
            payload={"event_key": event_key},
            prefer="resolution=ignore-duplicates,return=minimal",
        )
        if response.status_code == 409:
            return
        self._ensure_success(response, "insert webhook event")


class FakeRepo:
    def __init__(self, products: list[dict[str, Any]] | None = None) -> None:
        self.products: dict[str, dict[str, Any]] = {
            p["id"]: {**p} for p in (products or [])
        }
        self.orders_by_request: dict[str, dict[str, Any]] = {}
        self.orders_by_id: dict[str, dict[str, Any]] = {}
        self.entitlements: set[tuple[str, str]] = set()
        self.webhook_events: set[str] = set()

    def get_product(self, product_id: str) -> dict[str, Any] | None:
        product = self.products.get(product_id)
        if not product or not product.get("active", True):
            return None
        return {**product}

    def create_order_pending(
        self,
        user_id: str,
        product_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        order = {
            "id": uuid4().hex,
            "user_id": user_id,
            "product_id": product_id,
            "status": "pending",
            "request_id": request_id,
            "creem_checkout_id": None,
            "creem_order_id": None,
            "amount_cents": None,
            "currency": None,
        }
        self.orders_by_request[request_id] = order
        self.orders_by_id[order["id"]] = order
        return {**order}

    def update_order_failed(self, request_id: str) -> None:
        order = self.orders_by_request.get(request_id)
        if order:
            order["status"] = "failed"

    def update_order_checkout_ids(self, request_id: str, creem_checkout_id: str | None) -> None:
        order = self.orders_by_request.get(request_id)
        if order:
            order["creem_checkout_id"] = creem_checkout_id

    def get_order_by_request_id(self, request_id: str) -> dict[str, Any] | None:
        order = self.orders_by_request.get(request_id)
        return {**order} if order else None

    def mark_order_paid(
        self,
        request_id: str,
        creem_checkout_id: str | None,
        creem_order_id: str | None,
        amount_cents: int | None,
        currency: str | None,
    ) -> None:
        order = self.orders_by_request.get(request_id)
        if not order:
            return

        order["status"] = "paid"
        order["creem_checkout_id"] = creem_checkout_id
        order["creem_order_id"] = creem_order_id
        order["amount_cents"] = amount_cents
        order["currency"] = currency

    def grant_entitlement(self, user_id: str, product_id: str) -> None:
        self.entitlements.add((user_id, product_id))

    def webhook_event_seen(self, event_key: str) -> bool:
        return event_key in self.webhook_events

    def webhook_event_mark_seen(self, event_key: str) -> None:
        self.webhook_events.add(event_key)
