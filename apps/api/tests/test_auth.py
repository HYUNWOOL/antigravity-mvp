def test_me_requires_auth(client):
    response = client.get("/api/me")
    assert response.status_code == 401


def test_me_with_good_token(client):
    response = client.get("/api/me", headers={"Authorization": "Bearer good-token"})
    assert response.status_code == 200
    assert response.json()["id"] == "user_test"
