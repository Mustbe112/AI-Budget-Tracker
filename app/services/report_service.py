"""Spending reports: loads data, calls the algorithms, never calculates itself."""
from datetime import date

from sqlalchemy.orm import Session

from app.algorithms.common import money
from app.algorithms.spending_analysis import compare_periods, summarize_period
from app.schemas.report import CategoryReport, ComparisonReport, SpendingReport
from app.services import income_service
from app.services.budget_check_service import overall_budget_amount
from app.services.records import load_expense_records
from app.utils.dates import period_window, previous_window


def spending_report(db: Session, user_id: int, period: str, ref: date) -> SpendingReport:
    start, end = period_window(period, ref)
    records = load_expense_records(db, user_id, start, end)
    budget = overall_budget_amount(db, user_id, period, ref)   # for utilisation %
    summary = summarize_period(records, start, end, budget)
    income = income_service.total_income(db, user_id, start, end)
    return SpendingReport(
        period=period, reference_date=ref, summary=summary,
        income_total=income, net=money(income - summary.total_spending))


def category_report(db: Session, user_id: int, start: date, end: date) -> CategoryReport:
    summary = summarize_period(load_expense_records(db, user_id, start, end), start, end)
    return CategoryReport(start_date=start, end_date=end,
                          total_spending=summary.total_spending,
                          categories=summary.by_category)


def comparison_report(db: Session, user_id: int, period: str, ref: date) -> ComparisonReport:
    """Whole current period vs the whole previous period (same period type)."""
    cur_start, cur_end = period_window(period, ref)
    prev_start, prev_end = previous_window(period, ref)
    records = load_expense_records(db, user_id, prev_start, cur_end)  # one query
    budget = overall_budget_amount(db, user_id, period, ref)
    current = summarize_period(records, cur_start, cur_end, budget)
    previous = summarize_period(records, prev_start, prev_end)
    return ComparisonReport(period=period, reference_date=ref, current=current,
                            previous=previous, comparison=compare_periods(previous, current))