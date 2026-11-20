"""Validated receipt image storage, one folder per user (so users can't reach each other's files)."""
from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_RECEIPT_ID_RE = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp)$")  # blocks path traversal


class ReceiptFileError(ValueError):
    """Invalid upload (type, size, empty, spoofed)."""


class ReceiptNotFoundError(LookupError):
    pass


def detect_image_type(data: bytes) -> Optional[str]:
    """Identify the real format from magic bytes; the client-sent filename/type is not trusted."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _user_dir(user_id: object) -> Path:
    return Path(get_settings().upload_dir) / str(user_id)


def save_receipt(user_id: object, data: bytes, content_type: Optional[str]) -> tuple[str, int]:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ReceiptFileError("Only JPEG, PNG or WebP images are allowed.")
    if not data:
        raise ReceiptFileError("The uploaded file is empty.")
    limit = get_settings().max_upload_bytes
    if len(data) > limit:
        raise ReceiptFileError(f"File is larger than {limit // (1024 * 1024)} MB.")
    ext = detect_image_type(data)
    if ext is None:
        raise ReceiptFileError("File content is not a valid JPEG, PNG or WebP image.")
    receipt_id = f"{uuid.uuid4().hex}.{ext}"
    folder = _user_dir(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / receipt_id).write_bytes(data)
    return receipt_id, len(data)


def resolve_receipt_path(user_id: object, receipt_id: str) -> Path:
    if not _RECEIPT_ID_RE.match(receipt_id):
        raise ReceiptNotFoundError("Receipt not found.")
    path = _user_dir(user_id) / receipt_id
    if not path.is_file():
        raise ReceiptNotFoundError("Receipt not found.")
    return path


def delete_receipt(user_id: object, receipt_id: str) -> None:
    try:
        resolve_receipt_path(user_id, receipt_id).unlink(missing_ok=True)
    except ReceiptNotFoundError:
        pass