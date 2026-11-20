from typing import Literal

from pydantic import BaseModel


class Alert(BaseModel):
    level: Literal["exceeded", "warning"]
    budget_id: int
    category: str | None
    period: str
    message: str