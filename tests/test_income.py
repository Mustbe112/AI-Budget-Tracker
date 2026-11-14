from decimal import Decimal

import pytest


def payload(**overrides):
    data = {"amount": "30000.00", "source": "Salary", "income_date": "2026-11-01"}
    data.update(overrides)
    return data


def test_create_list_update_delete_income(client, auth_headers):
    r = client.post("/income", json=payload(), headers=auth_headers)
    assert r.status_code == 201
    income = r.json()
    assert Decimal(income["amount"]) == Decimal("30000")

    client.post("/income", json=payload(amount="2500.50", source="Freelance",
                                        income_date="2026-11-05"), headers=auth_headers)
    body = client.get("/income", headers=auth_headers).json()
    assert body["total"] == 2
    assert Decimal(body["total_amount"]) == Decimal("32500.50")
    assert body["items"][0]["source"] == "Freelance"        # newest first

    filtered = client.get("/income", params={"start_date": "2026-11-03"}, headers=auth_headers).json()
    assert filtered["total"] == 1

    r = client.put(f"/income/{income['id']}", json=payload(amount="31000"), headers=auth_headers)
    assert r.status_code == 200 and Decimal(r.json()["amount"]) == Decimal("31000")

    assert client.delete(f"/income/{income['id']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/income/{income['id']}", headers=auth_headers).status_code == 404


def test_other_users_cannot_touch_income(client, auth_headers, other_headers):
    income = client.post("/income", json=payload(), headers=auth_headers).json()
    url = f"/income/{income['id']}"
    assert client.put(url, json=payload(amount="1"), headers=other_headers).status_code == 404
    assert client.delete(url, headers=other_headers).status_code == 404
    assert client.get("/income", headers=other_headers).json()["total"] == 0


@pytest.mark.parametrize("bad", [{"amount": "0"}, {"amount": "-10"}, {"amount": "1.234"},
                                 {"source": ""}, {"income_date": "not-a-date"}])
def test_invalid_income_rejected(client, auth_headers, bad):
    assert client.post("/income", json=payload(**bad), headers=auth_headers).status_code == 422


def test_income_requires_login(client):
    assert client.get("/income").status_code == 401
    assert client.post("/income", json=payload()).status_code == 401