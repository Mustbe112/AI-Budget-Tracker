from decimal import Decimal

D = Decimal


def add_expense(client, headers, amount, day, category="food"):
    r = client.post("/expenses", json={"category": category, "amount": str(amount),
                                       "expense_date": day}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def add_budget(client, headers, amount, period="daily", category="food"):
    assert client.post("/budgets", json={"category": category, "amount": amount, "period": period,
                                         "start_date": "2026-11-01"}, headers=headers).status_code == 201


def test_overspending_lists_only_exceeded_budgets(client, auth_headers, fixed_today):
    add_budget(client, auth_headers, "150", "daily", "food")        # will be exceeded
    add_budget(client, auth_headers, "1000", "daily", "transport")  # fine
    add_expense(client, auth_headers, 220, "2026-11-11")
    add_expense(client, auth_headers, 100, "2026-11-11", "transport")
    body = client.get("/analysis/overspending", headers=auth_headers).json()
    assert body["exceeded_count"] == 1
    assert body["items"][0]["status"]["category"] == "food"
    assert D(body["items"][0]["status"]["overspent_amount"]) == D("70")
    assert len(body["alerts"]) == 1


def test_no_overspending_returns_empty_lists(client, auth_headers, fixed_today):
    body = client.get("/analysis/overspending", headers=auth_headers).json()
    assert body["exceeded_count"] == 0 and body["items"] == [] and body["alerts"] == []


def test_anomalies_flags_unusual_expense_without_changing_data(client, auth_headers, fixed_today):
    ids = [add_expense(client, auth_headers, a, f"2026-11-0{d}")
           for d, a in enumerate((100, 110, 120, 130, 140, 150, 160, 170), start=1)]
    big = add_expense(client, auth_headers, 1000, "2026-11-09")
    add_expense(client, auth_headers, 5000, "2026-11-10", "bills")  # only 1 bills expense
    body = client.get("/analysis/anomalies", headers=auth_headers).json()
    cats = {c["category"]: c for c in body["categories"]}
    assert cats["food"]["status"] == "analyzed" and D(cats["food"]["upper_bound"]) == D("220")
    assert [a["expense_id"] for a in cats["food"]["anomalies"]] == [big]
    assert cats["bills"]["status"] == "insufficient_data" and cats["bills"]["anomalies"] == []
    assert body["total_anomalies"] == 1
    # flagged expense still exists, untouched
    assert client.get(f"/expenses/{big}", headers=auth_headers).status_code == 200
    assert client.get("/expenses", headers=auth_headers).json()["total"] == len(ids) + 2


def test_anomalies_category_filter_and_validation(client, auth_headers, fixed_today):
    add_expense(client, auth_headers, 100, "2026-11-01", "bills")
    body = client.get("/analysis/anomalies", params={"category": "food"}, headers=auth_headers).json()
    assert body["categories"] == []
    assert client.get("/analysis/anomalies", params={"lookback_days": 1},
                      headers=auth_headers).status_code == 422


def test_forecast_matches_spec_example_and_excludes_today(client, auth_headers, fixed_today):
    for day, amount in zip(("06", "07", "08", "09", "10"), (100, 120, 150, 130, 200)):
        add_expense(client, auth_headers, amount, f"2026-11-{day}")
    add_expense(client, auth_headers, 9999, "2026-11-11")           # today: still in progress
    body = client.get("/analysis/forecast", params={"history_days": 5, "window": 5},
                      headers=auth_headers).json()
    assert (body["history_start"], body["history_end"]) == ("2026-11-06", "2026-11-10")
    assert (body["forecast_start"], body["forecast_end"]) == ("2026-11-11", "2026-11-17")
    f = body["forecast"]
    assert f["status"] == "ok" and D(f["moving_average"]) == D("140")
    assert D(f["forecast_total"]) == D("980") and "not a guarantee" in f["disclaimer"]


def test_forecast_with_no_data_is_zero_not_error(client, auth_headers, fixed_today):
    f = client.get("/analysis/forecast", headers=auth_headers).json()["forecast"]
    assert f["status"] == "ok" and D(f["moving_average"]) == 0


def test_forecast_insufficient_history_and_validation(client, auth_headers, fixed_today):
    f = client.get("/analysis/forecast", params={"history_days": 3, "window": 5},
                   headers=auth_headers).json()["forecast"]
    assert f["status"] == "insufficient_data" and f["moving_average"] is None
    for bad in ({"window": 0}, {"horizon_days": 0}, {"history_days": 0}):
        assert client.get("/analysis/forecast", params=bad, headers=auth_headers).status_code == 422


def test_summary_combines_report_budgets_and_alerts(client, auth_headers, fixed_today):
    add_budget(client, auth_headers, "150", "daily", "food")
    add_expense(client, auth_headers, 220, "2026-11-11")
    add_expense(client, auth_headers, 100, "2026-11-11", "transport")
    add_expense(client, auth_headers, 500, "2026-10-15")            # previous month
    body = client.get("/analysis/summary", headers=auth_headers).json()
    assert body["period"] == "monthly" and body["top_category"] == "food"
    cmp = body["report"]["comparison"]
    assert D(cmp["current_total"]) == D("320") and D(cmp["previous_total"]) == D("500")
    assert D(cmp["change_percent"]) == D("-36") and cmp["trend"] == "decrease"
    assert body["alerts"][0]["level"] == "exceeded"
    assert len(body["budget_checks"]) == 1


def test_summary_with_no_data(client, auth_headers, fixed_today):
    body = client.get("/analysis/summary", headers=auth_headers).json()
    assert body["top_category"] is None and body["alerts"] == [] and body["budget_checks"] == []


def test_analysis_is_user_scoped_and_needs_login(client, auth_headers, other_headers, fixed_today):
    add_expense(client, other_headers, 5000, "2026-11-10")
    body = client.get("/analysis/summary", headers=auth_headers).json()
    assert D(body["report"]["current"]["total_spending"]) == 0
    for path in ("overspending", "anomalies", "forecast", "summary"):
        assert client.get(f"/analysis/{path}").status_code == 401