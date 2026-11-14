"""Small building blocks shared by all algorithms. Pure Python: no DB, no FastAPI."""
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

ZERO = Decimal("0")
CENT = Decimal("0.01")


def money(value: Decimal | int | str) -> Decimal:
    """Round to 2 decimal places (satang) using the usual 'half up' rule."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def total(amounts: Iterable[Decimal]) -> Decimal:
    return sum(amounts, ZERO)


def percent(part: Decimal, whole: Decimal) -> Decimal | None:
    """part / whole * 100, rounded to 2 places. Returns None when whole is 0
    (the percentage is undefined) instead of raising ZeroDivisionError."""
    if whole == 0:
        return None
    return money(part / whole * 100)


@dataclass(frozen=True)
class ExpenseRecord:
    """Minimal expense the algorithms need. Services convert DB rows into these,
    so algorithms never depend on SQLAlchemy."""
    amount: Decimal
    category: str
    expense_date: date
    id: int | None = None