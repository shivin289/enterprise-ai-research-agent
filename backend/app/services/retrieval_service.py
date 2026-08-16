"""
Phase: Search & Retrieval.
For each sub-question, fan out to the configured search provider (and,
optionally, internal document similarity search), then dedupe results.
"""
from app.core.logging import get_logger
from app.retrieval.search_provider import get_search_provider, SearchResult

logger = get_logger(__name__)

DEPTH_TO_RESULTS_PER_QUESTION = {"quick": 3, "standard": 4, "deep": 6}


async def retrieve_for_question(question: str, depth: str = "standard") -> list[SearchResult]:
    provider = get_search_provider()
    max_results = DEPTH_TO_RESULTS_PER_QUESTION.get(depth, 4)

    results = await provider.search(question, max_results=max_results)
    return _dedupe(results)


def _dedupe(results: list[SearchResult]) -> list[SearchResult]:
    seen_hashes: set[str] = set()
    deduped = []
    for r in results:
        if r.content_hash in seen_hashes:
            continue
        seen_hashes.add(r.content_hash)
        deduped.append(r)
    return deduped
