from decimal import Decimal

D = Decimal


def add_expense(client, headers, amount, day, category="food"):
    r = client.post("/expenses", json={"category": category, "amount": str(amount),
                                       "expense_date": day}, headers=headers)
    assert r.status_code == 201, r.text


def add_income(client, headers, amount, day):
    assert client.post("/income", json={"amount": str(amount), "source": "Salary",
                                        "income_date": day}, headers=headers).status_code == 201


def test_daily_report(client, auth_headers, fixed_today):
    add_expense(client, auth_headers, 50, "2026-11-11")
    add_expense(client, auth_headers, 80, "2026-11-11")
    add_expense(client, auth_headers, 999, "2026-11-10")           # other day
    body = client.get("/reports/daily", headers=auth_headers).json()
    assert body["period"] == "daily" and body["reference_date"] == "2026-11-11"
    s = body["summary"]
    assert D(s["total_spending"]) == D("130") and s["transaction_count"] == 2
    assert D(s["average_daily_spending"]) == D("130") and s["days"] == 1


def test_weekly_report_uses_monday_to_sunday_and_includes_income(client, auth_headers, fixed_today):
    add_expense(client, auth_headers, 600, "2026-11-09")           # Monday
    add_expense(client, auth_headers, 400, "2026-11-15", "transport")  # Sunday
    add_expense(client, auth_headers, 999, "2026-11-16")           # next Monday: excluded
    add_income(client, auth_headers, 3000, "2026-11-10")
    body = client.get("/reports/weekly", headers=auth_headers).json()
    s = body["summary"]
    assert (s["start"], s["end"], s["days"]) == ("2026-11-09", "2026-11-15", 7)
    assert D(s["total_spending"]) == D("1000")
    assert D(s["average_daily_spending"]) == D("142.86")
    assert [c["category"] for c in s["by_category"]] == ["food", "transport"]
    assert D(body["income_total"]) == D("3000") and D(body["net"]) == D("2000")


def test_monthly_report_with_budget_utilization(client, auth_headers, fixed_today):
    client.post("/budgets", json={"category": None, "amount": "15000", "period": "monthly",
                                  "start_date": "2026-11-01"}, headers=auth_headers)
    add_expense(client, auth_headers, 3000, "2026-11-02", "bills")
    add_expense(client, auth_headers, 1500, "2026-11-20")
    body = client.get("/reports/monthly", params={"date": "2026-11-05"}, headers=auth_headers).json()
    s = body["summary"]
    assert (s["start"], s["end"], s["days"]) == ("2026-11-01", "2026-11-30", 30)
    assert D(s["total_spending"]) == D("4500")
    assert D(s["budget_utilization_percent"]) == D("30.00")


def test_empty_report_is_all_zeros_not_an_error(client, auth_headers, fixed_today):
    body = client.get("/reports/monthly", headers=auth_headers).json()
    assert D(body["summary"]["total_spending"]) == 0 and body["summary"]["by_category"] == []
    assert body["summary"]["budget_utilization_percent"] is None


def test_category_report_default_and_explicit_range(client, auth_headers, fixed_today):
    add_expense(client, auth_headers, 700, "2026-11-03", "food")
    add_expense(client, auth_headers, 300, "2026-11-04", "transport")
    add_expense(client, auth_headers, 999, "2026-10-30", "food")   # previous month
    body = client.get("/reports/categories", headers=auth_headers).json()   # 1 Nov .. today
    assert (body["start_date"], body["end_date"]) == ("2026-11-01", "2026-11-11")
    assert D(body["total_spending"]) == D("1000")
    assert body["categories"][0]["category"] == "food"
    assert D(body["categories"][0]["share_percent"]) == D("70")

    wide = client.get("/reports/categories",
                      params={"start_date": "2026-10-01", "end_date": "2026-11-30"},
                      headers=auth_headers).json()
    assert D(wide["total_spending"]) == D("1999")


def test_category_report_validates_range(client, auth_headers, fixed_today):
    r = client.get("/reports/categories",
                   params={"start_date": "2026-11-10", "end_date": "2026-11-01"}, headers=auth_headers)
    assert r.status_code == 422
    r = client.get("/reports/categories",
                   params={"start_date": "2020-01-01", "end_date": "2026-11-01"}, headers=auth_headers)
    assert r.status_code == 422


def test_weekly_comparison_matches_spec_example(client, auth_headers, fixed_today):
    add_expense(client, auth_headers, 800, "2026-11-03")           # previous week food
    add_expense(client, auth_headers, 1000, "2026-11-10")          # current week food
    add_expense(client, auth_headers, 200, "2026-11-12", "transport")  # new category
    body = client.get("/reports/comparison", headers=auth_headers).json()
    assert body["period"] == "weekly"
    assert body["previous"]["start"] == "2026-11-02" and body["current"]["start"] == "2026-11-09"
    cmp = body["comparison"]
    assert D(cmp["previous_total"]) == D("800") and D(cmp["current_total"]) == D("1200")
    assert D(cmp["change_percent"]) == D("50") and cmp["trend"] == "increase"
    cats = {c["category"]: c for c in cmp["categories"]}
    assert D(cats["food"]["change_percent"]) == D("25") and cats["transport"]["change_percent"] is None


def test_monthly_comparison_with_no_previous_data(client, auth_headers, fixed_today):
    add_expense(client, auth_headers, 500, "2026-11-05")
    cmp = client.get("/reports/comparison", params={"period": "monthly"},
                     headers=auth_headers).json()["comparison"]
    assert cmp["change_percent"] is None and cmp["trend"] == "increase"   # 0 -> 500: undefined %


def test_reports_are_user_scoped_and_need_login(client, auth_headers, other_headers, fixed_today):
    add_expense(client, other_headers, 5000, "2026-11-11")
    body = client.get("/reports/daily", headers=auth_headers).json()
    assert D(body["summary"]["total_spending"]) == 0
    for path in ("daily", "weekly", "monthly", "categories", "comparison"):
        assert client.get(f"/reports/{path}").status_code == 401


def test_invalid_date_rejected(client, auth_headers):
    assert client.get("/reports/daily", params={"date": "tomorrow"},
                      headers=auth_headers).status_code == 422