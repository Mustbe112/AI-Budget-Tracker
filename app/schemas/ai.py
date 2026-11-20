"""Pydantic schemas for the AI endpoints (Step 7)."""
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


class CategoryTotal(BaseModel):
    category: str
    total: Decimal


class BudgetFact(BaseModel):
    """One budget with numbers calculated by Python (never by the LLM)."""
    category: Optional[str] = None          # None = overall budget
    period: Literal["daily", "weekly", "monthly"]
    budget: Decimal
    spent: Decimal
    remaining: Decimal                      # negative when exceeded
    status: Literal["within", "near_limit", "exceeded"]


class FinancialContext(BaseModel):
    """Verified, aggregated facts. This is the ONLY data the LLM sees.
    No email, username, merchant names or free-text descriptions."""
    currency: str = "THB"
    period_start: date
    period_end: date
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal
    category_totals: list[CategoryTotal]
    budgets: list[BudgetFact]


class RecommendationRequest(BaseModel):
    days: int = Field(30, ge=1, le=365, description="Look-back window in days")
    focus_category: Optional[str] = Field(None, max_length=50)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    days: int = Field(30, ge=1, le=365)


class AIResponse(BaseModel):
    text: str
    ai_generated: bool = Field(description="False when the rule-based fallback was used")
    provider: str
    disclaimer: str
    facts: FinancialContext


class AIStatus(BaseModel):
    provider: str
    enabled: bool
