"""Expense persistence. EVERY query is scoped by user_id."""
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.models import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


def create_expense(db: Session, user_id: int, data: ExpenseCreate) -> Expense:
    expense = Expense(user_id=user_id, **data.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(
    db: Session,
    user_id: int,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Expense], int, Decimal]:
    """Return (page of expenses, total matching count, total matching amount)."""
    conditions = [Expense.user_id == user_id]
    if start_date is not None:
        conditions.append(Expense.expense_date >= start_date)
    if end_date is not None:
        conditions.append(Expense.expense_date <= end_date)
    if category is not None:
        conditions.append(Expense.category == category)

    count, amount_sum = db.execute(
        select(func.count(Expense.id), func.coalesce(func.sum(Expense.amount), 0))
        .where(*conditions)
    ).one()

    items = db.scalars(
        select(Expense)
        .where(*conditions)
        .order_by(Expense.expense_date.desc(), Expense.id.desc())  # newest first
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), int(count), Decimal(str(amount_sum))


def get_expense(db: Session, user_id: int, expense_id: int) -> Expense:
    expense = db.scalar(
        select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id)
    )
    if expense is None:  # same error whether missing or owned by someone else
        raise NotFoundError("Expense")
    return expense


def update_expense(
    db: Session, user_id: int, expense_id: int, data: ExpenseUpdate
) -> Expense:
    expense = get_expense(db, user_id, expense_id)
    for field, value in data.model_dump().items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, user_id: int, expense_id: int) -> None:
    expense = get_expense(db, user_id, expense_id)
    db.delete(expense)
    db.commit()