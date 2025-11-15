import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
env_path = BASE_DIR / ".env"

if env_path.exists():
    load_dotenv(env_path)

# Read environment paths
LOCAL_INPUT_PATH = os.getenv("LOCAL_INPUT_PATH", "data/input")
LOCAL_RAW_PATH = os.getenv("LOCAL_RAW_PATH", "data/raw")
LOCAL_ERROR_PATH = os.getenv("LOCAL_ERROR_PATH", "data/error")
LOCAL_PROCESSED_PATH = os.getenv("LOCAL_PROCESSED_PATH", "data/processed")
LOG_PATH = os.getenv("LOG_PATH", "data/logs")

# Ensure all folders exist
for path in [LOCAL_INPUT_PATH, LOCAL_RAW_PATH, LOCAL_ERROR_PATH, LOCAL_PROCESSED_PATH, LOG_PATH]:
    Path(path).mkdir(parents=True, exist_ok=True)


# --- Gemini API Key ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ENABLE_GEMINI = os.getenv("ENABLE_GEMINI", "false").lower() == "true"
SAVE_OCR_DEBUG_TEXT = os.getenv("SAVE_OCR_DEBUG_TEXT", "false").lower() == "true"

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH", "credentials/service_account.json")
ENABLE_SHEETS_EXPORT = os.getenv("ENABLE_SHEETS_EXPORT", "false").lower() == "true"
