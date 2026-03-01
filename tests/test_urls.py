from unittest.mock import patch


def test_shorten_url(client, auth_headers):
    resp = client.post("/shorten", json={"original_url": "https://example.com"}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "short_code" in data
    assert data["original_url"] == "https://example.com"
    assert data["click_count"] == 0


def test_shorten_requires_auth(client):
    resp = client.post("/shorten", json={"original_url": "https://example.com"})
    assert resp.status_code == 401


def test_list_urls(client, auth_headers):
    client.post("/shorten", json={"original_url": "https://one.com"}, headers=auth_headers)
    client.post("/shorten", json={"original_url": "https://two.com"}, headers=auth_headers)
    resp = client.get("/urls", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_delete_url(client, auth_headers):
    resp = client.post("/shorten", json={"original_url": "https://delete.com"}, headers=auth_headers)
    short_code = resp.json()["short_code"]
    resp = client.delete(f"/urls/{short_code}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get("/urls", headers=auth_headers)
    assert len(resp.json()) == 0


def test_delete_not_found(client, auth_headers):
    resp = client.delete("/urls/nonexistent", headers=auth_headers)
    assert resp.status_code == 404


@patch("app.routes.urls.redis_client")
def test_redirect(mock_redis, client, auth_headers):
    mock_redis.get.return_value = None

    resp = client.post("/shorten", json={"original_url": "https://example.com"}, headers=auth_headers)
    short_code = resp.json()["short_code"]

    with patch("app.tasks.process_click.delay"):
        resp = client.get(f"/{short_code}", follow_redirects=False)
        assert resp.status_code == 307
        assert resp.headers["location"] == "https://example.com"


def test_redirect_not_found(client):
    resp = client.get("/nonexistent", follow_redirects=False)
    assert resp.status_code == 404
