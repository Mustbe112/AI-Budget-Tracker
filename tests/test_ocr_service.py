from pathlib import Path

import pytest

from app.services.ocr_service import MockOCRProvider, OCRService, OCRUnavailableError


class _Broken:
    name = "broken"
    def read_lines(self, p): raise RuntimeError("corrupt image")

class _Empty:
    name = "empty"
    def read_lines(self, p): return []

class _Missing:
    name = "missing"
    def read_lines(self, p): raise OCRUnavailableError("not installed")


def test_mock_provider_returns_complete_draft():
    r = OCRService(MockOCRProvider()).extract(Path("x.jpg"))
    assert r.status == "ok" and r.requires_confirmation is True and r.confidence == 1.0


def test_corrupt_image_gives_failed_draft():
    r = OCRService(_Broken()).extract(Path("x.jpg"))
    assert r.status == "failed" and r.warnings


def test_no_text_gives_failed_draft():
    assert OCRService(_Empty()).extract(Path("x.jpg")).status == "failed"


def test_engine_missing_raises_unavailable():
    with pytest.raises(OCRUnavailableError):
        OCRService(_Missing()).extract(Path("x.jpg"))
