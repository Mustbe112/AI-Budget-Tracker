from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.core.clock import Today
from app.core.config import settings
from app.core.dependencies import CurrentUser, DbSession
from app.database.enums import BudgetPeriod, Category
from app.schemas.analysis import (
    AnalysisSummary, AnomalyReport, ForecastReport, OverspendingReport,
)
from app.services import analysis_service

router = APIRouter(prefix="/analysis", tags=["analysis"])

RefDate = Annotated[
    date | None,
    Query(alias="date", description="Default: today (Asia/Bangkok)"),
]


@router.get("/overspending", response_model=OverspendingReport)
def overspending(db: DbSession, user: CurrentUser, today: Today, reference_date: RefDate = None):
    """Only the budgets that are currently exceeded."""
    return analysis_service.overspending(db, user.id, reference_date or today)


@router.get("/anomalies", response_model=AnomalyReport)
def anomalies(
    db: DbSession, user: CurrentUser, today: Today,
    lookback_days: int = Query(180, ge=7, le=730),
    category: Category | None = None,
):
    """IQR-based unusual expenses. Expenses are flagged, never changed."""
    return analysis_service.anomalies(
        db, user.id, today, lookback_days, category.value if category else None)


@router.get("/forecast", response_model=ForecastReport)
def forecast(
    db: DbSession, user: CurrentUser, today: Today,
    history_days: int = Query(30, ge=1, le=365),
    window: int = Query(settings.forecast_window_days, ge=1, le=60),
    horizon_days: int = Query(7, ge=1, le=90),
):
    """Moving-average estimate of future daily spending. An estimate, not a guarantee."""
    return analysis_service.forecast(db, user.id, today, history_days, window, horizon_days)


@router.get("/summary", response_model=AnalysisSummary)
def summary(
    db: DbSession, user: CurrentUser, today: Today,
    period: BudgetPeriod = BudgetPeriod.MONTHLY, reference_date: RefDate = None,
):
    """Spending summary + comparison with the previous period + budget status + alerts."""
    return analysis_service.summary(db, user.id, period, reference_date or today)