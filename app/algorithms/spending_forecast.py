"""Algorithm 4: moving-average spending forecast.

Simple moving average (SMA): the forecast for each coming day is the mean of
the last `window` days. It's an estimate, not a promise.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from app.algorithms.common import ExpenseRecord, money, percent, total

OK = "ok"
INSUFFICIENT_DATA = "insufficient_data"

INCREASING = "increasing"
DECREASING = "decreasing"
STABLE = "stable"
UNKNOWN = "unknown"

DEFAULT_WINDOW = 5
DEFAULT_HORIZON = 7
DEFAULT_TREND_THRESHOLD = Decimal("5")   # +-5% counts as "stable"

DISCLAIMER = (
    "This forecast is an estimate based on recent spending. It is not a "
    "guarantee of future expenses."
)


@dataclass(frozen=True)
class ForecastResult:
    status: str                                  # ok | insufficient_data
    window: int
    days_of_data: int
    moving_average: Decimal | None = None        # mean of the last `window` days
    forecast_next_day: Decimal | None = None
    horizon_days: int = DEFAULT_HORIZON
    forecast_total: Decimal | None = None        # next_day * horizon_days
    trend: str = UNKNOWN
    trend_change_percent: Decimal | None = None
    moving_average_series: list[Decimal] = field(default_factory=list)  # for charts
    message: str = ""
    disclaimer: str = DISCLAIMER


def build_daily_series(
    expenses: Iterable[ExpenseRecord], start: date, end: date
) -> list[Decimal]:
    """One total per calendar day from start to end. Days with no spending count
    as 0, otherwise the average would be inflated."""
    if end < start:
        raise ValueError("end must be on or after start")
    per_day: dict[date, Decimal] = {}
    for e in expenses:
        if start <= e.expense_date <= end:
            per_day[e.expense_date] = per_day.get(e.expense_date, Decimal("0")) + e.amount
    days = (end - start).days + 1
    return [money(per_day.get(start + timedelta(days=i), Decimal("0"))) for i in range(days)]


def forecast_spending(
    daily_amounts: list[Decimal],
    window: int = DEFAULT_WINDOW,
    horizon_days: int = DEFAULT_HORIZON,
    trend_threshold_percent: Decimal = DEFAULT_TREND_THRESHOLD,
) -> ForecastResult:
    if window < 1:
        raise ValueError("window must be at least 1")
    if horizon_days < 1:
        raise ValueError("horizon_days must be at least 1")

    n = len(daily_amounts)
    if n < window:
        return ForecastResult(
            status=INSUFFICIENT_DATA, window=window, days_of_data=n,
            horizon_days=horizon_days,
            message=f"Need at least {window} days of history to forecast; found {n}.",
        )

    # Step 1: moving-average series (one value per full window).
    series = [
        money(total(daily_amounts[i - window + 1: i + 1]) / window)
        for i in range(window - 1, n)
    ]

    # Step 2: the forecast is the most recent average, held flat.
    moving_average = series[-1]
    forecast_total = money(moving_average * horizon_days)

    # Step 3: trend = latest window vs the window before it (or all earlier days
    # when there is less than two windows of data).
    recent = daily_amounts[-window:]
    earlier = daily_amounts[-2 * window:-window] if n >= 2 * window else daily_amounts[:-window]
    trend, change = UNKNOWN, None
    if earlier:
        recent_avg = total(recent) / len(recent)
        earlier_avg = total(earlier) / len(earlier)
        if earlier_avg == 0:
            trend = INCREASING if recent_avg > 0 else STABLE
        else:
            change = percent(recent_avg - earlier_avg, earlier_avg)
            if change > trend_threshold_percent:
                trend = INCREASING
            elif change < -trend_threshold_percent:
                trend = DECREASING
            else:
                trend = STABLE

    return ForecastResult(
        status=OK, window=window, days_of_data=n, moving_average=moving_average,
        forecast_next_day=moving_average, horizon_days=horizon_days,
        forecast_total=forecast_total, trend=trend, trend_change_percent=change,
        moving_average_series=series,
        message=f"Estimated daily spending is {moving_average} "
                f"(average of the last {window} days).",
    )