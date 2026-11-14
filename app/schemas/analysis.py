from datetime import date

from pydantic import BaseModel

from app.algorithms.anomaly_detection import CategoryAnomalyResult
from app.algorithms.spending_forecast import ForecastResult
from app.database.enums import BudgetPeriod
from app.schemas.alert import Alert
from app.schemas.budget_check import BudgetCheckItem
from app.schemas.report import ComparisonReport


class OverspendingReport(BaseModel):
    reference_date: date
    exceeded_count: int
    items: list[BudgetCheckItem]
    alerts: list[Alert]


class AnomalyReport(BaseModel):
    lookback_start: date
    lookback_end: date
    min_samples: int
    total_anomalies: int
    categories: list[CategoryAnomalyResult]
    note: str = ("Unusual means 'higher than your typical spending in that category'. "
                 "It does not mean the expense is wrong.")


class ForecastReport(BaseModel):
    history_start: date
    history_end: date          # last COMPLETED day (yesterday)
    forecast_start: date       # today
    forecast_end: date
    forecast: ForecastResult


class AnalysisSummary(BaseModel):
    """Everything the dashboard and the AI service need, computed in Python."""
    period: BudgetPeriod
    reference_date: date
    report: ComparisonReport
    top_category: str | None
    budget_checks: list[BudgetCheckItem]
    alerts: list[Alert]