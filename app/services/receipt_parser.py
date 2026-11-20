"""Pure text -> structured receipt fields. No OCR engine, no DB, no settings."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

# Amounts with exactly 2 decimals (used for the "largest amount" fallback)
_AMOUNT_2DP = re.compile(r"\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2}")
# Amounts on a "total" line may be integers too (e.g. "รวม 220")
_AMOUNT_ANY = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+(?:\.\d{2})?")

_STRONG_TOTAL = ("grand total", "net total", "total amount", "amount due", "net amount",
                 "ยอดสุทธิ", "ยอดรวม", "รวมทั้งสิ้น", "สุทธิ")
_WEAK_TOTAL = ("total", "รวม")
_NOT_TOTAL = ("subtotal", "sub total", "sub-total", "รวมย่อย", "change", "เงินทอน", "cash", "vat", "tax")

_DATE_YMD = re.compile(r"(?<!\d)(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)")
_DATE_DMY = re.compile(r"(?<!\d)(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})(?!\d)")

_MERCHANT_SKIP = ("receipt", "invoice", "tax", "tel", "phone", "date", "time", "cashier",
                  "ใบเสร็จ", "ใบกำกับ", "โทร", "วันที่", "welcome")


@dataclass
class ParsedReceipt:
    merchant: Optional[str] = None
    receipt_date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    warnings: list[str] = field(default_factory=list)


def _to_decimal(text: str) -> Optional[Decimal]:
    try:
        return Decimal(text.replace(",", ""))
    except InvalidOperation:
        return None


def parse_total(lines: list[str]) -> Optional[Decimal]:
    """Prefer an amount on a 'total' line (or the line after it); fall back to the largest amount."""
    for keywords in (_STRONG_TOTAL, _WEAK_TOTAL):
        for i, line in enumerate(lines):
            low = line.lower()
            if any(k in low for k in _NOT_TOTAL) or not any(k in low for k in keywords):
                continue
            # amount is usually right-aligned -> take the last one on the line
            found = _AMOUNT_ANY.findall(line)
            if not found and i + 1 < len(lines):
                found = _AMOUNT_ANY.findall(lines[i + 1])
            if found:
                value = _to_decimal(found[-1])
                if value is not None and value > 0:
                    return value
    values = [v for line in lines for m in _AMOUNT_2DP.findall(line) if (v := _to_decimal(m))]
    return max(values) if values else None


def _normalize_year(year: int) -> int:
    if year < 100:
        year += 2000
    if year > 2400:  # Buddhist Era (common on Thai receipts)
        year -= 543
    return year


def parse_date(lines: list[str], today: Optional[date] = None) -> tuple[Optional[date], list[str]]:
    """Return (date, warnings). Numeric dates are read day-first (dd/mm/yyyy) unless year comes first."""
    today = today or date.today()
    warnings: list[str] = []
    for line in lines:
        candidates: list[tuple[int, int, int]] = []
        for m in _DATE_YMD.finditer(line):
            candidates.append((int(m[1]), int(m[2]), int(m[3])))
        for m in _DATE_DMY.finditer(line):
            candidates.append((int(m[3]), int(m[2]), int(m[1])))
        for y, mo, d in candidates:
            try:
                found = date(_normalize_year(y), mo, d)
            except ValueError:
                continue
            if found.year < 2000 or found > today:
                warnings.append(f"Ignored implausible date {found.isoformat()}.")
                continue
            return found, warnings
    return None, warnings


def parse_merchant(lines: list[str]) -> Optional[str]:
    """Merchant name is normally one of the first lines and contains letters."""
    for line in lines[:6]:
        text = line.strip()
        low = text.lower()
        letters = sum(ch.isalpha() for ch in text)
        if len(text) < 3 or letters < 3 or letters < len(text) / 2:
            continue
        if any(k in low for k in _MERCHANT_SKIP):
            continue
        return text[:120]
    return None


def parse_receipt(lines: list[str], today: Optional[date] = None) -> ParsedReceipt:
    clean = [ln.strip() for ln in lines if ln and ln.strip()]
    result = ParsedReceipt()
    result.merchant = parse_merchant(clean)
    result.receipt_date, date_warnings = parse_date(clean, today)
    result.warnings.extend(date_warnings)
    result.total_amount = parse_total(clean)
    if result.merchant is None:
        result.warnings.append("Merchant name not found.")
    if result.receipt_date is None:
        result.warnings.append("Transaction date not found.")
    if result.total_amount is None:
        result.warnings.append("Total amount not found.")
    return result
