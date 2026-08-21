"""
LLM provider abstraction.

The rest of the application only ever talks to `LLMProvider`. This means
swapping OpenAI for Anthropic, or a local model, never touches business
logic in services/ — only this file and config change.
"""
from __future__ import annotations

import abc
import json
import re
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LLMProvider(abc.ABC):
    """Common interface every model backend must implement."""

    @abc.abstractmethod
    async def generate(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> str:
        """Return a raw text completion."""

    @abc.abstractmethod
    async def generate_json(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> Any:
        """Return a parsed JSON object. Provider is responsible for enforcing JSON-only output."""

    @abc.abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.embedding_model = settings.openai_embedding_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate_json(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> Any:
        messages = []
        base_system = (system or "") + "\nRespond ONLY with valid JSON. No markdown, no preamble."
        messages.append({"role": "system", "content": base_system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(model=self.embedding_model, input=texts)
        return [item.embedding for item in response.data]


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return "".join(block.text for block in response.content if block.type == "text")

    async def generate_json(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> Any:
        base_system = (system or "") + "\nRespond ONLY with valid JSON. No markdown, no preamble."
        raw = await self.generate(prompt, system=base_system, temperature=temperature)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Anthropic has no first-party embeddings API; fall back to OpenAI for embeddings
        # if configured, otherwise raise so the caller knows to switch providers.
        raise NotImplementedError(
            "AnthropicProvider has no embeddings endpoint. Set LLM_PROVIDER=openai "
            "or configure a dedicated embedding provider."
        )

class GroqProvider(LLMProvider):
    """
    OpenAI-compatible free-tier provider (https://groq.com). Uses the
    standard `openai` Python client pointed at Groq's endpoint -- Groq
    implements the same chat completions API shape, so this needed almost
    no new code. Runs fast open models (Llama 3.3, etc.) at no cost, no
    credit card required for the free tier.

    Note: Groq has no embeddings endpoint, so document upload / pgvector
    similarity search won't work under this provider. The core research
    pipeline (planning, evidence, synthesis) doesn't need embeddings and
    works fully.
    """

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self) -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=settings.groq_api_key, base_url=self.BASE_URL, timeout=60.0)
        self.model = settings.groq_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate_json(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> Any:
        messages = []
        base_system = (system or "") + "\nRespond ONLY with valid JSON. No markdown, no preamble, no code fences."
        messages.append({"role": "system", "content": base_system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            logger.error(
                "Groq API call failed: %s: %s | underlying cause: %r",
                type(exc).__name__, str(exc), exc.__cause__,
            )
            raise
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            "Groq has no embeddings endpoint. Document upload / pgvector search "
            "won't work under LLM_PROVIDER=groq. The core research pipeline "
            "(planning/evidence/synthesis) doesn't call embed() and is unaffected."
        )

class LocalModelProvider(LLMProvider):
    """Stub for a self-hosted / Ollama-style model. Swap in a real client here."""

    def __init__(self) -> None:
        raise NotImplementedError("Wire this up to your local inference server (e.g. Ollama, vLLM).")

    async def generate(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> str:
        raise NotImplementedError

    async def generate_json(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> Any:
        raise NotImplementedError

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

class MockLLMProvider(LLMProvider):
    """
    Zero-cost, zero-key LLM provider for local development and demos.
    Detects which pipeline phase is calling it (planner / evidence /
    conflict-detection / synthesis) by inspecting the prompt's requested
    JSON shape, and returns plausible, clearly-labeled placeholder data.

    Lets you exercise the ENTIRE research pipeline end-to-end -- planning,
    search, evidence extraction, conflict detection, synthesis, citation
    rendering, and the frontend UI -- without any API key or billing.
    Swap LLM_PROVIDER back to openai/anthropic for real output quality.
    """

    async def generate(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> str:
        return f"[MOCK LLM] This is a placeholder response for: {prompt[:80]}..."

    async def generate_json(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> Any:
        logger.warning("Using MockLLMProvider -- set LLM_PROVIDER=openai|anthropic for real output.")

        if '"sub_questions"' in prompt:
            return {
                "sub_questions": [
                    "What is the current state of this topic?",
                    "What are the main drivers or causes?",
                    "What do experts/industry reports say?",
                    "What are the likely future developments?",
                ]
            }

        if '"evidence"' in prompt:
            indices = [int(n) for n in re.findall(r"^\[(\d+)\]", prompt, re.MULTILINE)]
            if not indices:
                indices = [0]
            return {
                "evidence": [
                    {
                        "claim": "[MOCK] Placeholder claim supported by the retrieved source.",
                        "supporting_excerpt": "[MOCK] Placeholder excerpt text.",
                        "source_index": indices[0],
                        "relevance_score": 0.7,
                        "confidence_score": 0.65,
                    }
                ]
            }

        if '"conflict_groups"' in prompt:
            return {"conflict_groups": []}

        if '"executive_summary"' in prompt:
            return {
                "executive_summary": "[MOCK] This is a placeholder executive summary. "
                                      "Configure a real LLM_PROVIDER for actual analysis.",
                "key_findings": ["[MOCK] Placeholder key finding one.", "[MOCK] Placeholder key finding two."],
                "opportunities": ["[MOCK] Placeholder opportunity."],
                "risks": ["[MOCK] Placeholder risk."],
                "conflicting_evidence": [],
                "recommendations": [
                    {
                        "recommendation": "[MOCK] Placeholder recommendation.",
                        "why": "[MOCK] Placeholder rationale.",
                        "supporting_source_indices": [0],
                        "confidence": 0.6,
                    }
                ],
                "overall_confidence": 0.6,
            }

        return {}

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import hashlib

        vectors = []
        for text in texts:
            seed = int(hashlib.sha256(text.encode()).hexdigest(), 16)
            rng = __import__("random").Random(seed)
            vectors.append([rng.uniform(-1, 1) for _ in range(1536)])
        return vectors

_provider_instance: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """Factory returning the configured provider as a singleton."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    if settings.llm_provider == "openai":
        _provider_instance = OpenAIProvider()
    elif settings.llm_provider == "anthropic":
        _provider_instance = AnthropicProvider()
    elif settings.llm_provider == "groq":
        _provider_instance = GroqProvider()
    elif settings.llm_provider == "local":
        _provider_instance = LocalModelProvider()
    elif settings.llm_provider == "mock":
        _provider_instance = MockLLMProvider()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")

    logger.info("LLM provider initialized: %s", settings.llm_provider)
    return _provider_instance
