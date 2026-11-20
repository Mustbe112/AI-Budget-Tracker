"""Algorithm 3: statistical spending analysis and period comparison."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Iterable

from app.algorithms.common import ExpenseRecord, money, percent, total

INCREASE = "increase"
DECREASE = "decrease"
UNCHANGED = "unchanged"


@dataclass(frozen=True)
class CategoryTotal:
    category: str
    total: Decimal
    share_percent: Decimal | None     # share of the period's total spending


@dataclass(frozen=True)
class PeriodSummary:
    start: date
    end: date
    days: int
    total_spending: Decimal
    transaction_count: int
    average_daily_spending: Decimal
    by_category: list[CategoryTotal] = field(default_factory=list)
    budget_amount: Decimal | None = None
    budget_utilization_percent: Decimal | None = None   # None if no budget / budget is 0

    def category_total(self, category: str) -> Decimal:
        for c in self.by_category:
            if c.category == category:
                return c.total
        return Decimal("0.00")


@dataclass(frozen=True)
class CategoryChange:
    category: str
    previous: Decimal
    current: Decimal
    change_amount: Decimal
    change_percent: Decimal | None    # None when previous is 0 (undefined)
    trend: str


@dataclass(frozen=True)
class PeriodComparison:
    previous_total: Decimal
    current_total: Decimal
    change_amount: Decimal
    change_percent: Decimal | None
    trend: str
    categories: list[CategoryChange]


def percentage_change(previous: Decimal, current: Decimal) -> Decimal | None:
    """(current - previous) / previous * 100.
    previous == 0 and current == 0 -> 0 (nothing changed).
    previous == 0 and current  > 0 -> None (infinite growth is not a number)."""
    if previous == 0:
        return Decimal("0.00") if current == 0 else None
    return percent(current - previous, previous)


def _trend(previous: Decimal, current: Decimal) -> str:
    if current > previous:
        return INCREASE
    if current < previous:
        return DECREASE
    return UNCHANGED


def summarize_period(
    expenses: Iterable[ExpenseRecord],
    start: date,
    end: date,
    budget_amount: Decimal | None = None,
) -> PeriodSummary:
    """Total, average daily, per-category totals and budget utilisation for [start, end]."""
    if end < start:
        raise ValueError("end must be on or after start")

    in_window = [e for e in expenses if start <= e.expense_date <= end]
    days = (end - start).days + 1                      # inclusive day count
    grand_total = money(total(e.amount for e in in_window))

    per_category: dict[str, Decimal] = {}
    for e in in_window:
        per_category[e.category] = per_category.get(e.category, Decimal("0")) + e.amount

    by_category = sorted(
        (CategoryTotal(c, money(v), percent(v, grand_total)) for c, v in per_category.items()),
        key=lambda c: c.total, reverse=True,           # biggest spending first
    )

    utilization = None
    if budget_amount is not None and budget_amount > 0:
        utilization = percent(grand_total, budget_amount)

    return PeriodSummary(
        start=start, end=end, days=days, total_spending=grand_total,
        transaction_count=len(in_window),
        average_daily_spending=money(grand_total / days),
        by_category=by_category,
        budget_amount=money(budget_amount) if budget_amount is not None else None,
        budget_utilization_percent=utilization,
    )


def compare_periods(previous: PeriodSummary, current: PeriodSummary) -> PeriodComparison:
    """Compare two summaries, overall and for every category seen in either."""
    categories = sorted(
        {c.category for c in previous.by_category} | {c.category for c in current.by_category}
    )
    changes = []
    for cat in categories:
        prev, cur = previous.category_total(cat), current.category_total(cat)
        changes.append(CategoryChange(
            category=cat, previous=prev, current=cur,
            change_amount=money(cur - prev),
            change_percent=percentage_change(prev, cur),
            trend=_trend(prev, cur),
        ))
    return PeriodComparison(
        previous_total=previous.total_spending,
        current_total=current.total_spending,
        change_amount=money(current.total_spending - previous.total_spending),
        change_percent=percentage_change(previous.total_spending, current.total_spending),
        trend=_trend(previous.total_spending, current.total_spending),
        categories=changes,
    )