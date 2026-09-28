import requests

from backend.config import settings
from backend.utils.logger import logger

SERPER_URL = "https://google.serper.dev/search"
TIMEOUT_SECONDS = 15
MAX_RESULTS = 5


def web_search(query: str) -> str:
    """Search the web for the given query and return the latest top results."""
    if not query or not query.strip():
        return "Web search failed: empty query."

    headers = {
        "X-API-KEY": settings.SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": MAX_RESULTS, "gl": "in"}

    logger.info(f"Web search started | query='{query}'")

    try:
        response = requests.post(
            SERPER_URL, headers=headers, json=payload, timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        logger.error(f"Web search timeout | query='{query}'")
        return "Web search failed: the search service timed out."
    except Exception as e:
        logger.error(f"Web search error | query='{query}' | error={e}")
        return f"Web search failed: {e}"

    results = []

    # 1. Google's direct answer box (most accurate for facts)
    answer_box = data.get("answerBox")
    if answer_box:
        direct = answer_box.get("answer") or answer_box.get("snippet") or ""
        if direct:
            results.append(f"DIRECT ANSWER (Google): {direct}")

    # 2. Knowledge graph (info panel on the right side of Google)
    kg = data.get("knowledgeGraph")
    if kg:
        results.append(
            f"KNOWLEDGE PANEL: {kg.get('title', '')} - {kg.get('description', '')}"
        )

    # 3. Normal search results
    for item in data.get("organic", [])[:MAX_RESULTS]:
        results.append(
            f"Title: {item.get('title', '')}\n"
            f"Published: {item.get('date', '')}\n"
            f"Snippet: {item.get('snippet', '')}\n"
            f"Link: {item.get('link', '')}"
        )

    logger.info(f"Web search done | query='{query}' | results={len(results)}")

    if not results:
        return "No results found."
    return "\n\n".join(results)