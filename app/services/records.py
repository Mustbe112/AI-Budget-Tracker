"""Bridge between the database and the pure algorithms.
Loads a user's expenses as lightweight ExpenseRecord objects (user-scoped)."""
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.algorithms.common import ExpenseRecord
from app.database.models import Expense


def load_expense_records(
    db: Session, user_id: int, start: date, end: date, category: str | None = None
) -> list[ExpenseRecord]:
    stmt = select(Expense.id, Expense.category, Expense.amount, Expense.expense_date).where(
        Expense.user_id == user_id,
        Expense.expense_date >= start,
        Expense.expense_date <= end,
    )
    if category is not None:
        stmt = stmt.where(Expense.category == category)
    return [
        ExpenseRecord(id=r.id, category=r.category, amount=Decimal(str(r.amount)),
                      expense_date=r.expense_date)
        for r in db.execute(stmt)
    ]