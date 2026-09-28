from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

from backend.config import settings
from backend.tools.file_store import save_to_file
from backend.tools.web_search import web_search

# Agent names (used by the service layer to pick answers)
ASSISTANT_NAME = "Assistant"
WEB_SEARCH_NAME = "Web_Search_Assistant"
ENTRY_NAME = "Entry_Agent"

MAX_MESSAGES = 4  # user + 3 agents

# ============ System Prompts ============

ASSISTANT_PROMPT = (
    "You are a helpful customer support assistant. "
    "Answer the user's query directly using your own knowledge. "
    "Keep the answer clear and short (under 150 words). "
    "Do not use any tools."
)

WEB_SEARCH_PROMPT = (
    "You are a web research assistant. Today's date is {today}. "
    "Call the web_search tool with the user's query EXACTLY as the user wrote it. "
    "Do NOT add any year to the query. "
    "Your own knowledge is OUTDATED. Answer ONLY using the search results. "
    "If the search results disagree with what you remember, TRUST THE SEARCH RESULTS. "
    "Prefer the DIRECT ANSWER and the most recent dated results. "
    "The 'Published' field is when an article was published, NOT when the event happened. "
    "Snippets may use relative words like 'today', 'this morning' or '3 months ago'; "
    "do NOT assume they mean today's date. Prefer explicit dates. "
    "Never copy the Assistant's earlier answer. "
    "Keep the answer under 150 words and mention 1-2 source links at the end."
)

ENTRY_PROMPT = (
    "You are the entry agent. Read the conversation. "
    "Call the save_to_file tool with: "
    "query = the user's original query, "
    f"assistant_answer = the full answer from {ASSISTANT_NAME}, "
    f"web_answer = the full answer from {WEB_SEARCH_NAME}. "
    "After saving, reply with both answers under the headings "
    "'Assistant Answer' and 'Web Search Answer', "
    "and end your message with the word TERMINATE."
)


# ============ Factory Functions ============

def build_model_client() -> OpenAIChatCompletionClient:
    """Create a new OpenAI model client using settings from .env."""
    return OpenAIChatCompletionClient(
        model=settings.LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
    )


def build_support_team():
    """Create a FRESH team for every request (no shared history between users)."""
    model_client = build_model_client()
    today = datetime.now().strftime("%d %B %Y")

    assistant_agent = AssistantAgent(
        name=ASSISTANT_NAME,
        model_client=model_client,
        system_message=ASSISTANT_PROMPT,
    )

    web_search_agent = AssistantAgent(
        name=WEB_SEARCH_NAME,
        model_client=model_client,
        tools=[web_search],
        reflect_on_tool_use=True,
        system_message=WEB_SEARCH_PROMPT.format(today=today),
    )

    entry_agent = AssistantAgent(
        name=ENTRY_NAME,
        model_client=model_client,
        tools=[save_to_file],
        reflect_on_tool_use=True,
        system_message=ENTRY_PROMPT,
    )

    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(
        max_messages=MAX_MESSAGES
    )

    team = RoundRobinGroupChat(
        participants=[assistant_agent, web_search_agent, entry_agent],
        termination_condition=termination,
    )

    return team, model_client