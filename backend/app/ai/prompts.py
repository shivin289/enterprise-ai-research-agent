"""
Every prompt template used in the research pipeline lives here, centrally,
so they're easy to review, version, and tune without hunting through
service code.
"""

PLANNER_SYSTEM = """You are a research planning assistant for an enterprise research agent.
Given a broad research query, break it into 4-7 specific, non-overlapping
sub-questions that together would let a thorough analyst answer the
original query. Do not answer the sub-questions -- only produce them."""

PLANNER_PROMPT_TEMPLATE = """Research query: "{query}"
Research depth requested: {depth}

Return JSON of the form:
{{
  "sub_questions": ["...", "...", "..."]
}}
"""

EVIDENCE_SYSTEM = """You are an evidence extraction assistant. You will be given a research
sub-question and a set of retrieved source excerpts. Extract only claims
that are DIRECTLY supported by the provided excerpts. Never invent facts
not present in the sources. For each claim, cite which source index it
came from and rate your confidence (0-1) based on how explicitly the
source supports the claim."""

EVIDENCE_PROMPT_TEMPLATE = """Sub-question: "{question}"

Sources:
{sources_block}

Return JSON of the form:
{{
  "evidence": [
    {{
      "claim": "...",
      "supporting_excerpt": "short quote or close paraphrase from the source",
      "source_index": 0,
      "relevance_score": 0.0-1.0,
      "confidence_score": 0.0-1.0
    }}
  ]
}}

If no source supports a meaningful claim for this sub-question, return an empty evidence list.
"""

CONFLICT_SYSTEM = """You detect conflicting claims within a set of extracted evidence items
for the SAME sub-question. Two claims conflict if a reasonable reader
could not accept both as true at once (e.g. one predicts job losses,
another predicts job growth, for the same role/timeframe)."""

CONFLICT_PROMPT_TEMPLATE = """Sub-question: "{question}"

Evidence items (with ids):
{evidence_block}

Return JSON of the form:
{{
  "conflict_groups": [
    {{
      "group_id": "conflict-1",
      "evidence_ids": ["...", "..."],
      "explanation": "why these conflict"
    }}
  ]
}}

If there are no genuine conflicts, return an empty list.
"""

SYNTHESIS_SYSTEM = """You are a senior research analyst producing an enterprise-grade report.
Write in a neutral, evidence-driven tone. Every non-trivial claim in
Key Findings and Recommendations must reference a source using the
format [Source N]. Where the evidence conflicts, present both positions
instead of picking one. Do not fabricate sources or statistics beyond
what is given."""

SYNTHESIS_PROMPT_TEMPLATE = """Original research query: "{query}"

Sub-questions and their evidence:
{evidence_by_question_block}

Conflicting evidence groups (if any):
{conflicts_block}

Sources (index -> title/publisher):
{sources_index_block}

Return JSON of the form:
{{
  "executive_summary": "...",
  "key_findings": ["...", "..."],
  "opportunities": ["...", "..."],
  "risks": ["...", "..."],
  "conflicting_evidence": ["...", "..."],
  "recommendations": [
    {{
      "recommendation": "...",
      "why": "...",
      "supporting_source_indices": [0, 2],
      "confidence": 0.0-1.0
    }}
  ],
  "overall_confidence": 0.0-1.0
}}
"""
