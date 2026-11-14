from decimal import Decimal

import pytest


def payload(**overrides):
    data = {
        "category": "food", "amount": "220.50", "description": "Dinner",
        "merchant": "Som Tam Stall", "expense_date": "2026-11-10",
    }
    data.update(overrides)
    return data


def create(client, headers, **overrides):
    r = client.post("/expenses", json=payload(**overrides), headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_and_get_expense(client, auth_headers):
    created = create(client, auth_headers)
    assert Decimal(created["amount"]) == Decimal("220.50")
    assert created["category"] == "food"

    r = client.get(f"/expenses/{created['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["merchant"] == "Som Tam Stall"


def test_list_filters_and_pagination(client, auth_headers):
    create(client, auth_headers, amount="50", expense_date="2026-11-09")
    create(client, auth_headers, amount="80", expense_date="2026-11-10")
    create(client, auth_headers, amount="90", expense_date="2026-11-10")
    create(client, auth_headers, category="transport", amount="40",
           expense_date="2026-11-11")

    body = client.get("/expenses", headers=auth_headers).json()
    assert body["total"] == 4
    assert Decimal(body["total_amount"]) == Decimal("260")
    assert body["items"][0]["expense_date"] == "2026-11-11"  # newest first

    body = client.get("/expenses", params={"category": "food"}, headers=auth_headers).json()
    assert body["total"] == 3

    body = client.get(
        "/expenses",
        params={"start_date": "2026-11-10", "end_date": "2026-11-10"},
        headers=auth_headers,
    ).json()
    assert body["total"] == 2
    assert Decimal(body["total_amount"]) == Decimal("170")

    body = client.get("/expenses", params={"limit": 2, "offset": 2},
                      headers=auth_headers).json()
    assert len(body["items"]) == 2 and body["total"] == 4


def test_update_expense(client, auth_headers):
    exp = create(client, auth_headers)
    r = client.put(f"/expenses/{exp['id']}",
                   json=payload(category="bills", amount="300.00"), headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["category"] == "bills"
    assert Decimal(r.json()["amount"]) == Decimal("300")


def test_delete_expense(client, auth_headers):
    exp = create(client, auth_headers)
    url = f"/expenses/{exp['id']}"
    assert client.delete(url, headers=auth_headers).status_code == 204
    assert client.get(url, headers=auth_headers).status_code == 404


def test_other_users_cannot_touch_expense(client, auth_headers, other_headers):
    exp = create(client, auth_headers)
    url = f"/expenses/{exp['id']}"
    assert client.get(url, headers=other_headers).status_code == 404
    assert client.put(url, json=payload(amount="1"), headers=other_headers).status_code == 404
    assert client.delete(url, headers=other_headers).status_code == 404
    assert client.get("/expenses", headers=other_headers).json()["total"] == 0
    assert client.get(url, headers=auth_headers).status_code == 200  # still intact


@pytest.mark.parametrize("bad", [
    {"amount": "-5"},
    {"amount": "0"},
    {"amount": "10.555"},        # more than 2 decimal places
    {"amount": "abc"},
    {"category": "gambling"},
    {"expense_date": None},
])
def test_invalid_input_rejected(client, auth_headers, bad):
    r = client.post("/expenses", json=payload(**bad), headers=auth_headers)
    assert r.status_code == 422


def test_reversed_date_range_rejected(client, auth_headers):
    r = client.get("/expenses",
                   params={"start_date": "2026-11-10", "end_date": "2026-11-01"},
                   headers=auth_headers)
    assert r.status_code == 422