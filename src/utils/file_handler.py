import shutil
from pathlib import Path
from src.utils.config import LOCAL_ERROR_PATH
from src.utils.logger import get_logger

log = get_logger("file_handler")

def move_to_error(src_file: Path):
    dst = Path(LOCAL_ERROR_PATH) / src_file.name
    shutil.move(str(src_file), str(dst))
    log.info(f"🚫 Moved to ERROR folder → {dst}")
