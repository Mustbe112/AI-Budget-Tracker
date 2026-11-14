from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.database.enums import Category
from app.schemas.common import Money


class ExpenseCreate(BaseModel):
    # use_enum_values: store plain strings, so SQLAlchemy/psycopg2 get simple str values.
    model_config = ConfigDict(use_enum_values=True, str_strip_whitespace=True)

    category: Category
    amount: Money
    description: str | None = Field(default=None, max_length=500)
    merchant: str | None = Field(default=None, max_length=120)
    expense_date: date


class ExpenseUpdate(ExpenseCreate):
    """PUT replaces the whole record, so it takes the same fields as POST."""


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: Category
    amount: Decimal  # serialized as a string, e.g. "220.50"
    description: str | None
    merchant: str | None
    expense_date: date
    created_at: datetime


class ExpenseList(BaseModel):
    items: list[ExpenseRead]
    total: int             # records matching the filters (ignores limit/offset)
    total_amount: Decimal  # sum of all records matching the filters
    limit: int
    offset: int