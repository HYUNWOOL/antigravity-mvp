def test_checkout_requires_auth(client, fake_repo):
    product_id = next(iter(fake_repo.products.keys()))
    response = client.post("/api/checkout", json={"product_id": product_id})
    assert response.status_code == 401


def test_checkout_product_not_found(client):
    response = client.post(
        "/api/checkout",
        headers={"Authorization": "Bearer good-token"},
        json={"product_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


def test_checkout_success_creates_pending_order(client, fake_repo):
    product_id = next(iter(fake_repo.products.keys()))
    response = client.post(
        "/api/checkout",
        headers={"Authorization": "Bearer good-token"},
        json={"product_id": product_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert "checkout_url" in body
    assert body["checkout_url"].startswith("https://checkout.test/")

    assert len(fake_repo.orders_by_request) == 1
    order = next(iter(fake_repo.orders_by_request.values()))
    assert order["status"] == "pending"
    assert order["creem_checkout_id"] == "chk_test"
    assert order["user_id"] == "user_test"
