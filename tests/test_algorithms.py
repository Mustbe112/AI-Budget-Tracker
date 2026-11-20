"""Pure unit tests: no database, no HTTP. Realistic Thai Baht examples."""
from datetime import date
from decimal import Decimal as D

import pytest

from app.algorithms import anomaly_detection as ad
from app.algorithms import budget_calculator as bc
from app.algorithms import spending_analysis as sa
from app.algorithms import spending_forecast as sf
from app.algorithms.common import ExpenseRecord
from app.utils.dates import period_window, previous_window


def exp(amount, category="food", day=date(2026, 11, 11), id=None):
    return ExpenseRecord(amount=D(str(amount)), category=category, expense_date=day, id=id)


# ---------------- dates ----------------

def test_period_windows():
    wed = date(2026, 11, 11)  # a Wednesday
    assert period_window("daily", wed) == (wed, wed)
    assert period_window("weekly", wed) == (date(2026, 11, 9), date(2026, 11, 15))
    assert period_window("monthly", wed) == (date(2026, 11, 1), date(2026, 11, 30))
    assert period_window("monthly", date(2028, 2, 10))[1] == date(2028, 2, 29)  # leap year


def test_previous_windows_cross_month_and_year():
    assert previous_window("weekly", date(2026, 11, 11)) == (date(2026, 11, 2), date(2026, 11, 8))
    assert previous_window("monthly", date(2026, 1, 15)) == (date(2025, 12, 1), date(2025, 12, 31))
    assert previous_window("daily", date(2026, 3, 1)) == (date(2026, 2, 28), date(2026, 2, 28))


def test_unknown_period_rejected():
    with pytest.raises(ValueError):
        period_window("yearly", date(2026, 11, 11))


# ---------------- Algorithm 1: budget ----------------

def test_spec_example_daily_food_budget_exceeded():
    # Breakfast 50 + lunch 80 + dinner 90 = 220 against a 150 budget.
    spec = bc.BudgetSpec(amount=D("150"), period="daily", category="food")
    result = bc.evaluate_budget(spec, [exp(50), exp(80), exp(90)], date(2026, 11, 11))
    assert result.total_spent == D("220.00")
    assert result.overspent_amount == D("70.00")
    assert result.remaining == D("-70.00")
    assert result.status == bc.EXCEEDED
    assert result.utilization_percent == D("146.67")


def test_within_and_near_limit_statuses():
    ok = bc.calculate_budget_status(D("150"), [D("50")])
    assert ok["status"] == bc.WITHIN_BUDGET and ok["remaining"] == D("100.00")
    near = bc.calculate_budget_status(D("150"), [D("130")])   # 86.67%
    assert near["status"] == bc.NEAR_LIMIT
    exact = bc.calculate_budget_status(D("150"), [D("150")])  # exactly on budget
    assert exact["status"] == bc.NEAR_LIMIT and exact["overspent_amount"] == D("0.00")


def test_weekly_budget_only_counts_that_week_and_category():
    spec = bc.BudgetSpec(amount=D("800"), period="weekly", category="food")
    expenses = [
        exp(300, day=date(2026, 11, 9)),                       # Monday, in week
        exp(250, day=date(2026, 11, 15)),                      # Sunday, in week
        exp(999, day=date(2026, 11, 8)),                       # previous Sunday, excluded
        exp(400, category="transport", day=date(2026, 11, 10)),  # other category, excluded
    ]
    result = bc.evaluate_budget(spec, expenses, date(2026, 11, 11))
    assert result.total_spent == D("550.00")
    assert (result.window_start, result.window_end) == (date(2026, 11, 9), date(2026, 11, 15))


def test_overall_monthly_budget_counts_all_categories():
    spec = bc.BudgetSpec(amount=D("15000"), period="monthly", category=None)
    expenses = [exp(5000, "bills", date(2026, 11, 1)), exp(2500.50, "food", date(2026, 11, 20))]
    result = bc.evaluate_budget(spec, expenses, date(2026, 11, 11))
    assert result.total_spent == D("7500.50")
    assert result.status == bc.WITHIN_BUDGET


def test_decimal_precision_no_float_errors():
    # 0.1 + 0.2 style bug must not appear with Decimal.
    r = bc.calculate_budget_status(D("1"), [D("0.10"), D("0.20")])
    assert r["total_spent"] == D("0.30")


def test_invalid_budget_amount_rejected():
    with pytest.raises(ValueError):
        bc.calculate_budget_status(D("0"), [D("10")])


# ---------------- Algorithm 2: IQR ----------------

FOOD_HISTORY = [100, 110, 120, 130, 140, 150, 160, 170]  # typical meals


def test_quartile_interpolation():
    vals = [D(v) for v in (100, 110, 120, 130, 140, 150, 160, 170, 1000)]
    assert ad.quartile(vals, D("0.25")) == D("120")
    assert ad.quartile(vals, D("0.75")) == D("160")


def test_iqr_flags_unusually_high_expense():
    expenses = [exp(a, id=i) for i, a in enumerate(FOOD_HISTORY + [1000], start=1)]
    [result] = ad.detect_anomalies(expenses)
    assert result.status == ad.ANALYZED
    assert (result.q1, result.q3, result.iqr) == (D("120.00"), D("160.00"), D("40.00"))
    assert result.upper_bound == D("220.00")      # 160 + 1.5 * 40
    assert [a.expense_id for a in result.anomalies] == [9]
    assert result.anomalies[0].excess_over_bound == D("780.00")


def test_value_equal_to_upper_bound_is_not_flagged():
    expenses = [exp(a) for a in FOOD_HISTORY + [220]]
    [result] = ad.detect_anomalies(expenses)
    assert result.anomalies == []


def test_insufficient_data_is_handled_gracefully():
    [result] = ad.detect_anomalies([exp(100), exp(5000)])
    assert result.status == ad.INSUFFICIENT_DATA
    assert result.anomalies == [] and result.q1 is None
    assert "at least 8" in result.message


def test_categories_are_analyzed_independently():
    food = [exp(a, "food") for a in FOOD_HISTORY]
    rent = [exp(9000, "bills") for _ in range(8)]
    results = {r.category: r for r in ad.detect_anomalies(food + rent + [exp(9000, "bills")])}
    # 9,000 is normal for bills; it would be a huge outlier if mixed with food.
    assert results["bills"].status == ad.NO_VARIATION
    assert results["food"].anomalies == []


def test_no_variation_does_not_flag_noise():
    expenses = [exp(50) for _ in range(8)] + [exp(51)]
    [result] = ad.detect_anomalies(expenses)
    assert result.status == ad.NO_VARIATION and result.anomalies == []


def test_detection_never_modifies_or_drops_input():
    expenses = [exp(a) for a in FOOD_HISTORY + [1000]]
    before = list(expenses)
    ad.detect_anomalies(expenses)
    assert expenses == before and len(expenses) == 9


# ---------------- Algorithm 3: analysis ----------------

def test_spec_example_weekly_food_increase_is_25_percent():
    assert sa.percentage_change(D("800"), D("1000")) == D("25.00")
    assert sa.percentage_change(D("1000"), D("800")) == D("-20.00")


def test_percentage_change_handles_zero_safely():
    assert sa.percentage_change(D("0"), D("0")) == D("0.00")
    assert sa.percentage_change(D("0"), D("500")) is None   # undefined, not a crash


def test_summarize_period():
    start, end = date(2026, 11, 9), date(2026, 11, 15)
    expenses = [
        exp(600, "food", date(2026, 11, 9)), exp(400, "food", date(2026, 11, 12)),
        exp(300, "transport", date(2026, 11, 10)),
        exp(999, "food", date(2026, 11, 16)),               # outside the window
    ]
    s = sa.summarize_period(expenses, start, end, budget_amount=D("2000"))
    assert s.days == 7
    assert s.total_spending == D("1300.00")
    assert s.average_daily_spending == D("185.71")          # 1300 / 7
    assert s.transaction_count == 3
    assert [c.category for c in s.by_category] == ["food", "transport"]
    assert s.by_category[0].total == D("1000.00")
    assert s.by_category[0].share_percent == D("76.92")
    assert s.budget_utilization_percent == D("65.00")


def test_summary_with_no_spending_and_no_budget():
    s = sa.summarize_period([], date(2026, 11, 1), date(2026, 11, 7))
    assert s.total_spending == D("0.00") and s.average_daily_spending == D("0.00")
    assert s.by_category == [] and s.budget_utilization_percent is None


def test_summary_with_zero_budget_does_not_divide_by_zero():
    s = sa.summarize_period([exp(100)], date(2026, 11, 11), date(2026, 11, 11), D("0"))
    assert s.budget_utilization_percent is None


def test_compare_periods_with_new_and_dropped_categories():
    prev_s = sa.summarize_period(
        [exp(800, "food", date(2026, 11, 2)), exp(200, "bills", date(2026, 11, 3))],
        date(2026, 11, 2), date(2026, 11, 8))
    cur_s = sa.summarize_period(
        [exp(1000, "food", date(2026, 11, 9)), exp(150, "health", date(2026, 11, 10))],
        date(2026, 11, 9), date(2026, 11, 15))
    cmp = sa.compare_periods(prev_s, cur_s)
    assert cmp.change_percent == D("15.00")                 # 1000 -> 1150
    by_cat = {c.category: c for c in cmp.categories}
    assert by_cat["food"].change_percent == D("25.00") and by_cat["food"].trend == sa.INCREASE
    assert by_cat["bills"].change_percent == D("-100.00") and by_cat["bills"].trend == sa.DECREASE
    assert by_cat["health"].change_percent is None          # new category, previous was 0


def test_summarize_rejects_reversed_dates():
    with pytest.raises(ValueError):
        sa.summarize_period([], date(2026, 11, 10), date(2026, 11, 1))


# ---------------- Algorithm 4: forecast ----------------

def test_spec_example_five_day_average_is_140():
    r = sf.forecast_spending([D(x) for x in (100, 120, 150, 130, 200)], window=5)
    assert r.status == sf.OK
    assert r.moving_average == D("140.00")
    assert r.forecast_next_day == D("140.00")
    assert r.forecast_total == D("980.00")                  # 7 days * 140
    assert r.trend == sf.UNKNOWN                            # only one window of history
    assert "not a guarantee" in r.disclaimer


def test_window_is_configurable():
    amounts = [D(x) for x in (100, 120, 150, 130, 200)]
    r3 = sf.forecast_spending(amounts, window=3)
    assert r3.moving_average == D("160.00")                 # (150+130+200)/3
    assert r3.moving_average_series == [D("123.33"), D("133.33"), D("160.00")]


def test_trend_detection():
    rising = sf.forecast_spending([D(x) for x in (100, 100, 100, 200, 200, 200)], window=3)
    assert rising.trend == sf.INCREASING and rising.trend_change_percent == D("100.00")
    falling = sf.forecast_spending([D(x) for x in (200, 200, 200, 100, 100, 100)], window=3)
    assert falling.trend == sf.DECREASING
    flat = sf.forecast_spending([D(x) for x in (100, 102, 98, 101, 99, 100)], window=3)
    assert flat.trend == sf.STABLE


def test_insufficient_history():
    r = sf.forecast_spending([D("100"), D("120")], window=5)
    assert r.status == sf.INSUFFICIENT_DATA
    assert r.moving_average is None and r.forecast_total is None
    assert r.disclaimer                                     # disclaimer is always present


def test_invalid_parameters_rejected():
    with pytest.raises(ValueError):
        sf.forecast_spending([D("1")], window=0)
    with pytest.raises(ValueError):
        sf.forecast_spending([D("1")], window=1, horizon_days=0)


def test_build_daily_series_fills_empty_days_with_zero():
    expenses = [exp(100, day=date(2026, 11, 9)), exp(50, day=date(2026, 11, 9)),
                exp(80, day=date(2026, 11, 11)), exp(999, day=date(2026, 11, 20))]
    series = sf.build_daily_series(expenses, date(2026, 11, 9), date(2026, 11, 12))
    assert series == [D("150.00"), D("0.00"), D("80.00"), D("0.00")]