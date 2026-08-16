"""
Search provider abstraction. The research engine calls `search()` and
never knows or cares whether results came from Tavily, SerpAPI, or a
local mock -- this is what lets us plug in enterprise connectors later
without touching the orchestrator.
"""
from __future__ import annotations

import abc
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class SearchResult:
    title: str
    url: str | None
    publisher: str | None
    published_at: datetime | None
    snippet: str
    content: str
    source_type: str = "web"
    content_hash: str = field(default="")

    def __post_init__(self) -> None:
        if not self.content_hash:
            basis = (self.url or self.title) + self.content[:500]
            self.content_hash = hashlib.sha256(basis.encode("utf-8")).hexdigest()


class SearchProvider(abc.ABC):
    @abc.abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        ...


class TavilySearchProvider(SearchProvider):
    """Wraps the Tavily search API (https://tavily.com)."""

    BASE_URL = "https://api.tavily.com/search"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                self.BASE_URL,
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("url"),
                    publisher=_publisher_from_url(item.get("url")),
                    published_at=None,
                    snippet=item.get("content", "")[:300],
                    content=item.get("content", ""),
                )
            )
        return results


class SerpApiSearchProvider(SearchProvider):
    """Wraps SerpAPI's Google search endpoint."""

    BASE_URL = "https://serpapi.com/search"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                self.BASE_URL,
                params={"q": query, "api_key": settings.serpapi_api_key, "num": max_results},
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("organic_results", [])[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("link"),
                    publisher=_publisher_from_url(item.get("link")),
                    published_at=None,
                    snippet=item.get("snippet", ""),
                    content=item.get("snippet", ""),
                )
            )
        return results


class MockSearchProvider(SearchProvider):
    """
    Deterministic fake search provider for local development, demos, and
    tests where no external API key is configured. Produces plausible,
    clearly-labeled placeholder sources so the rest of the pipeline
    (evidence extraction, citations, synthesis) can be exercised end to end.
    """

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        logger.warning("Using MockSearchProvider -- configure SEARCH_PROVIDER for real results.")
        results = []
        for i in range(max_results):
            results.append(
                SearchResult(
                    title=f"[MOCK] Source {i + 1} for: {query}",
                    url=f"https://example.com/mock-source-{i + 1}",
                    publisher="Mock Research Corp" if i % 2 == 0 else "Example Institute",
                    published_at=datetime.now(timezone.utc),
                    snippet=f"This is placeholder content discussing '{query}'. Replace with a real "
                             f"SEARCH_PROVIDER (tavily|serpapi) for production use.",
                    content=(
                        f"Placeholder analysis regarding '{query}'. In a real deployment this would be "
                        f"actual retrieved article content used for evidence extraction. Point {i + 1}: "
                        f"stakeholders note both opportunities and risks associated with this topic."
                    ),
                    source_type="web",
                )
            )
        return results


def _publisher_from_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        domain = url.split("//")[-1].split("/")[0]
        return domain.replace("www.", "")
    except Exception:
        return None


def get_search_provider() -> SearchProvider:
    provider_name = settings.search_provider
    if provider_name == "tavily":
        return TavilySearchProvider()
    if provider_name == "serpapi":
        return SerpApiSearchProvider()
    return MockSearchProvider()
