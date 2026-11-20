import pytest
from types import SimpleNamespace
from app.core.config import settings
from app.services import receipt_storage as st

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


@pytest.fixture(autouse=True)
def _upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "get_settings",
    lambda: SimpleNamespace(upload_dir=str(tmp_path), max_upload_bytes=1024))


def test_save_and_resolve():
    rid, size = st.save_receipt(1, JPEG, "image/jpeg")
    assert rid.endswith(".jpg") and size == len(JPEG)
    assert st.resolve_receipt_path(1, rid).is_file()


def test_rejects_wrong_type_empty_and_spoofed():
    with pytest.raises(st.ReceiptFileError): st.save_receipt(1, JPEG, "application/pdf")
    with pytest.raises(st.ReceiptFileError): st.save_receipt(1, b"", "image/png")
    with pytest.raises(st.ReceiptFileError): st.save_receipt(1, b"<?php evil ?>", "image/png")


def test_rejects_oversized():
    with pytest.raises(st.ReceiptFileError):
        st.save_receipt(1, PNG + b"0" * 2000, "image/png")


def test_user_cannot_access_other_users_receipt():
    rid, _ = st.save_receipt(1, PNG, "image/png")
    with pytest.raises(st.ReceiptNotFoundError):
        st.resolve_receipt_path(2, rid)


def test_path_traversal_blocked():
    with pytest.raises(st.ReceiptNotFoundError):
        st.resolve_receipt_path(1, "../../etc/passwd")
