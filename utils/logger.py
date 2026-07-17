"""
utils/logger.py
---------------

Provides a shared logger for the application. Logs are written to both
the console and a log file to make debugging and monitoring easier.
"""
import logging
import sys
from pathlib import Path

# Project root = two levels up from this file (utils/logger.py -> project root)
LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
DEFAULT_LOG_FILE = LOGS_DIR / "backend.log"


def get_logger(name: str, log_filename: str = "backend.log") -> logging.Logger:
    """
    Returns a logger that writes to BOTH the console and a file inside logs/.

    log_filename lets specific modules use their own file - e.g.
    predictor.py uses "prediction.log" so prediction history is easy to
    audit separately from general backend/request logs.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )

        # Console handler - what you see live in the terminal
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler - persists across restarts, useful for debugging
        # a demo run after the fact or checking what happened while a
        # long interview call was in progress.
        file_handler = logging.FileHandler(LOGS_DIR / log_filename, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.setLevel(logging.INFO)
    return logger
