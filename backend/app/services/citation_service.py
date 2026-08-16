"""
Phase: Citation tracking.
Maps every source used in a research session to a stable [Source N]
index so the synthesized report and the UI's "why this recommendation"
panel can point back to exact sources.
"""
from app.models.source import Source


def build_source_index(sources: list[Source]) -> tuple[str, dict[str, int]]:
    """
    Returns:
      - a human-readable block for the synthesis prompt, e.g.
        "[0] Title (Publisher)\n[1] Title2 (Publisher2)"
      - a mapping of source_id (str) -> index, so evidence can be
        translated into [Source N] citations in the final report.
    """
    lines = []
    id_to_index: dict[str, int] = {}
    for i, s in enumerate(sources):
        id_to_index[str(s.id)] = i
        lines.append(f"[{i}] {s.title} ({s.publisher or 'unknown'}) - {s.url or 'no url'}")
    return "\n".join(lines), id_to_index


def resolve_citation_indices(source_ids: list[str], id_to_index: dict[str, int]) -> list[int]:
    return sorted({id_to_index[sid] for sid in source_ids if sid in id_to_index})
