"""Runs Algorithm 1 against a user's real budgets and expenses."""
from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.algorithms.budget_calculator import BudgetSpec, evaluate_budget
from app.database.models import Budget
from app.schemas.budget_check import BudgetCheckItem
from app.services.records import load_expense_records
from app.utils.dates import period_window


def active_budgets(db: Session, user_id: int, ref: date) -> list[Budget]:
    """Budgets whose [start_date, end_date] range contains `ref`."""
    return list(db.scalars(
        select(Budget)
        .where(Budget.user_id == user_id, Budget.start_date <= ref,
               or_(Budget.end_date.is_(None), Budget.end_date >= ref))
        .order_by(Budget.start_date.desc(), Budget.id.desc())
    ))


def check_budgets(db: Session, user_id: int, ref: date) -> list[BudgetCheckItem]:
    budgets = active_budgets(db, user_id, ref)
    if not budgets:
        return []

    # One query covering every budget's window, instead of one query per budget.
    windows = [period_window(b.period, ref) for b in budgets]
    records = load_expense_records(
        db, user_id, min(w[0] for w in windows), max(w[1] for w in windows))

    items: list[BudgetCheckItem] = []
    for budget, (win_start, win_end) in zip(budgets, windows):
        # A budget created mid-week/month only counts spending from its own
        # start_date (and up to its end_date, if it has one).
        lo = max(win_start, budget.start_date)
        hi = min(win_end, budget.end_date) if budget.end_date else win_end
        scoped = [r for r in records if lo <= r.expense_date <= hi]
        status = evaluate_budget(
            BudgetSpec(amount=Decimal(str(budget.amount)), period=budget.period,
                       category=budget.category),
            scoped, ref)
        items.append(BudgetCheckItem(budget_id=budget.id, status=status))
    return items


def overall_budget_amount(db: Session, user_id: int, period: str, ref: date) -> Decimal | None:
    """The overall (all-category) budget for this period type, if any.
    If several are active, the most recently started one wins."""
    for budget in active_budgets(db, user_id, ref):
        if budget.category is None and budget.period == str(period):
            return Decimal(str(budget.amount))
    return None