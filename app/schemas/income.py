from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Money


class IncomeCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    amount: Money
    source: str = Field(min_length=1, max_length=100)   # e.g. "Salary", "Freelance"
    income_date: date


class IncomeUpdate(IncomeCreate):
    """PUT replaces the whole record."""


class IncomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    source: str
    income_date: date
    created_at: datetime


class IncomeList(BaseModel):
    items: list[IncomeRead]
    total: int
    total_amount: Decimal
    limit: int
    offset: int