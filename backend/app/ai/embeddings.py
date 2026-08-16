"""
Thin helper around the LLM provider's embed() call, plus cosine similarity
utility used by the ranker when we're not doing DB-side pgvector search.
"""
import numpy as np

from app.ai.llm_client import get_llm_provider


async def embed_texts(texts: list[str]) -> list[list[float]]:
    provider = get_llm_provider()
    return await provider.embed(texts)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = (np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)
