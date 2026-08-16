"""
Redis-backed LLM response cache.

Before calling the LLM we hash (question + context + model_version) and
check Redis; on a hit we skip the LLM call entirely. This is what the
architecture doc's "Caching" section (#16) describes -- it cuts cost,
latency, and duplicate work for repeated/overlapping research queries.
"""
import json
from typing import Any

import redis

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.hashing import cache_key

logger = get_logger(__name__)
settings = get_settings()

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def get_cached(*key_parts: str) -> Any | None:
    try:
        client = get_redis()
        raw = client.get(cache_key(*key_parts))
        return json.loads(raw) if raw else None
    except redis.RedisError:
        logger.warning("Redis unavailable; skipping cache read.")
        return None


def set_cached(value: Any, *key_parts: str) -> None:
    try:
        client = get_redis()
        client.setex(cache_key(*key_parts), settings.cache_ttl_seconds, json.dumps(value))
    except redis.RedisError:
        logger.warning("Redis unavailable; skipping cache write.")


async def cached_generate_json(provider, prompt: str, system: str, model_version: str, temperature: float = 0.2):
    """Wraps provider.generate_json() with a cache-first lookup."""
    cached = get_cached(prompt, system, model_version)
    if cached is not None:
        logger.info("Cache hit for LLM call.")
        return cached

    result = await provider.generate_json(prompt, system=system, temperature=temperature)
    set_cached(result, prompt, system, model_version)
    return result
