import re


def truncate(text: str, max_chars: int = 500) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
