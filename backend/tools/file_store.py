import os
from datetime import datetime

from backend.config import settings
from backend.utils.logger import logger

ANSWERS_FILE = os.path.join(settings.DATA_DIR, "answers.txt")


def save_to_file(query: str, assistant_answer: str, web_answer: str) -> str:
    """Save the user query, the assistant answer and the web search answer to answers.txt."""
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(ANSWERS_FILE, "a", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"Time: {timestamp}\n")
            f.write(f"Query: {query}\n\n")
            f.write(f"Assistant Answer:\n{assistant_answer}\n\n")
            f.write(f"Web Search Answer:\n{web_answer}\n\n")
    except OSError as e:
        logger.error(f"Save to file failed | error={e}")
        return f"Save failed: {e}"

    logger.info(f"Saved answers to {ANSWERS_FILE} | query='{query}'")
    return f"Saved successfully to {ANSWERS_FILE}"