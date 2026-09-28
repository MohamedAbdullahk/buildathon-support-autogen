import time
from typing import List

from autogen_agentchat.messages import TextMessage, ToolCallExecutionEvent
from pydantic import BaseModel

from backend.agents.support_team import (
    ASSISTANT_NAME,
    ENTRY_NAME,
    WEB_SEARCH_NAME,
    build_support_team,
)
from backend.services.guardrails import sanitize_output, validate_input  # ⭐
from backend.utils.logger import logger


# ============ Result Models ============

class TraceItem(BaseModel):
    source: str
    type: str
    content: str


class SupportResult(BaseModel):
    query: str
    blocked: bool = False            # ⭐
    block_reason: str = ""           # ⭐
    assistant_answer: str = ""
    web_answer: str = ""
    entry_reply: str = ""
    search_context: str = ""
    stop_reason: str = ""
    duration_seconds: float = 0.0
    trace: List[TraceItem] = []


# ============ Service Function ============

async def run_support_query(query: str) -> SupportResult:
    """Run the 3-agent team for one query and return a clean, structured result."""
    start_time = time.perf_counter()

    # ⭐ 1. INPUT GUARD - block bad queries before calling any agent
    check = validate_input(query)
    if not check.is_safe:
        logger.warning(f"Query blocked by guardrails | reason='{check.reason}'")
        return SupportResult(query=query, blocked=True, block_reason=check.reason)

    query = query.strip()
    team, model_client = build_support_team()
    logger.info(f"Support query started | query='{query}'")

    try:
        result = await team.run(task=query)
    except Exception as e:
        logger.error(f"Support team failed | query='{query}' | error={e}")
        raise
    finally:
        await model_client.close()

    assistant_answer = ""
    web_answer = ""
    entry_reply = ""
    search_context = ""
    trace: List[TraceItem] = []

    for msg in result.messages:
        trace.append(
            TraceItem(
                source=msg.source,
                type=type(msg).__name__,
                content=sanitize_output(str(msg.content)),  # ⭐
            )
        )

        if isinstance(msg, TextMessage):
            if msg.source == ASSISTANT_NAME:
                assistant_answer = msg.content
            elif msg.source == WEB_SEARCH_NAME:
                web_answer = msg.content
            elif msg.source == ENTRY_NAME:
                entry_reply = msg.content.replace("TERMINATE", "").strip()

        elif isinstance(msg, ToolCallExecutionEvent) and msg.source == WEB_SEARCH_NAME:
            search_context = "\n\n".join(r.content for r in msg.content)

    duration = round(time.perf_counter() - start_time, 2)
    logger.info(f"Support query done | query='{query}' | duration={duration}s")

    # ⭐ 2. OUTPUT GUARD - redact secrets before returning
    return SupportResult(
        query=query,
        assistant_answer=sanitize_output(assistant_answer),
        web_answer=sanitize_output(web_answer),
        entry_reply=sanitize_output(entry_reply),
        search_context=search_context,
        stop_reason=result.stop_reason or "",
        duration_seconds=duration,
        trace=trace,
    )