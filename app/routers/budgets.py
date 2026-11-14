from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.core.clock import Today
from app.core.dependencies import CurrentUser, DbSession
from app.database.enums import BudgetPeriod, Category
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from app.schemas.budget_check import BudgetCheckResponse
from app.services import budget_check_service, budget_service
from app.services.notification_service import build_alerts

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(data: BudgetCreate, db: DbSession, user: CurrentUser):
    return budget_service.create_budget(db, user.id, data)


@router.get("", response_model=list[BudgetRead])
def list_budgets(
    db: DbSession,
    user: CurrentUser,
    category: Category | None = None,
    period: BudgetPeriod | None = None,
):
    return budget_service.list_budgets(
        db, user.id,
        category=category.value if category else None,
        period=period.value if period else None,
    )


# Declared BEFORE any /budgets/{id} route so "check" is never read as an id.
@router.get("/check", response_model=BudgetCheckResponse)
def check_budgets(
    db: DbSession,
    user: CurrentUser,
    today: Today,
    reference_date: Annotated[
        date | None, Query(alias="date", description="Default: today (Asia/Bangkok)")
    ] = None,
):
    """Spent / remaining / status for every budget active on the given date."""
    ref = reference_date or today
    items = budget_check_service.check_budgets(db, user.id, ref)
    return BudgetCheckResponse(reference_date=ref, items=items, alerts=build_alerts(items))


@router.put("/{budget_id}", response_model=BudgetRead)
def update_budget(budget_id: int, data: BudgetUpdate, db: DbSession, user: CurrentUser):
    return budget_service.update_budget(db, user.id, budget_id, data)


@router.delete(
    "/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_budget(budget_id: int, db: DbSession, user: CurrentUser) -> None:
    budget_service.delete_budget(db, user.id, budget_id)