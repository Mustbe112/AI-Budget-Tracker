from tests.conftest import PASSWORD


def test_register_login_and_me(client):
    r = client.post("/auth/register", json={
        "username": "somchai", "email": "Somchai@Example.com", "password": PASSWORD,
    })
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "somchai@example.com"  # normalized to lower case
    assert "password" not in body and "password_hash" not in body

    r = client.post("/auth/login", data={"username": "somchai", "password": PASSWORD})
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"
    token = r.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["username"] == "somchai"


def test_duplicate_registration_conflicts(client):
    first = {"username": "somchai", "email": "a@example.com", "password": PASSWORD}
    assert client.post("/auth/register", json=first).status_code == 201
    same_email_other_case = {**first, "username": "other", "email": "A@EXAMPLE.COM"}
    assert client.post("/auth/register", json=same_email_other_case).status_code == 409
    same_username_other_case = {**first, "username": "SOMCHAI", "email": "b@example.com"}
    assert client.post("/auth/register", json=same_username_other_case).status_code == 409


def test_wrong_password_rejected(client, auth_headers):
    r = client.post("/auth/login", data={"username": "somchai", "password": "wrong-pass"})
    assert r.status_code == 401


def test_password_over_72_bytes_rejected(client):
    r = client.post("/auth/register", json={
        "username": "thai", "email": "t@example.com", "password": "ก" * 30,  # 90 bytes
    })
    assert r.status_code == 422


def test_protected_routes_require_valid_token(client):
    assert client.get("/expenses").status_code == 401
    assert client.get("/budgets").status_code == 401
    bad = {"Authorization": "Bearer not-a-real-token"}
    assert client.get("/expenses", headers=bad).status_code == 401