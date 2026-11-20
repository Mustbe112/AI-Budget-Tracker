from decimal import Decimal
from typing import Annotated

from pydantic import Field

# Positive money with max 2 decimals and 12 digits total (matches NUMERIC(12,2)).
Money = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]