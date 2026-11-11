from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.algorithms.spending_analysis import CategoryTotal, PeriodComparison, PeriodSummary
from app.database.enums import BudgetPeriod


class SpendingReport(BaseModel):
    """Daily / weekly / monthly report."""
    period: BudgetPeriod
    reference_date: date
    summary: PeriodSummary
    income_total: Decimal       # income received in the same window
    net: Decimal                # income_total - total spending (negative = deficit)


class CategoryReport(BaseModel):
    start_date: date
    end_date: date
    total_spending: Decimal
    categories: list[CategoryTotal]


class ComparisonReport(BaseModel):
    period: BudgetPeriod
    reference_date: date
    current: PeriodSummary
    previous: PeriodSummary
    comparison: PeriodComparison