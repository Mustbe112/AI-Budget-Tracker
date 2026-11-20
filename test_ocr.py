from pathlib import Path
from app.services.ocr_service import OCRService, PaddleOCRProvider

result = OCRService(PaddleOCRProvider()).extract(Path("sample_receipt_2.png"))
print(result.model_dump_json(indent=2))