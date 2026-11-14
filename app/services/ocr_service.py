"""OCR service. Kept separate from expense/budget logic: it only turns an image into a DRAFT."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Protocol

from app.core.config import get_settings
from app.schemas.receipts import ReceiptExtraction
from app.services.receipt_parser import parse_receipt

logger = logging.getLogger(__name__)


class OCRUnavailableError(Exception):
    """OCR engine is not installed / not configured."""


class OCRProvider(Protocol):
    name: str

    def read_lines(self, image_path: Path) -> list[str]:
        """Return recognised text lines, top to bottom."""
        ...


class MockOCRProvider:
    """Deterministic provider so the API works without PaddleOCR (dev, tests, demos)."""

    name = "mock"

    def read_lines(self, image_path: Path) -> list[str]:
        return ["Lotus's Express", "Tax Invoice", "Date: 12/11/2026 12:41",
                "Fried rice            60.00", "Iced tea              25.00",
                "Subtotal              85.00", "VAT 7%                5.56", "TOTAL                 85.00"]


class PaddleOCRProvider:
    """PaddleOCR wrapper. The engine is created lazily (slow to import, downloads models once)."""

    name = "paddleocr"

    def __init__(self, lang: str = "en") -> None:
        self._lang = lang
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            try:
                from paddleocr import PaddleOCR  # imported here so the backend runs without it
            except ImportError as exc:
                raise OCRUnavailableError("PaddleOCR is not installed.") from exc
            try:
                try:  # PaddleOCR 3.x: skip heavy document pre-processing models (faster for receipts)
                    self._engine = PaddleOCR(
                        lang=self._lang,
                        use_doc_orientation_classify=False,
                        use_doc_unwarping=False,
                        use_textline_orientation=False,
                        enable_mkldnn=False,  # avoids the oneDNN crash on Windows CPUs
                    )
                except Exception:  # PaddleOCR 2.x does not know these options
                    self._engine = PaddleOCR(lang=self._lang, enable_mkldnn=False)
            except Exception as exc:
                logger.exception("PaddleOCR failed to start")
                raise OCRUnavailableError("PaddleOCR could not start.") from exc
        return self._engine

    def read_lines(self, image_path: Path) -> list[str]:
        result = self._get_engine().ocr(str(image_path)) or []
        lines: list[str] = []
        for page in result:
            if isinstance(page, dict):  # PaddleOCR 3.x: {"rec_texts": [...], ...}
                lines.extend(str(t) for t in page.get("rec_texts", []))
            else:  # PaddleOCR 2.x: [[box, (text, score)], ...]
                lines.extend(str(item[1][0]) for item in page or [])
        return lines


class OCRService:
    def __init__(self, provider: OCRProvider) -> None:
        self.provider = provider

    def extract(self, image_path: Path) -> ReceiptExtraction:
        try:
            lines = self.provider.read_lines(image_path)
        except OCRUnavailableError:
            raise
        except Exception:  # unreadable/corrupt image etc. -> graceful "failed" draft
            logger.exception("OCR failed for %s", image_path.name)
            return ReceiptExtraction(status="failed", confidence=0.0, provider=self.provider.name,
                                     warnings=["The receipt could not be read. Please enter it manually."])
        if not lines:
            return ReceiptExtraction(status="failed", confidence=0.0, provider=self.provider.name,
                                     warnings=["No text detected. Try a sharper, well-lit photo."])

        parsed = parse_receipt(lines)
        found = sum(x is not None for x in (parsed.merchant, parsed.receipt_date, parsed.total_amount))
        status = "ok" if found == 3 else "partial" if found else "failed"
        return ReceiptExtraction(
            status=status, merchant=parsed.merchant, transaction_date=parsed.receipt_date,
            total_amount=parsed.total_amount, confidence=round(found / 3, 2),
            warnings=parsed.warnings, raw_lines=lines, provider=self.provider.name,
        )


_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """One shared service so PaddleOCR models load only once."""
    global _service
    wanted = "paddleocr" if get_settings().ocr_provider == "paddle" else "mock"
    if _service is None or _service.provider.name != wanted:
        _service = OCRService(PaddleOCRProvider() if wanted == "paddleocr" else MockOCRProvider())
    return _service