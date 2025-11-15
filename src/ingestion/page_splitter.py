# src/ingestion/page_splitter.py
"""
Splits a single multi-page PDF into one-page PDFs for downstream OCR processing.

This module does NOT scan the input folder or move originals.
That orchestration is handled by src.pipeline.pipeline_runner.
"""

from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from src.utils.logger import get_logger

logger = get_logger("page_splitter")


def split_pdf_to_pages(pdf_path: Path, output_dir: Path) -> int:
    """
    Splits a single multi-page PDF into one-page PDFs under output_dir.

    Returns:
        int: number of pages successfully written.
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        # Clean any existing page PDFs for this document to avoid stale files
        for f in output_dir.glob("*.pdf"):
            try:
                f.unlink()
            except Exception as e:
                logger.warning(f"⚠️ Could not delete old page file {f}: {e}")

        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)

        logger.info(f"📄 Splitting {pdf_path.name} into {total_pages} pages...")

        for i in range(total_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])

            page_filename = f"{pdf_path.stem.lower()}_pg{i+1}.pdf"
            output_path = output_dir / page_filename

            with open(output_path, "wb") as out_f:
                writer.write(out_f)

            logger.info(f"   ✅ Saved {output_path.name} ({i+1}/{total_pages})")

        logger.info(f"✅ Finished splitting {pdf_path.name} ({total_pages} pages).")
        return total_pages

    except Exception as e:
        logger.error(f"❌ Failed to split {pdf_path.name}: {e}")
        return 0
