"""
Phase: Evidence Extraction + Conflict Detection.
Turns raw retrieved sources into structured, source-grounded claims,
then flags claims within the same sub-question that genuinely conflict.
"""
import uuid

from app.ai.llm_client import get_llm_provider
from app.ai.output_parser import safe_parse_json
from app.ai.prompts import (
    EVIDENCE_SYSTEM,
    EVIDENCE_PROMPT_TEMPLATE,
    CONFLICT_SYSTEM,
    CONFLICT_PROMPT_TEMPLATE,
)
from app.core.logging import get_logger
from app.retrieval.ranker import estimate_reliability, estimate_freshness, compute_source_score
from app.retrieval.search_provider import SearchResult

logger = get_logger(__name__)


async def extract_evidence(question: str, sources: list[SearchResult]) -> list[dict]:
    """
    Returns a list of evidence dicts:
    {claim, supporting_excerpt, source_index, relevance_score, confidence_score}
    `source_index` refers to the position in the `sources` list passed in.
    """
    if not sources:
        return []

    provider = get_llm_provider()

    sources_block = "\n\n".join(
        f"[{i}] {s.title} ({s.publisher or 'unknown publisher'})\n{s.content[:1500]}"
        for i, s in enumerate(sources)
    )
    prompt = EVIDENCE_PROMPT_TEMPLATE.format(question=question, sources_block=sources_block)

    raw = await provider.generate_json(prompt, system=EVIDENCE_SYSTEM)
    parsed = safe_parse_json(raw)
    evidence_items = parsed.get("evidence", [])

    # Attach a computed source score to each evidence item so downstream
    # ranking/synthesis can weigh evidence, not just trust the LLM's confidence.
    for item in evidence_items:
        idx = item.get("source_index", 0)
        if 0 <= idx < len(sources):
            src = sources[idx]
            reliability = estimate_reliability(src.url, src.publisher)
            freshness = estimate_freshness(src.published_at)
            item["source_score"] = compute_source_score(
                reliability=reliability,
                relevance=item.get("relevance_score", 0.5),
                freshness=freshness,
            )
        else:
            item["source_score"] = 0.3

    return evidence_items


async def detect_conflicts(question: str, evidence_items: list[dict]) -> list[dict]:
    """
    evidence_items must each have an 'id' key (string/UUID) the LLM can reference.
    Returns conflict groups: [{group_id, evidence_ids, explanation}]
    """
    if len(evidence_items) < 2:
        return []

    provider = get_llm_provider()

    evidence_block = "\n".join(f"- id={e['id']}: {e['claim']}" for e in evidence_items)
    prompt = CONFLICT_PROMPT_TEMPLATE.format(question=question, evidence_block=evidence_block)

    raw = await provider.generate_json(prompt, system=CONFLICT_SYSTEM)
    parsed = safe_parse_json(raw)
    return parsed.get("conflict_groups", [])
