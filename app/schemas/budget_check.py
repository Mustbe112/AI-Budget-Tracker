from datetime import date

from pydantic import BaseModel

from app.algorithms.budget_calculator import BudgetStatus
from app.schemas.alert import Alert


class BudgetCheckItem(BaseModel):
    budget_id: int
    status: BudgetStatus


class BudgetCheckResponse(BaseModel):
    reference_date: date
    items: list[BudgetCheckItem]
    alerts: list[Alert]