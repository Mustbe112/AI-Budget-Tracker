"""Turns verified budget results into human-readable alerts.
Pure text formatting over numbers Python already calculated."""
from app.algorithms.budget_calculator import EXCEEDED, NEAR_LIMIT
from app.core.config import settings
from app.schemas.alert import Alert
from app.schemas.budget_check import BudgetCheckItem


def build_alerts(items: list[BudgetCheckItem]) -> list[Alert]:
    sym = settings.currency_symbol
    alerts: list[Alert] = []
    for item in items:
        s = item.status
        label = f"{s.period} {s.category or 'overall'} budget"
        if s.status == EXCEEDED:
            alerts.append(Alert(
                level="exceeded", budget_id=item.budget_id, category=s.category,
                period=s.period,
                message=f"You exceeded your {label} by {sym}{s.overspent_amount:,.2f}."))
        elif s.status == NEAR_LIMIT:
            alerts.append(Alert(
                level="warning", budget_id=item.budget_id, category=s.category,
                period=s.period,
                message=f"You have used {s.utilization_percent}% of your {label} "
                        f"({sym}{s.remaining:,.2f} remaining)."))
    alerts.sort(key=lambda a: a.level != "exceeded")   # exceeded first
    return alerts