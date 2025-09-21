def test_register_and_login(client):
    # register
    r = client.post("/api/v1/auth/register", json={"username": "u1", "password": "p1"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token

    # login
    r2 = client.post("/api/v1/auth/login", data={"username": "u1", "password": "p1"})
    assert r2.status_code == 200
    token2 = r2.json()["access_token"]
    assert token2

    # me
    r3 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token2}"})
    assert r3.status_code == 200
    assert r3.json()["username"] == "u1"
