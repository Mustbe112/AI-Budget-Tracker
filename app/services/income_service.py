"""Income persistence. EVERY query is scoped by user_id."""
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.models import Income
from app.schemas.income import IncomeCreate, IncomeUpdate


def create_income(db: Session, user_id: int, data: IncomeCreate) -> Income:
    income = Income(user_id=user_id, **data.model_dump())
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


def list_income(
    db: Session, user_id: int, *, start_date: date | None = None,
    end_date: date | None = None, limit: int = 50, offset: int = 0,
) -> tuple[list[Income], int, Decimal]:
    conditions = [Income.user_id == user_id]
    if start_date is not None:
        conditions.append(Income.income_date >= start_date)
    if end_date is not None:
        conditions.append(Income.income_date <= end_date)
    count, amount_sum = db.execute(
        select(func.count(Income.id), func.coalesce(func.sum(Income.amount), 0)).where(*conditions)
    ).one()
    items = db.scalars(
        select(Income).where(*conditions)
        .order_by(Income.income_date.desc(), Income.id.desc())
        .limit(limit).offset(offset)
    ).all()
    return list(items), int(count), Decimal(str(amount_sum))


def total_income(db: Session, user_id: int, start: date, end: date) -> Decimal:
    value = db.scalar(
        select(func.coalesce(func.sum(Income.amount), 0)).where(
            Income.user_id == user_id, Income.income_date >= start, Income.income_date <= end)
    )
    return Decimal(str(value)).quantize(Decimal("0.01"))


def get_income(db: Session, user_id: int, income_id: int) -> Income:
    income = db.scalar(select(Income).where(Income.id == income_id, Income.user_id == user_id))
    if income is None:
        raise NotFoundError("Income")
    return income


def update_income(db: Session, user_id: int, income_id: int, data: IncomeUpdate) -> Income:
    income = get_income(db, user_id, income_id)
    for field, value in data.model_dump().items():
        setattr(income, field, value)
    db.commit()
    db.refresh(income)
    return income


def delete_income(db: Session, user_id: int, income_id: int) -> None:
    db.delete(get_income(db, user_id, income_id))
    db.commit()