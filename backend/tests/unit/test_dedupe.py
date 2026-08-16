from app.services.retrieval_service import _dedupe
from app.retrieval.search_provider import SearchResult


def _make(title, content="same content"):
    return SearchResult(title=title, url=f"https://example.com/{title}", publisher="Test",
                         published_at=None, snippet="", content=content)


def test_dedupe_removes_identical_content_hash():
    a = _make("A", content="identical")
    b = _make("B", content="identical")  # different URL/title, but url is part of hash basis too
    results = _dedupe([a, a])
    assert len(results) == 1


def test_dedupe_keeps_distinct_results():
    a = _make("A", content="one")
    b = _make("B", content="two")
    results = _dedupe([a, b])
    assert len(results) == 2
