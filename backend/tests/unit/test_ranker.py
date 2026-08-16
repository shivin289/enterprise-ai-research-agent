"""Unit tests for source scoring logic -- no DB/LLM required."""
from datetime import datetime, timedelta, timezone

from app.retrieval.ranker import estimate_reliability, estimate_freshness, compute_source_score


def test_gov_domain_scores_highest_reliability():
    assert estimate_reliability("https://www.data.gov/report", None) == 1.0


def test_unknown_domain_gets_default_reliability():
    assert estimate_reliability("https://randomblog123.xyz", None) == 0.5


def test_recent_content_scores_high_freshness():
    recent = datetime.now(timezone.utc) - timedelta(days=5)
    assert estimate_freshness(recent) == 1.0


def test_old_content_scores_low_freshness():
    old = datetime.now(timezone.utc) - timedelta(days=1500)
    assert estimate_freshness(old) == 0.3


def test_missing_date_gets_moderate_freshness():
    assert estimate_freshness(None) == 0.6


def test_compute_source_score_is_clamped_between_0_and_1():
    score = compute_source_score(reliability=1.0, relevance=1.0, freshness=1.0)
    assert 0.0 <= score <= 1.0
    assert score == 1.0

    score_low = compute_source_score(reliability=0.0, relevance=0.0, freshness=0.0)
    assert score_low == 0.0
