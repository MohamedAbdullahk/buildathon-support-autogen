import asyncio
import os
from datetime import datetime

import pytest
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from backend.config import settings
from backend.services.support_service import run_support_query

# DeepEval reads the key from os.environ (pydantic-settings does not set it)
os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)
os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

THRESHOLD = 0.7

# Judge must be STRONGER than the model being tested
JUDGE_MODEL = "gpt-4.1"

EVAL_QUESTIONS = [
    "How do I reset my Gmail password?",
    "Who is the CM of Tamil Nadu now?",
    "How can I track my Amazon order?",
    "What is the latest stable version of Python?",
    "How do I cancel my Netflix subscription?",
]

RELEVANCY_CRITERIA = (
    "Today's date is {today}. "
    "The retrieval context comes from a live web search and is MORE RECENT than your training data. "
    "Treat the retrieval context as the source of truth for facts and dates; "
    "dates before today's date are in the past, not the future. "
    "Judge whether the actual output directly and clearly answers the user's input question. "
    "Do NOT lower the score because a fact differs from what you remember. "
    "Penalise answers that are off-topic, evasive, or padded with unrelated details."
)


def build_metrics():
    """Relevancy (grounded, date-aware) + Faithfulness (claims supported by search context)."""
    today = datetime.now().strftime("%d %B %Y")

    relevancy = GEval(
        name="Relevancy",
        criteria=RELEVANCY_CRITERIA.format(today=today),
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.RETRIEVAL_CONTEXT,
        ],
        threshold=THRESHOLD,
        model=JUDGE_MODEL,
    )
    faithfulness = FaithfulnessMetric(
        threshold=THRESHOLD,
        model=JUDGE_MODEL,
        include_reason=True,
    )
    return [relevancy, faithfulness]


@pytest.mark.eval
@pytest.mark.parametrize("question", EVAL_QUESTIONS)
def test_web_answer_quality(question):
    result = asyncio.run(run_support_query(question))

    # Basic sanity checks first (fail fast, before paying for judge calls)
    assert not result.blocked, f"Query was blocked: {result.block_reason}"
    assert result.web_answer, "Web answer is empty"
    assert result.search_context, "No search context captured"

    test_case = LLMTestCase(
        input=question,
        actual_output=result.web_answer,
        retrieval_context=[result.search_context],
    )

    assert_test(test_case, build_metrics())