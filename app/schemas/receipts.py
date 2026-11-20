"""Pydantic schemas for the receipt (OCR) workflow."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.database.enums import Category
from app.schemas.common import Money


class ReceiptUploadResponse(BaseModel):
    receipt_id: str = Field(description="Opaque ID used in /receipts/extract and /receipts/confirm")
    size_bytes: int
    content_type: str


class ReceiptExtractRequest(BaseModel):
    receipt_id: str


class ReceiptExtraction(BaseModel):
    """OCR draft. It is NOT an expense until the user confirms it."""

    status: Literal["ok", "partial", "failed"]
    merchant: Optional[str] = None
    transaction_date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    confidence: float = Field(ge=0, le=1, description="Share of fields found (completeness, not model accuracy)")
    warnings: list[str] = []
    raw_lines: list[str] = []
    provider: str
    requires_confirmation: bool = True


class ReceiptConfirmRequest(BaseModel):
    """What the user reviewed/corrected in the UI. Same rules as POST /expenses."""

    model_config = ConfigDict(str_strip_whitespace=True)

    receipt_id: Optional[str] = None
    category: Category
    amount: Money
    merchant: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    expense_date: date