from PIL import Image
import pytesseract
from app.core.config import cfg

async def ocr_photo(path: str) -> str:
    if not cfg.OCR_ENABLED:
        return ""
    img = Image.open(path)
    return pytesseract.image_to_string(img, lang="rus+eng").strip()