"""Glues the algorithms to a user's data for the /analysis endpoints."""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.algorithms.anomaly_detection import detect_anomalies
from app.algorithms.budget_calculator import EXCEEDED
from app.algorithms.spending_forecast import build_daily_series, forecast_spending
from app.core.config import settings
from app.schemas.analysis import (
    AnalysisSummary, AnomalyReport, ForecastReport, OverspendingReport,
)
from app.services import report_service
from app.services.budget_check_service import check_budgets
from app.services.notification_service import build_alerts
from app.services.records import load_expense_records


def overspending(db: Session, user_id: int, ref: date) -> OverspendingReport:
    exceeded = [i for i in check_budgets(db, user_id, ref) if i.status.status == EXCEEDED]
    return OverspendingReport(reference_date=ref, exceeded_count=len(exceeded),
                              items=exceeded, alerts=build_alerts(exceeded))


def anomalies(db: Session, user_id: int, today: date, lookback_days: int,
              category: str | None) -> AnomalyReport:
    start = today - timedelta(days=lookback_days - 1)
    records = load_expense_records(db, user_id, start, today, category)
    results = detect_anomalies(records, min_samples=settings.anomaly_min_samples)
    return AnomalyReport(
        lookback_start=start, lookback_end=today, min_samples=settings.anomaly_min_samples,
        total_anomalies=sum(len(r.anomalies) for r in results), categories=results)


def forecast(db: Session, user_id: int, today: date, history_days: int,
             window: int, horizon_days: int) -> ForecastReport:
    # Use COMPLETED days only. Today is still in progress, and counting a
    # half-finished day would drag the average down.
    history_end = today - timedelta(days=1)
    history_start = history_end - timedelta(days=history_days - 1)
    records = load_expense_records(db, user_id, history_start, history_end)
    series = build_daily_series(records, history_start, history_end)
    return ForecastReport(
        history_start=history_start, history_end=history_end,
        forecast_start=today, forecast_end=today + timedelta(days=horizon_days - 1),
        forecast=forecast_spending(series, window=window, horizon_days=horizon_days))


def summary(db: Session, user_id: int, period: str, ref: date) -> AnalysisSummary:
    report = report_service.comparison_report(db, user_id, period, ref)
    checks = check_budgets(db, user_id, ref)
    categories = report.current.by_category
    return AnalysisSummary(
        period=period, reference_date=ref, report=report,
        top_category=categories[0].category if categories else None,
        budget_checks=checks, alerts=build_alerts(checks))