from decimal import Decimal

D = Decimal


def add_expense(client, headers, amount, day="2026-11-11", category="food"):
    r = client.post("/expenses", json={"category": category, "amount": str(amount),
                                       "expense_date": day}, headers=headers)
    assert r.status_code == 201, r.text


def add_budget(client, headers, amount="150", period="daily", category="food",
               start="2026-11-01", end=None):
    r = client.post("/budgets", json={"category": category, "amount": amount, "period": period,
                                      "start_date": start, "end_date": end}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_spec_example_daily_food_budget_exceeded(client, auth_headers, fixed_today):
    budget_id = add_budget(client, auth_headers)
    for amount in (50, 80, 90):                      # breakfast, lunch, dinner
        add_expense(client, auth_headers, amount)

    body = client.get("/budgets/check", headers=auth_headers).json()
    assert body["reference_date"] == "2026-11-11"
    [item] = body["items"]
    s = item["status"]
    assert item["budget_id"] == budget_id
    assert D(s["total_spent"]) == D("220") and D(s["remaining"]) == D("-70")
    assert D(s["overspent_amount"]) == D("70") and s["status"] == "exceeded"
    [alert] = body["alerts"]
    assert alert["level"] == "exceeded"
    assert alert["message"] == "You exceeded your daily food budget by ฿70.00."


def test_explicit_date_param(client, auth_headers, fixed_today):
    add_budget(client, auth_headers)
    add_expense(client, auth_headers, 100, day="2026-11-05")
    body = client.get("/budgets/check", params={"date": "2026-11-05"}, headers=auth_headers).json()
    assert D(body["items"][0]["status"]["total_spent"]) == D("100")
    assert body["items"][0]["status"]["status"] == "within_budget" or \
        body["items"][0]["status"]["status"] == "near_limit"


def test_warning_alert_near_limit(client, auth_headers, fixed_today):
    add_budget(client, auth_headers)
    add_expense(client, auth_headers, 130)                        # 86.67% of 150
    [alert] = client.get("/budgets/check", headers=auth_headers).json()["alerts"]
    assert alert["level"] == "warning"
    assert "86.67%" in alert["message"] and "฿20.00 remaining" in alert["message"]


def test_inactive_budgets_are_ignored(client, auth_headers, fixed_today):
    add_budget(client, auth_headers, start="2026-10-01", end="2026-10-31")   # ended
    add_budget(client, auth_headers, start="2026-12-01")                     # not started
    body = client.get("/budgets/check", headers=auth_headers).json()
    assert body["items"] == [] and body["alerts"] == []


def test_budget_only_counts_spending_from_its_start_date(client, auth_headers, fixed_today):
    add_budget(client, auth_headers, amount="5000", period="monthly", start="2026-11-10")
    add_expense(client, auth_headers, 999, day="2026-11-05")      # before the budget existed
    add_expense(client, auth_headers, 100, day="2026-11-11")
    s = client.get("/budgets/check", headers=auth_headers).json()["items"][0]["status"]
    assert D(s["total_spent"]) == D("100")


def test_weekly_and_overall_budgets(client, auth_headers, fixed_today):
    add_budget(client, auth_headers, amount="800", period="weekly", category="food")
    add_budget(client, auth_headers, amount="15000", period="monthly", category=None)
    add_expense(client, auth_headers, 300, day="2026-11-09")                   # Monday
    add_expense(client, auth_headers, 400, day="2026-11-08", category="bills")  # last week
    items = {i["status"]["period"]: i["status"]
             for i in client.get("/budgets/check", headers=auth_headers).json()["items"]}
    assert D(items["weekly"]["total_spent"]) == D("300")
    assert D(items["monthly"]["total_spent"]) == D("700")          # all categories


def test_other_users_spending_is_never_counted(client, auth_headers, other_headers, fixed_today):
    add_budget(client, auth_headers)
    add_expense(client, other_headers, 5000)
    s = client.get("/budgets/check", headers=auth_headers).json()["items"][0]["status"]
    assert D(s["total_spent"]) == D("0")


def test_check_requires_login(client):
    assert client.get("/budgets/check").status_code == 401