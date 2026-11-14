from decimal import Decimal


def bp(**overrides):
    data = {"category": "food", "amount": "150", "period": "daily",
            "start_date": "2026-11-01", "end_date": None}
    data.update(overrides)
    return data


def test_create_list_and_filter_budgets(client, auth_headers):
    r = client.post("/budgets", json=bp(), headers=auth_headers)
    assert r.status_code == 201
    assert Decimal(r.json()["amount"]) == Decimal("150")
    assert r.json()["period"] == "daily"

    client.post("/budgets", json=bp(category="transport", amount="500", period="weekly"),
                headers=auth_headers)

    assert len(client.get("/budgets", headers=auth_headers).json()) == 2
    only_food = client.get("/budgets", params={"category": "food"}, headers=auth_headers)
    assert len(only_food.json()) == 1
    weekly = client.get("/budgets", params={"period": "weekly"}, headers=auth_headers)
    assert len(weekly.json()) == 1


def test_overall_budget_has_null_category(client, auth_headers):
    r = client.post("/budgets", json=bp(category=None, amount="15000", period="monthly"),
                    headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["category"] is None


def test_update_budget(client, auth_headers):
    b = client.post("/budgets", json=bp(), headers=auth_headers).json()
    r = client.put(f"/budgets/{b['id']}", json=bp(amount="200"), headers=auth_headers)
    assert r.status_code == 200
    assert Decimal(r.json()["amount"]) == Decimal("200")


def test_delete_budget(client, auth_headers):
    b = client.post("/budgets", json=bp(), headers=auth_headers).json()
    assert client.delete(f"/budgets/{b['id']}", headers=auth_headers).status_code == 204
    assert client.get("/budgets", headers=auth_headers).json() == []
    assert client.delete(f"/budgets/{b['id']}", headers=auth_headers).status_code == 404


def test_end_date_before_start_date_rejected(client, auth_headers):
    r = client.post("/budgets", json=bp(start_date="2026-11-10", end_date="2026-11-01"),
                    headers=auth_headers)
    assert r.status_code == 422


def test_invalid_period_rejected(client, auth_headers):
    r = client.post("/budgets", json=bp(period="yearly"), headers=auth_headers)
    assert r.status_code == 422


def test_other_users_cannot_touch_budget(client, auth_headers, other_headers):
    b = client.post("/budgets", json=bp(), headers=auth_headers).json()
    url = f"/budgets/{b['id']}"
    assert client.put(url, json=bp(amount="1"), headers=other_headers).status_code == 404
    assert client.delete(url, headers=other_headers).status_code == 404
    assert client.get("/budgets", headers=other_headers).json() == []
    assert len(client.get("/budgets", headers=auth_headers).json()) == 1