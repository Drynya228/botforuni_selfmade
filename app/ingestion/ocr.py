# app/ingestion/ocr.py
import os
from PIL import Image
import pytesseract

OCR_ENABLED = (os.getenv("OCR_ENABLED", "true").lower() == "true")

async def ocr_photo(path: str) -> str:
    if not OCR_ENABLED:
        return ""
    try:
        img = Image.open(path)
        return pytesseract.image_to_string(img, lang="rus+eng").strip()
    except Exception:
        return ""
