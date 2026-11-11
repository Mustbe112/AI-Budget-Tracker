from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.income import IncomeCreate, IncomeList, IncomeRead, IncomeUpdate
from app.services import income_service

router = APIRouter(prefix="/income", tags=["income"])


@router.post("", response_model=IncomeRead, status_code=status.HTTP_201_CREATED)
def create_income(data: IncomeCreate, db: DbSession, user: CurrentUser):
    return income_service.create_income(db, user.id, data)


@router.get("", response_model=IncomeList)
def list_income(
    db: DbSession, user: CurrentUser,
    start_date: date | None = None, end_date: date | None = None,
    limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
    items, total, total_amount = income_service.list_income(
        db, user.id, start_date=start_date, end_date=end_date, limit=limit, offset=offset)
    return IncomeList(items=items, total=total, total_amount=total_amount,
                      limit=limit, offset=offset)


@router.put("/{income_id}", response_model=IncomeRead)
def update_income(income_id: int, data: IncomeUpdate, db: DbSession, user: CurrentUser):
    return income_service.update_income(db, user.id, income_id, data)


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_income(income_id: int, db: DbSession, user: CurrentUser) -> None:
    income_service.delete_income(db, user.id, income_id)