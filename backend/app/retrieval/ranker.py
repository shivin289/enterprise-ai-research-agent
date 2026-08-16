"""
Combines reliability + relevance + freshness into a single source score,
per the "source scoring" requirement in the architecture doc.
"""
from datetime import datetime, timezone

# Static reliability priors by publisher/domain pattern. In production this
# would be a maintained allowlist/table, not a hardcoded dict.
RELIABILITY_TABLE: dict[str, float] = {
    ".gov": 1.0,
    ".edu": 0.95,
    "nature.com": 0.95,
    "arxiv.org": 0.85,
    "mckinsey.com": 0.9,
    "gartner.com": 0.9,
    "reuters.com": 0.8,
    "bloomberg.com": 0.8,
    "nytimes.com": 0.75,
    "techcrunch.com": 0.7,
    "medium.com": 0.45,
}
DEFAULT_RELIABILITY = 0.5


def estimate_reliability(url: str | None, publisher: str | None) -> float:
    haystack = f"{url or ''} {publisher or ''}".lower()
    for pattern, score in RELIABILITY_TABLE.items():
        if pattern in haystack:
            return score
    return DEFAULT_RELIABILITY


def estimate_freshness(published_at: datetime | None) -> float:
    """1.0 for very recent content, decaying toward 0.3 floor for old content."""
    if published_at is None:
        return 0.6  # unknown date -> assume moderate freshness
    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_days = max((now - published_at).days, 0)
    if age_days <= 30:
        return 1.0
    if age_days <= 180:
        return 0.85
    if age_days <= 365:
        return 0.65
    if age_days <= 365 * 3:
        return 0.45
    return 0.3


def compute_source_score(
    reliability: float,
    relevance: float,
    freshness: float,
    weights: tuple[float, float, float] = (0.4, 0.4, 0.2),
) -> float:
    """Weighted blend of the three signals, clamped to [0, 1]."""
    w_rel, w_relv, w_fresh = weights
    score = reliability * w_rel + relevance * w_relv + freshness * w_fresh
    return max(0.0, min(1.0, score))
