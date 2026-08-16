"""
Defensive parsing helpers for LLM JSON output. LLMs occasionally wrap
JSON in markdown fences or add stray text -- these helpers make callers
resilient to that without scattering try/except everywhere.
"""
import json
import re
from typing import Any


def safe_parse_json(raw: str | dict | list) -> Any:
    if isinstance(raw, (dict, list)):
        return raw

    text = raw.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Last resort: grab the first {...} or [...] block
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise
