from datetime import datetime

from fastapi import APIRouter

from backend.config import settings

router = APIRouter()


@router.get("")
async def health_check():
    """Simple health check - used by Docker, Nginx and uptime monitors."""
    return {
        "status": "ok",
        "model": settings.LLM_MODEL,
        "keys_configured": bool(settings.OPENAI_API_KEY and settings.SERPER_API_KEY),
        "time": datetime.now().isoformat(timespec="seconds"),
    }