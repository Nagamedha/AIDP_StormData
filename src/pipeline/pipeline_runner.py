# src/pipeline/pipeline_runner.py
"""
Pipeline Runner for AIDP_StormData

Current Stage (No Gemini yet):
--------------------------------
1. Read PDFs from data/input/
2. Split multi-page PDF → single pages under data/raw/<doc_name>/
3. OCR each page
4. Score based on NOAA table headers
5. KEEP pages with score >= THRESHOLD in raw/
6. MOVE bad pages to data/error/<doc_name>/
7. (Optional) Save OCR debug text under logs/ocr_text/<doc_name>/
8. Move original PDF → data/archived_input/

This prepares clean pages for tomorrow's Gemini extraction.
"""
from src.utils.config import SAVE_OCR_DEBUG_TEXT
from pathlib import Path
from typing import List, Tuple

from pdf2image import convert_from_path
from PIL import ImageOps
import pytesseract

from src.utils.logger import get_logger
from src.utils.config import (
    LOCAL_INPUT_PATH,
    LOCAL_RAW_PATH,
    LOCAL_ERROR_PATH,
    SAVE_OCR_DEBUG_TEXT,
)

from src.ingestion.page_splitter import split_pdf_to_pages

logger = get_logger("pipeline_runner")

# --------------------------------------
# CONFIG FLAGS for ocr debug text saving
# --------------------------------------
#SAVE_OCR_DEBUG_TEXT = False  # ← set False to stop saving OCR text files


# --------------------------------------
# NOAA KEYWORDS FOR PAGE SCORING
# --------------------------------------
HEADER_FIELDS = [
    "location",
    "place",
    "date",
    "time",
    "path",
    "mile",
    "yard",
    "killed",
    "injured",
    "damage",
    "property",
    "crops",
    "character",
    "character of storm",
    "storm data",
]

THRESHOLD = 6  # minimum hits required for keeping page


# --------------------------------------
# FOLDER PATHS
# --------------------------------------
ARCHIVE_INPUT_PATH = Path("data/archived_input")


# --------------------------------------
# OCR HELPERS
# --------------------------------------
def ocr_page_pdf(page_pdf: Path) -> str:
    """OCR a single-page PDF → return text."""
    try:
        images = convert_from_path(str(page_pdf), dpi=200)
        if not images:
            logger.warning(f"⚠️ No image rendered for {page_pdf.name}")
            return ""

        img = images[0]
        gray = ImageOps.grayscale(img)
        text = pytesseract.image_to_string(gray)
        return text.lower()

    except Exception as e:
        logger.error(f"❌ OCR error for {page_pdf.name}: {e}")
        return ""


def score_ocr_text(text: str) -> Tuple[int, List[str]]:
    """Return (#hits, [matched_keywords])."""
    hits = [h for h in HEADER_FIELDS if h in text]
    return len(hits), hits


# --------------------------------------
# PROCESS ONE PDF
# --------------------------------------
def process_single_pdf(pdf_path: Path) -> None:
    logger.info("===================================================")
    logger.info(f"➡️ Starting processing for: {pdf_path.name}")
    logger.info("===================================================")

    raw_root = Path(LOCAL_RAW_PATH)
    error_root = Path(LOCAL_ERROR_PATH)

    raw_subdir = raw_root / pdf_path.stem.replace(" ", "_").lower()
    error_subdir = error_root / pdf_path.stem.replace(" ", "_").lower()
    ocr_text_dir = Path("logs/ocr_text") / pdf_path.stem.replace(" ", "_").lower()

    raw_subdir.mkdir(parents=True, exist_ok=True)
    error_subdir.mkdir(parents=True, exist_ok=True)
    ocr_text_dir.mkdir(parents=True, exist_ok=True)
    ARCHIVE_INPUT_PATH.mkdir(parents=True, exist_ok=True)

    # --------------------------
    # 1. Split file into pages
    # --------------------------
    page_count = split_pdf_to_pages(pdf_path, raw_subdir)
    if page_count == 0:
        logger.error(f"❌ Skipping {pdf_path.name}: splitting failed or no pages.")
        return

    kept = 0
    discarded = 0

    # --------------------------
    # 2. Score each page
    # --------------------------
    page_pdfs = sorted(raw_subdir.glob("*.pdf"))
    for page_pdf in page_pdfs:
        logger.info("\n----------------------------------------")
        logger.info(f"➡️ Evaluating page: {page_pdf.name}")

        text = ocr_page_pdf(page_pdf)

        if not text.strip():
            logger.warning(f"⚠️ Empty OCR text for {page_pdf.name}, moving to error.")
            page_pdf.rename(error_subdir / page_pdf.name)
            discarded += 1
            continue

        score, hits = score_ocr_text(text)
        logger.info(f"🔹 OCR HEADER HITS ({score}): {hits}")

        # --------------------------
        # KEEP PAGE
        # --------------------------
        if score >= THRESHOLD:
            kept += 1

            # Optional debug storage
            if SAVE_OCR_DEBUG_TEXT:
                txt_out = ocr_text_dir / f"{page_pdf.stem}.txt"
                try:
                    with open(txt_out, "w", encoding="utf-8") as f:
                        f.write(text)
                    logger.info(f"💾 OCR debug saved → {txt_out}")
                except Exception as e:
                    logger.error(f"❌ Failed to save OCR text: {e}")

            logger.info("✅ KEEP PAGE (remains in raw/)")

        # --------------------------
        # DISCARD PAGE
        # --------------------------
        else:
            discarded += 1
            target = error_subdir / page_pdf.name
            try:
                page_pdf.rename(target)
                logger.info(f"⏭ SKIP PAGE → moved to error/{page_pdf.name}")
            except Exception as e:
                logger.error(f"❌ Failed to move page to error folder: {e}")

    logger.info("\n----------------------------------------")
    logger.info(f"📊 Summary for {pdf_path.name}: kept={kept}, discarded={discarded}")

    # --------------------------
    # 3. Archive original PDF
    # --------------------------
    try:
        archived_target = ARCHIVE_INPUT_PATH / pdf_path.name
        pdf_path.rename(archived_target)
        logger.info(f"📦 Archived original PDF → {archived_target}")
    except Exception as e:
        logger.error(f"❌ Failed to archive {pdf_path.name}: {e}")


# --------------------------------------
# PIPELINE ENTRYPOINT
# --------------------------------------
def run_pipeline() -> None:
    input_dir = Path(LOCAL_INPUT_PATH)
    input_dir.mkdir(parents=True, exist_ok=True)

    logger.info("🚀 AIDP_StormData Pipeline Run Started")
    logger.info(f"📂 Looking for PDFs in input folder: {input_dir}")

    pdfs = sorted(input_dir.glob("*.pdf"))
    if not pdfs:
        logger.info("⚠️ No PDFs found. Nothing to process.")
        logger.info("🏁 Pipeline finished.")
        return

    logger.info(f"📌 Found {len(pdfs)} PDF(s): {[p.name for p in pdfs]}")

    for pdf_path in pdfs:
        try:
            process_single_pdf(pdf_path)
        except Exception as e:
            logger.error(f"❌ Unexpected error while processing {pdf_path.name}: {e}")

    logger.info("🏁 Pipeline run completed.")

