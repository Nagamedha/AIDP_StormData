import logging
import os
from datetime import datetime

def get_logger(name="AIDP"):
    os.makedirs("data/logs", exist_ok=True)
    logfile = "data/logs/" + datetime.now().strftime("%Y%m%d") + ".log"

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # File handler
    fh = logging.FileHandler(logfile)
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.propagate = False

    return logger
