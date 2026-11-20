from datetime import date
from decimal import Decimal

from app.services.receipt_parser import parse_receipt

TODAY = date(2026, 11, 13)


def test_english_receipt_all_fields():
    lines = ["Lotus's Express", "Tax Invoice", "Date: 12/11/2026 12:41", "Fried rice 60.00",
             "Subtotal 85.00", "VAT 7% 5.56", "TOTAL 1,085.00"]
    r = parse_receipt(lines, TODAY)
    assert r.merchant == "Lotus's Express"
    assert r.receipt_date == date(2026, 11, 12)
    assert r.total_amount == Decimal("1085.00")  # not the subtotal
    assert r.warnings == []


def test_thai_buddhist_year_and_total_keyword():
    r = parse_receipt(["ร้านข้าวมันไก่", "วันที่ 12/11/2569", "ยอดรวม 220"], TODAY)
    assert r.receipt_date == date(2026, 11, 12)  # 2569 BE -> 2026
    assert r.total_amount == Decimal("220")


def test_total_on_next_line():
    r = parse_receipt(["Cafe Amazon", "TOTAL", "145.00"], TODAY)
    assert r.total_amount == Decimal("145.00")


def test_fallback_to_largest_amount():
    r = parse_receipt(["Mini Mart", "Milk 25.00", "Bread 40.50"], TODAY)
    assert r.total_amount == Decimal("40.50")


def test_future_date_rejected_with_warning():
    r = parse_receipt(["Shop ABC", "01/01/2030", "TOTAL 10.00"], TODAY)
    assert r.receipt_date is None
    assert any("implausible" in w for w in r.warnings)


def test_unreadable_receipt_returns_warnings_not_crash():
    r = parse_receipt(["", "###", "~~"], TODAY)
    assert r.merchant is None and r.receipt_date is None and r.total_amount is None
    assert len(r.warnings) == 3
