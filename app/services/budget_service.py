"""Budget persistence. EVERY query is scoped by user_id."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.models import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate


def create_budget(db: Session, user_id: int, data: BudgetCreate) -> Budget:
    budget = Budget(user_id=user_id, **data.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def list_budgets(
    db: Session,
    user_id: int,
    *,
    category: str | None = None,
    period: str | None = None,
) -> list[Budget]:
    stmt = select(Budget).where(Budget.user_id == user_id)
    if category is not None:
        stmt = stmt.where(Budget.category == category)
    if period is not None:
        stmt = stmt.where(Budget.period == period)
    return list(db.scalars(stmt.order_by(Budget.start_date.desc(), Budget.id.desc())))


def get_budget(db: Session, user_id: int, budget_id: int) -> Budget:
    budget = db.scalar(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    )
    if budget is None:
        raise NotFoundError("Budget")
    return budget


def update_budget(
    db: Session, user_id: int, budget_id: int, data: BudgetUpdate
) -> Budget:
    budget = get_budget(db, user_id, budget_id)
    for field, value in data.model_dump().items():
        setattr(budget, field, value)
    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, user_id: int, budget_id: int) -> None:
    budget = get_budget(db, user_id, budget_id)
    db.delete(budget)
    db.commit()