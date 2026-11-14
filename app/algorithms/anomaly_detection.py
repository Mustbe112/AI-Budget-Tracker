"""Algorithm 2: IQR anomaly detection, per category.

    Q1, Q3     = 25th and 75th percentiles (linear interpolation)
    IQR        = Q3 - Q1
    upper bound = Q3 + 1.5 * IQR
    An expense is flagged when amount > upper bound.

Flagging only means "worth a look". Nothing is ever deleted or rejected.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Iterable

from app.algorithms.common import ExpenseRecord, money

ANALYZED = "analyzed"
INSUFFICIENT_DATA = "insufficient_data"
NO_VARIATION = "no_variation"

DEFAULT_MIN_SAMPLES = 8
DEFAULT_MULTIPLIER = Decimal("1.5")


@dataclass(frozen=True)
class Anomaly:
    expense_id: int | None
    category: str
    amount: Decimal
    expense_date: date
    upper_bound: Decimal
    excess_over_bound: Decimal


@dataclass(frozen=True)
class CategoryAnomalyResult:
    category: str
    status: str                       # analyzed | insufficient_data | no_variation
    sample_count: int
    q1: Decimal | None = None
    q3: Decimal | None = None
    iqr: Decimal | None = None
    upper_bound: Decimal | None = None
    anomalies: list[Anomaly] = field(default_factory=list)
    message: str = ""


def quartile(sorted_values: list[Decimal], q: Decimal) -> Decimal:
    """Percentile by linear interpolation (same as numpy's default).
    `sorted_values` must be sorted ascending and non-empty; q is 0..1."""
    position = (len(sorted_values) - 1) * q
    lower = int(position)                       # index just below the position
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


def detect_anomalies(
    expenses: Iterable[ExpenseRecord],
    min_samples: int = DEFAULT_MIN_SAMPLES,
    multiplier: Decimal = DEFAULT_MULTIPLIER,
) -> list[CategoryAnomalyResult]:
    """Run the IQR test separately for every category."""
    by_category: dict[str, list[ExpenseRecord]] = {}
    for e in expenses:
        by_category.setdefault(e.category, []).append(e)

    results: list[CategoryAnomalyResult] = []
    for category in sorted(by_category):
        items = by_category[category]
        n = len(items)

        # Too little history makes quartiles meaningless, so don't guess.
        if n < min_samples:
            results.append(CategoryAnomalyResult(
                category=category, status=INSUFFICIENT_DATA, sample_count=n,
                message=f"Need at least {min_samples} expenses in '{category}' "
                        f"to detect unusual spending; found {n}.",
            ))
            continue

        values = sorted(e.amount for e in items)                 # step 1: sort
        q1 = quartile(values, Decimal("0.25"))                   # step 2: quartiles
        q3 = quartile(values, Decimal("0.75"))
        iqr = q3 - q1                                            # step 3: spread
        upper_bound = q3 + multiplier * iqr                      # step 4: fence

        if iqr == 0:
            # Every typical expense is identical, so any difference would look
            # "unusual". Refuse to flag rather than produce noise.
            results.append(CategoryAnomalyResult(
                category=category, status=NO_VARIATION, sample_count=n,
                q1=money(q1), q3=money(q3), iqr=money(iqr),
                upper_bound=money(upper_bound),
                message=f"Spending in '{category}' has almost no variation, "
                        "so unusual expenses cannot be identified.",
            ))
            continue

        flagged = [                                              # step 5: compare
            Anomaly(
                expense_id=e.id, category=category, amount=money(e.amount),
                expense_date=e.expense_date, upper_bound=money(upper_bound),
                excess_over_bound=money(e.amount - upper_bound),
            )
            for e in sorted(items, key=lambda x: (x.expense_date, x.id or 0))
            if e.amount > upper_bound
        ]
        results.append(CategoryAnomalyResult(
            category=category, status=ANALYZED, sample_count=n,
            q1=money(q1), q3=money(q3), iqr=money(iqr),
            upper_bound=money(upper_bound), anomalies=flagged,
            message=f"{len(flagged)} unusually high expense(s) found."
                    if flagged else "No unusual expenses found.",
        ))
    return results