"""
Phase: Research Planner.
Decomposes a broad research query into focused sub-questions. The
planner NEVER answers -- it only plans, per the architecture spec.
"""
from app.ai.llm_client import get_llm_provider
from app.ai.output_parser import safe_parse_json
from app.ai.prompts import PLANNER_SYSTEM, PLANNER_PROMPT_TEMPLATE
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.cache_service import cached_generate_json

logger = get_logger(__name__)

DEPTH_TO_QUESTION_COUNT = {"quick": 3, "standard": 5, "deep": 7}


async def plan_research(query: str, depth: str = "standard") -> list[str]:
    provider = get_llm_provider()
    target_count = DEPTH_TO_QUESTION_COUNT.get(depth, 5)
    model_version = get_settings().openai_model

    prompt = PLANNER_PROMPT_TEMPLATE.format(query=query, depth=depth)
    # Cache-first: identical queries at the same depth skip a duplicate LLM call.
    raw = await cached_generate_json(provider, prompt, PLANNER_SYSTEM, model_version)
    parsed = safe_parse_json(raw)

    sub_questions = parsed.get("sub_questions", [])
    if not sub_questions:
        logger.warning("Planner returned no sub-questions for query=%r; falling back to the raw query.", query)
        return [query]

    return sub_questions[:target_count]
