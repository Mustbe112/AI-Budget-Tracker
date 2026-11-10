from fastapi import APIRouter, Response, status

from app.core.dependencies import CurrentUser, DbSession
from app.database.enums import BudgetPeriod, Category
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from app.services import budget_service

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


# NOTE: GET /budgets/check is added in Step 6. It must be declared BEFORE any
# GET /budgets/{id} route, or FastAPI would treat "check" as an id.


@router.put("/{budget_id}", response_model=BudgetRead)
def update_budget(budget_id: int, data: BudgetUpdate, db: DbSession, user: CurrentUser):
    return budget_service.update_budget(db, user.id, budget_id, data)


@router.delete(
    "/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_budget(budget_id: int, db: DbSession, user: CurrentUser) -> None:
    budget_service.delete_budget(db, user.id, budget_id)