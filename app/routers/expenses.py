from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.core.dependencies import CurrentUser, DbSession
from app.database.enums import Category
from app.schemas.expense import ExpenseCreate, ExpenseList, ExpenseRead, ExpenseUpdate
from app.services import expense_service

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(data: ExpenseCreate, db: DbSession, user: CurrentUser):
    return expense_service.create_expense(db, user.id, data)


@router.get("", response_model=ExpenseList)
def list_expenses(
    db: DbSession,
    user: CurrentUser,
    start_date: date | None = None,
    end_date: date | None = None,
    category: Category | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be on or before end_date",
        )
    items, total, total_amount = expense_service.list_expenses(
        db, user.id, start_date=start_date, end_date=end_date,
        category=category.value if category else None, limit=limit, offset=offset,
    )
    return ExpenseList(
        items=items, total=total, total_amount=total_amount, limit=limit, offset=offset
    )


@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense(expense_id: int, db: DbSession, user: CurrentUser):
    return expense_service.get_expense(db, user.id, expense_id)


@router.put("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: int, data: ExpenseUpdate, db: DbSession, user: CurrentUser
):
    return expense_service.update_expense(db, user.id, expense_id, data)


@router.delete(
    "/{expense_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_expense(expense_id: int, db: DbSession, user: CurrentUser) -> None:
    expense_service.delete_expense(db, user.id, expense_id)