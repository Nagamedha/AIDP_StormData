from pathlib import Path
from pdf2image import convert_from_path
from PIL import ImageOps
import pytesseract

from src.utils.logger import get_logger
from src.utils.file_handler import move_to_error
from src.utils.config import LOCAL_RAW_PATH

log = get_logger("selector")

HEADER_KEYWORDS = [
    "location", "place", "date", "time", "path", "mile", "yard",
    "killed", "injured", "damage", "property", "crops",
    "character", "character of storm", "storm data"
]

THRESHOLD = 6

def ocr_text(image):
    gray = ImageOps.grayscale(image)
    return pytesseract.image_to_string(gray).lower()

def score_page(text):
    hits = [kw for kw in HEADER_KEYWORDS if kw in text]
    return len(hits), hits

def process_pdf_folder(folder: Path):
    page_files = sorted(folder.glob("*.pdf"))
    log.info(f"🔍 Selecting pages for PDF: {folder.name}")

    for page_pdf in page_files:
        try:
            images = convert_from_path(str(page_pdf), dpi=200)
            img = images[0]

            text = ocr_text(img)
            score, hits = score_page(text)

            log.info(f"📄 {page_pdf.name} → HITS={score} → {hits}")

            if score >= THRESHOLD:
                log.info(f"✅ KEEP: {page_pdf.name}")
            else:
                log.info(f"❌ DISCARD: {page_pdf.name}")
                move_to_error(page_pdf)

        except Exception as e:
            log.error(f"❌ Error processing {page_pdf.name}: {e}")
            move_to_error(page_pdf)

def run_selector():
    raw_dir = Path(LOCAL_RAW_PATH)

    for folder in raw_dir.iterdir():
        if folder.is_dir():
            process_pdf_folder(folder)

    log.info("✅ Page selection completed")
