def test_register(client):
    resp = client.post("/register", json={"email": "new@test.com", "password": "pass123"})
    assert resp.status_code == 201
    assert "access_token" in resp.json()


def test_register_duplicate(client):
    client.post("/register", json={"email": "dup@test.com", "password": "pass123"})
    resp = client.post("/register", json={"email": "dup@test.com", "password": "pass123"})
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/register", json={"email": "login@test.com", "password": "pass123"})
    resp = client.post("/login", data={"username": "login@test.com", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/register", json={"email": "wrong@test.com", "password": "pass123"})
    resp = client.post("/login", data={"username": "wrong@test.com", "password": "bad"})
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post("/login", data={"username": "ghost@test.com", "password": "pass123"})
    assert resp.status_code == 401
