"""Date-window helpers shared by budgets, reports and algorithms (pure functions)."""
import calendar
from datetime import date, timedelta

from app.database.enums import BudgetPeriod


def period_window(period: str, reference: date) -> tuple[date, date]:
    """Return (start, end), both inclusive, of the period containing `reference`.

    daily   -> that single day
    weekly  -> Monday..Sunday
    monthly -> first..last day of the month
    """
    p = BudgetPeriod(period)  # raises ValueError for an unknown period
    if p is BudgetPeriod.DAILY:
        return reference, reference
    if p is BudgetPeriod.WEEKLY:
        start = reference - timedelta(days=reference.weekday())  # Monday = 0
        return start, start + timedelta(days=6)
    last_day = calendar.monthrange(reference.year, reference.month)[1]
    return reference.replace(day=1), reference.replace(day=last_day)


def previous_window(period: str, reference: date) -> tuple[date, date]:
    """The period immediately before the one containing `reference`."""
    start, _ = period_window(period, reference)
    return period_window(period, start - timedelta(days=1))