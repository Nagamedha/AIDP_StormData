# src/extraction/gemini_extractor.py
"""
Final Gemini Extractor With Safe Continuation Detection
-------------------------------------------------------
- OCRs pages in sorted order for each document folder
- Detects if a page is continuation of previous page using heuristics
- Inserts markers to help Gemini merge multi-page rows
- Calls Gemini (your model), with retry + skip safe mode
- Produces ONE JSON per document (folder)
- Moves raw folder → archived_raw
"""

import os, io, json, time, shutil, requests
from pathlib import Path
from typing import Dict, Any, List
from pdf2image import convert_from_path
from PIL import Image, ImageOps, ImageFilter
import pytesseract

from src.utils.logger import get_logger
from src.utils.config import GEMINI_API_KEY, LOCAL_RAW_PATH, LOCAL_PROCESSED_PATH

log = get_logger("gemini_extractor")

MODEL_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash-lite:generateContent"
)

# ============================================================
# OCR PREPROCESSING
# ============================================================

def preprocess_image(img):
    gray = ImageOps.grayscale(img)
    sharpened = gray.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=2))
    bw = sharpened.point(lambda x: 255 if x > 185 else 0)
    return bw

def ocr_page(pdf_path: Path) -> str:
    """Extracts OCR text from a single-page PDF."""
    try:
        images = convert_from_path(str(pdf_path), dpi=300)
        if not images:
            return ""
        processed = preprocess_image(images[0])
        return pytesseract.image_to_string(processed, config="--oem 1 --psm 6")
    except Exception as e:
        log.error(f"OCR failed for {pdf_path.name}: {e}")
        return ""


# ============================================================
# CONTINUATION HEURISTICS
# ============================================================

HEADER_KEYWORDS = [
    "location", "place", "date", "time", "path",
    "mile", "yard", "killed", "injured",
    "damage", "property", "crops", "character"
]

def is_continuation(curr_text: str, prev_text: str) -> bool:
    """
    Detect if current page is continuation of previous page.
    We use multiple signals:
    - Page starts with numbers (typical table continuation)
    - Page starts with lowercase (mid-sentence continuation)
    - Page starts directly with storm rows (no headers)
    - Previous page ends mid-sentence or without punctuation
    """

    # Normalize spaces
    curr = curr_text.strip()
    prev = prev_text.strip()

    if not prev:
        return False  # first page

    # Signal 1 — no headers on current page
    if not any(h in curr.lower() for h in HEADER_KEYWORDS):
        return True

    # Signal 2 — starts with numbers (row continuation)
    if curr[:1].isdigit():
        return True

    # Signal 3 — starts with lowercase letter (continuation of a sentence)
    if curr[:1].islower():
        return True

    # Signal 4 — previous page ends mid-sentence
    if not prev.endswith(('.', ';', ':')):
        return True

    return False


# ============================================================
# BUILD COMBINED OCR WITH CONTINUATION MARKERS
# ============================================================

def build_combined_ocr_text(folder: Path) -> str:
    """Combines OCR of all pages with CONTINUATION markers."""
    page_files = sorted(folder.glob("*.pdf"), key=lambda p: int(p.stem.split("_pg")[-1]))

    combined = []
    prev_text = ""

    for idx, page_pdf in enumerate(page_files, start=1):
        log.info(f"📝 OCR page {idx}: {page_pdf.name}")
        curr_text = ocr_page(page_pdf)

        if not curr_text.strip():
            log.warning(f"⚠️ Empty OCR for {page_pdf.name}")
            continue

        if idx == 1:
            combined.append(f"--- PAGE 1 ---\n{curr_text}")
        else:
            if is_continuation(curr_text, prev_text):
                combined.append(f"\n--- CONTINUED FROM PREVIOUS PAGE ---\n{curr_text}")
            else:
                combined.append(f"\n--- PAGE {idx} ---\n{curr_text}")

        prev_text = curr_text

    return "\n".join(combined).strip()


# ============================================================
# GEMINI CALL
# ============================================================

def build_prompt(text: str, doc_name: str) -> str:
    return f"""
You are an expert extracting structured storm data from NOAA storm reports.

IMPORTANT:
- When you see the marker '--- CONTINUED FROM PREVIOUS PAGE ---',
  that text is a continuation of the SAME storm event row.
  DO NOT create a new JSON entry for it.

- Merge continuation text into the previous event.

Extract only valid structured JSON:
{{
  "month": "",
  "year": "",
  "storm_events": [
     {{
        "state": "",
        "place_or_location": "",
        "date": "",
        "time": "",
        "path_length": "",
        "path_width": "",
        "killed": "",
        "injured": "",
        "property_damage_code": "",
        "crop_damage_code": "",
        "character_of_storm": "",
        "description": ""
     }}
  ]
}}

Document name: {doc_name}
Document text:
{text}
"""

def gemini_extract(doc_name: str, ocr_text: str) -> Dict[str, Any]:
    """Calls Gemini with retry + safe fallback."""
    payload = {
        "contents": [{"parts": [{"text": build_prompt(ocr_text, doc_name)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }

    for attempt in range(1, 3):  # 2 retries
        try:
            log.info(f"📡 Gemini API call attempt {attempt} for {doc_name}")
            r = requests.post(
                f"{MODEL_URL}?key={GEMINI_API_KEY}",
                json=payload,
                timeout=180
            )
            r.raise_for_status()
            txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            cleaned = txt.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(cleaned)

        except Exception as e:
            log.error(f"Gemini error: {e}")
            if attempt == 1:
                log.info("⏳ Waiting 80 sec before retry...")
                time.sleep(80)

    # Final fallback if Gemini still fails
    return {
        "month": "",
        "year": "",
        "storm_events": [],
        "error": "Gemini extraction failed after retries"
    }


# ============================================================
# PER DOCUMENT PROCESSING
# ============================================================

def extract_from_raw_folder(doc_folder: Path):
    doc_name = doc_folder.name

    log.info("\n========================================")
    log.info(f"➡️ Starting extraction for {doc_name}")
    log.info("========================================")

    ocr_text = build_combined_ocr_text(doc_folder)
    log.info(f"✅ Combined OCR text built for {doc_name}")

    # Parse month/year for final JSON
    parts = doc_name.split("_")
    month = parts[0].capitalize()
    year = parts[1] if len(parts) > 1 else ""

    structured = gemini_extract(doc_name, ocr_text)

    # Insert month/year for DynamoDB use
    structured["month"] = month
    structured["year"] = year

    out_json = Path(LOCAL_PROCESSED_PATH) / f"{doc_name}.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=2)

    log.info(f"✅ JSON saved → {out_json}")

    # Archive the raw folder
    archive_dir = Path("data/archived_raw") / doc_name
    archive_dir.parent.mkdir(parents=True, exist_ok=True)

    if archive_dir.exists():
        shutil.rmtree(archive_dir)

    shutil.move(str(doc_folder), str(archive_dir))
    log.info(f"📦 Archived raw folder → {archive_dir}")


# ============================================================
# MAIN
# ============================================================

def run_gemini_extractor():
    raw_root = Path(LOCAL_RAW_PATH)
    raw_root.mkdir(parents=True, exist_ok=True)

    log.info("🚀 Starting Gemini extraction over raw/ kept pages")
    folders = [f for f in raw_root.iterdir() if f.is_dir()]

    if not folders:
        log.info("⚠️ No document folders found in raw/")
        return

    log.info(f"📌 Found {len(folders)} document folder(s): {[f.name for f in folders]}")

    for folder in folders:
        extract_from_raw_folder(folder)

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        raise RuntimeError("❌ Missing GEMINI_API_KEY in .env")

    run_gemini_extractor()
