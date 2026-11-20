"""Algorithm 1: rule-based budget calculation.

Rules (no AI, fully deterministic):
    total_spent = sum of matching expenses
    remaining   = budget - total_spent          (negative when overspent)
    overspent   = max(total_spent - budget, 0)
    status      = exceeded    if total_spent > budget
                  near_limit  if utilisation >= warning threshold (default 80%)
                  within_budget otherwise
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from app.algorithms.common import ExpenseRecord, money, percent, total
from app.utils.dates import period_window

WITHIN_BUDGET = "within_budget"
NEAR_LIMIT = "near_limit"
EXCEEDED = "exceeded"

DEFAULT_WARNING_PERCENT = Decimal("80")


@dataclass(frozen=True)
class BudgetSpec:
    amount: Decimal
    period: str                    # "daily" | "weekly" | "monthly"
    category: str | None = None    # None = overall budget (all categories)


@dataclass(frozen=True)
class BudgetStatus:
    category: str | None
    period: str
    window_start: date | None
    window_end: date | None
    budget_amount: Decimal
    total_spent: Decimal
    remaining: Decimal             # negative when exceeded
    overspent_amount: Decimal      # 0 when not exceeded
    utilization_percent: Decimal   # spent / budget * 100
    status: str


def calculate_budget_status(
    budget_amount: Decimal,
    spent_amounts: Iterable[Decimal],
    warning_percent: Decimal = DEFAULT_WARNING_PERCENT,
) -> dict:
    """Core arithmetic on plain numbers. Returns the computed fields as a dict."""
    if budget_amount <= 0:
        raise ValueError("budget_amount must be greater than 0")

    spent = money(total(spent_amounts))
    budget = money(budget_amount)
    remaining = budget - spent                       # step 1: remaining budget
    overspent = max(spent - budget, Decimal("0.00"))  # step 2: overage, never negative
    utilization = percent(spent, budget)              # step 3: % used (budget > 0, so never None)

    if spent > budget:                                # step 4: pick the status
        status = EXCEEDED
    elif utilization >= warning_percent:
        status = NEAR_LIMIT
    else:
        status = WITHIN_BUDGET

    return {
        "budget_amount": budget,
        "total_spent": spent,
        "remaining": remaining,
        "overspent_amount": overspent,
        "utilization_percent": utilization,
        "status": status,
    }


def evaluate_budget(
    spec: BudgetSpec,
    expenses: Iterable[ExpenseRecord],
    reference_date: date,
    warning_percent: Decimal = DEFAULT_WARNING_PERCENT,
) -> BudgetStatus:
    """Evaluate one budget for the period (day/week/month) containing reference_date.

    Supports daily, weekly and monthly budgets, overall or per category.
    Whether the budget is active on that date (its start/end dates) is checked
    by the service layer before calling this.
    """
    start, end = period_window(spec.period, reference_date)

    matching = [
        e.amount
        for e in expenses
        if start <= e.expense_date <= end
        and (spec.category is None or e.category == spec.category)
    ]
    result = calculate_budget_status(spec.amount, matching, warning_percent)
    return BudgetStatus(
        category=spec.category,
        period=str(spec.period),
        window_start=start,
        window_end=end,
        **result,
    )