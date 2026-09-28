import re

from pydantic import BaseModel

from backend.config import settings
from backend.utils.logger import logger

MIN_QUERY_LENGTH = 3
MAX_QUERY_LENGTH = 500

# Prompt injection / jailbreak patterns (case-insensitive)
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(the\s+)?(previous|above|prior)\s+instructions",
    r"disregard\s+(all\s+)?(the\s+)?(previous|above|prior)",
    r"(reveal|show|print|repeat)\s+(me\s+)?(your|the)\s+(system\s+prompt|instructions)",
    r"you\s+are\s+now\s+(an?\s+)?(unrestricted|evil|dan|jailbroken)",
    r"\bjailbreak\b",
    r"\bdeveloper\s+mode\b",
    r"(show|print|reveal|give)\s+(me\s+)?(your|the)\s+(api\s*keys?|\.env|secrets?)",
]
COMPILED_INJECTION = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# Secret patterns that must never reach the user
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),  # OpenAI-style keys
]

REDACTED = "[REDACTED]"


class GuardrailResult(BaseModel):
    is_safe: bool
    reason: str = ""


def validate_input(query: str) -> GuardrailResult:
    """Check the user query BEFORE it reaches the agents."""
    cleaned = (query or "").strip()

    if len(cleaned) < MIN_QUERY_LENGTH:
        return GuardrailResult(is_safe=False, reason="Query is too short. Please ask a full question.")

    if len(cleaned) > MAX_QUERY_LENGTH:
        return GuardrailResult(
            is_safe=False,
            reason=f"Query is too long. Please keep it under {MAX_QUERY_LENGTH} characters.",
        )

    for pattern in COMPILED_INJECTION:
        if pattern.search(cleaned):
            logger.warning(f"Guardrail blocked query | pattern='{pattern.pattern}'")
            return GuardrailResult(
                is_safe=False,
                reason="Your query contains instructions that are not allowed.",
            )

    return GuardrailResult(is_safe=True)


def sanitize_output(text: str) -> str:
    """Remove any secrets from agent output BEFORE it reaches the user."""
    if not text:
        return text

    sanitized = text

    # 1. Redact our real key values (strongest check)
    for secret in (settings.OPENAI_API_KEY, settings.SERPER_API_KEY):
        if secret and secret in sanitized:
            sanitized = sanitized.replace(secret, REDACTED)
            logger.warning("Guardrail redacted a real API key from output")

    # 2. Redact anything that looks like a key
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub(REDACTED, sanitized)

    return sanitized