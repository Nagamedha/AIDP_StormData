# main.py

from src.pipeline.pipeline_runner import run_pipeline
from src.utils.config import ENABLE_GEMINI, ENABLE_SHEETS_EXPORT
from src.utils.logger import get_logger

logger = get_logger("main")

def main():
    logger.info("🚀 Starting AIDP_StormData pipeline")

    # STEP 1 — OCR + Page Filtering
    run_pipeline()

    # STEP 2 — Gemini extraction
    if ENABLE_GEMINI:
        try:
            logger.info("⚡ Running Gemini extractor...")
            from src.extraction.gemini_extractor import run_gemini_extractor
            run_gemini_extractor()
        except Exception as e:
            logger.error(f"❌ Gemini failed: {e}")
    else:
        logger.info("⏭ Skipped Gemini (ENABLE_GEMINI=false)")

    # STEP 3 — Google Sheets export
    if ENABLE_SHEETS_EXPORT:
        try:
            logger.info("📤 Exporting processed JSON to Google Sheets...")
            from src.export.google_sheets_exporter import run_google_sheets_exporter
            run_google_sheets_exporter()
        except Exception as e:
            logger.error(f"❌ Sheets export failed: {e}")
    else:
        logger.info("⏭ Skipped Sheets export (ENABLE_SHEETS_EXPORT=false)")

    logger.info("🏁 Pipeline completed.")

if __name__ == "__main__":
    main()
