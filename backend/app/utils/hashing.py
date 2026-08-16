import hashlib


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cache_key(*parts: str) -> str:
    """Builds a stable Redis cache key from arbitrary string parts."""
    joined = "|".join(parts)
    return "cache:" + sha256(joined)
