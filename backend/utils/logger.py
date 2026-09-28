import logging
import os
from logging.handlers import RotatingFileHandler

from backend.config import settings

os.makedirs(settings.LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(settings.LOG_DIR, "app.log")

logger = logging.getLogger("SupportAgents")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # 1. Save logs to file (max 5 MB, keep 3 old files)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # 2. Also show logs in terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)