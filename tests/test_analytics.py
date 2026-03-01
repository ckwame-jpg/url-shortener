from app.models import Click
from datetime import datetime, timezone


def test_stats_empty(client, auth_headers):
    resp = client.post("/shorten", json={"original_url": "https://example.com"}, headers=auth_headers)
    short_code = resp.json()["short_code"]

    resp = client.get(f"/urls/{short_code}/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_clicks"] == 0
    assert data["recent_clicks"] == []


def test_stats_with_clicks(client, auth_headers, db_session):
    resp = client.post("/shorten", json={"original_url": "https://example.com"}, headers=auth_headers)
    data = resp.json()
    short_code = data["short_code"]
    url_id = data["id"]

    # Simulate processed clicks directly in DB
    for i in range(3):
        click = Click(
            url_id=url_id,
            ip_address=f"1.2.3.{i}",
            user_agent="Mozilla/5.0",
            referrer="https://twitter.com" if i < 2 else "https://google.com",
            device_type="desktop",
            country=None,
        )
        db_session.add(click)
    db_session.commit()

    # Update click count on URL
    from app.models import URL
    url = db_session.query(URL).filter(URL.id == url_id).first()
    url.click_count = 3
    db_session.commit()

    resp = client.get(f"/urls/{short_code}/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_clicks"] == 3
    assert len(data["recent_clicks"]) == 3
    assert data["devices"]["desktop"] == 3
    assert len(data["top_referrers"]) == 2


def test_stats_not_found(client, auth_headers):
    resp = client.get("/urls/nonexistent/stats", headers=auth_headers)
    assert resp.status_code == 404


def test_stats_requires_auth(client):
    resp = client.get("/urls/abc/stats")
    assert resp.status_code == 401
