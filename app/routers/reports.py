from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.core.clock import Today
from app.core.dependencies import CurrentUser, DbSession
from app.database.enums import BudgetPeriod
from app.schemas.report import CategoryReport, ComparisonReport, SpendingReport
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])

RefDate = Annotated[
    date | None,
    Query(alias="date", description="Any date inside the period. Default: today (Asia/Bangkok)"),
]
MAX_RANGE_DAYS = 366


@router.get("/daily", response_model=SpendingReport)
def daily_report(db: DbSession, user: CurrentUser, today: Today, reference_date: RefDate = None):
    return report_service.spending_report(db, user.id, BudgetPeriod.DAILY, reference_date or today)


@router.get("/weekly", response_model=SpendingReport)
def weekly_report(db: DbSession, user: CurrentUser, today: Today, reference_date: RefDate = None):
    """Monday to Sunday of the week containing the date."""
    return report_service.spending_report(db, user.id, BudgetPeriod.WEEKLY, reference_date or today)


@router.get("/monthly", response_model=SpendingReport)
def monthly_report(db: DbSession, user: CurrentUser, today: Today, reference_date: RefDate = None):
    return report_service.spending_report(db, user.id, BudgetPeriod.MONTHLY, reference_date or today)


@router.get("/categories", response_model=CategoryReport)
def category_report(
    db: DbSession, user: CurrentUser, today: Today,
    start_date: date | None = None, end_date: date | None = None,
):
    """Spending grouped by category. Default range: first of this month to today."""
    end = end_date or today
    start = start_date or end.replace(day=1)
    if start > end:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
    if (end - start) > timedelta(days=MAX_RANGE_DAYS):
        raise HTTPException(status_code=422, detail=f"Date range cannot exceed {MAX_RANGE_DAYS} days")
    return report_service.category_report(db, user.id, start, end)


@router.get("/comparison", response_model=ComparisonReport)
def comparison_report(
    db: DbSession, user: CurrentUser, today: Today,
    period: BudgetPeriod = BudgetPeriod.WEEKLY, reference_date: RefDate = None,
):
    """The period containing the date vs the whole period before it."""
    return report_service.comparison_report(db, user.id, period, reference_date or today)