from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator

from app.database.enums import BudgetPeriod, Category
from app.schemas.common import Money


class BudgetCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    category: Category | None = None  # null = overall budget across all categories
    amount: Money
    period: BudgetPeriod
    start_date: date
    end_date: date | None = None      # null = open-ended

    @model_validator(mode="after")
    def end_not_before_start(self) -> "BudgetCreate":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class BudgetUpdate(BudgetCreate):
    """PUT replaces the whole record."""


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: Category | None
    amount: Decimal
    period: BudgetPeriod
    start_date: date
    end_date: date | None