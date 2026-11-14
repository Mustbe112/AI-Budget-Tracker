"""Receipt workflow: upload -> extract (draft) -> user reviews -> confirm (only then an expense exists)."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import CurrentUser
from app.database.connection import get_db
from app.schemas.expense import ExpenseCreate, ExpenseRead
from app.schemas.receipts import (ReceiptConfirmRequest, ReceiptExtraction, ReceiptExtractRequest,
                                  ReceiptUploadResponse)
from app.services import expense_service
from app.services import receipt_storage as storage
from app.services.ocr_service import OCRService, OCRUnavailableError, get_ocr_service

router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.post("/upload", response_model=ReceiptUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(user: CurrentUser, file: UploadFile = File(...)):
    limit = get_settings().max_upload_bytes
    data = await file.read(limit + 1)  # read at most limit+1 bytes: never load a huge file
    try:
        receipt_id, size = storage.save_receipt(user.id, data, file.content_type)
    except storage.ReceiptFileError as exc:
        code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if "larger" in str(exc) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(code, str(exc))
    return ReceiptUploadResponse(receipt_id=receipt_id, size_bytes=size, content_type=file.content_type)


@router.post("/extract", response_model=ReceiptExtraction)
def extract_receipt(body: ReceiptExtractRequest, user: CurrentUser,
                    ocr: OCRService = Depends(get_ocr_service)):
    """Returns a DRAFT only. Nothing is written to the expenses table here."""
    try:
        path = storage.resolve_receipt_path(user.id, body.receipt_id)
    except storage.ReceiptNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receipt not found.")
    try:
        return ocr.extract(path)
    except OCRUnavailableError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Receipt scanning is unavailable. Please enter the expense manually.")


@router.post("/confirm", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def confirm_receipt(body: ReceiptConfirmRequest, user: CurrentUser, db: Session = Depends(get_db)):
    """Saves the values the USER reviewed (not the raw OCR output) through the normal expense service."""
    if body.receipt_id:
        try:
            storage.resolve_receipt_path(user.id, body.receipt_id)  # must belong to this user
        except storage.ReceiptNotFoundError:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Receipt not found.")
    data = ExpenseCreate(category=body.category, amount=body.amount, description=body.description,
                         merchant=body.merchant, expense_date=body.expense_date)
    expense = expense_service.create_expense(db, user.id, data)
    if body.receipt_id:
        storage.delete_receipt(user.id, body.receipt_id)  # image no longer needed once confirmed
    return expense