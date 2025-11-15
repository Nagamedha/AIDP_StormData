# src/export/google_sheets_exporter.py

"""
Google Sheets Exporter for AIDP_StormData
----------------------------------------
Reads all JSON files in data/processed/
Flattens "storm_events" list into rows
Adds month/year extracted from filename
Appends rows into a Google Sheet
Moves processed JSON files → data/archived_processed/

Run standalone:
    python -m src.export.google_sheets_exporter
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List

import gspread
from google.oauth2.service_account import Credentials

from src.utils.logger import get_logger
from src.utils.config import (
    GOOGLE_SHEET_ID,
    SERVICE_ACCOUNT_PATH,
    LOCAL_PROCESSED_PATH,
)

log = get_logger("sheets_exporter")

# ---------------------- CLEANING HELPERS ----------------------
def clean_numeric(val):
    """
    Clean numeric-like fields while preserving ?, NR, "".
    Also removes hidden apostrophes that force Google Sheets text mode.
    """
    if val is None:
        return ""

    val = str(val).strip()

    # Preserve NOAA-specific unknown markers
    if val in ["?", "NR", ""]:
        return val

    # Remove hidden apostrophes like '12 or '09-12
    if val.startswith("'"):
        val = val[1:]

    # Extract first numeric sequence only
    import re
    digits = re.findall(r"\d+", val)

    return digits[0] if digits else ""

def clean_date(val):
    """
    Extract only the first 1–2 digits (e.g. 09 from '09-12').
    """
    if val is None:
        return ""

    val = str(val).strip()

    if val in ["?", "NR", ""]:
        return val

    # Remove leading apostrophe
    if val.startswith("'"):
        val = val[1:]

    import re
    digits = re.findall(r"\d+", val)

    if not digits:
        return ""

    # Only return the FIRST numeric chunk
    return digits[0][:2]   # ensures “09-12” → “09”


# --------------------------
# CONSTANTS
# --------------------------

ARCHIVED_PROCESSED_PATH = Path("data/archived_processed")
ARCHIVED_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# --------------------------
# LOAD GOOGLE SHEET CLIENT
# --------------------------

def load_google_sheet():
    """Authenticate service account and return the worksheet."""
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_PATH,
            scopes=SCOPES
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = sheet.sheet1  # use first sheet
        log.info("✅ Connected to Google Sheet successfully")
        return worksheet
    except Exception as e:
        log.error(f"❌ Failed to authenticate Google Sheets: {e}")
        raise


# --------------------------
# FILE HELPERS
# --------------------------

def extract_month_year(file_name: str) -> (str, str):
    """
    Example:
        'jan_1993.json' -> ('jan', '1993')
        'oct_1970.json' -> ('oct', '1970')
    """
    base = Path(file_name).stem  # remove .json
    parts = base.split("_")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return "", ""


def flatten_event(event: Dict[str, Any], month: str, year: str, file_name: str, idx: int) -> List[str]:
    """
    Convert a single storm_event dict → list (row).
    Preserves column order exactly as your sheet headers.
    """
    return [
        month,
        year,
        event.get("state", ""),
        event.get("place_or_location", ""),

        clean_date(event.get("date", "")),
        event.get("time", ""),

        clean_numeric(event.get("path_length", "")),
        clean_numeric(event.get("path_width", "")),
        clean_numeric(event.get("killed", "")),
        clean_numeric(event.get("injured", "")),
        clean_numeric(event.get("property_damage_code", "")),
        clean_numeric(event.get("crop_damage_code", "")),

        event.get("character_of_storm", ""),
        event.get("description", ""),
        file_name,
        idx
    ]

    # return [
    #     month,
    #     year,
    #     event.get("state", ""),
    #     event.get("place_or_location", ""),
    #     event.get("date", ""),
    #     event.get("time", ""),
    #     event.get("path_length", ""),
    #     event.get("path_width", ""),
    #     event.get("killed", ""),
    #     event.get("injured", ""),
    #     event.get("property_damage_code", ""),
    #     event.get("crop_damage_code", ""),
    #     event.get("character_of_storm", ""),
    #     event.get("description", ""),
    #     file_name,
    #     idx  # page/row index for debugging/auditing
    # ] 


# --------------------------
# MAIN PROCESSOR
# --------------------------

def process_json_file(json_path: Path, worksheet):
    """
    Read one processed JSON file, write rows to Google Sheets, archive JSON.
    """
    file_name = json_path.name
    log.info(f"➡️ Processing JSON: {file_name}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log.error(f"❌ Failed reading {file_name}: {e}")
        return

    # Extract month/year from filename
    month, year = extract_month_year(file_name)

    events = data.get("storm_events", [])
    if not isinstance(events, list):
        log.error(f"❌ Invalid JSON format in {file_name} — missing storm_events list")
        return

    # Build rows
    rows_to_insert = []
    for idx, event in enumerate(events, start=1):
        row = flatten_event(event, month, year, file_name, idx)
        rows_to_insert.append(row)

    # Append to Google Sheet
    try:
        worksheet.append_rows(rows_to_insert, value_input_option="USER_ENTERED")
        log.info(f"✅ Appended {len(rows_to_insert)} rows from {file_name}")
    except Exception as e:
        log.error(f"❌ Failed appending rows for {file_name}: {e}")
        return

    # Move processed JSON to archive
    try:
        archived_path = ARCHIVED_PROCESSED_PATH / file_name
        shutil.move(str(json_path), str(archived_path))
        log.info(f"📦 Archived JSON → {archived_path}")
    except Exception as e:
        log.error(f"❌ Failed archiving JSON file {file_name}: {e}")


# --------------------------
# RUN FOR ALL JSON FILES
# --------------------------

def run_google_sheets_exporter():
    """Main entry point to export all processed JSON into Google Sheet."""
    log.info("🚀 Starting Google Sheets Exporter...")

    processed_dir = Path(LOCAL_PROCESSED_PATH)
    processed_dir.mkdir(parents=True, exist_ok=True)

    worksheet = load_google_sheet()

    json_files = list(processed_dir.glob("*.json"))
    if not json_files:
        log.warning("⚠️ No JSON files found in data/processed/ — nothing to export.")
        return

    log.info(f"📌 Found {len(json_files)} JSON file(s) to export")

    for json_path in json_files:
        process_json_file(json_path, worksheet)

    log.info("🏁 Google Sheet export completed successfully.")


# --------------------------
# Standalone Run
# --------------------------

if __name__ == "__main__":
    run_google_sheets_exporter()
