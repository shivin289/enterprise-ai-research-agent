"""
Research Orchestrator.

This is the heart of the application: it runs a research session through
every phase of the pipeline in order, persisting state as it goes so the
frontend can poll /research/{id}/status and see live progress.

    plan -> search -> extract evidence -> detect conflicts -> synthesize -> save report

Each phase is intentionally a separate, testable function imported from
its own service module -- this function just sequences them and handles
persistence + error recovery.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.research import ResearchSession, ResearchQuestion, Report
from app.models.source import Source
from app.models.evidence import Evidence
from app.services import planner_service, retrieval_service, evidence_service, synthesis_service, citation_service

logger = get_logger(__name__)


async def run_research_pipeline(db: Session, session_id: uuid.UUID) -> None:
    """
    Executes the full pipeline for a research session. Designed to be called
    from a background worker (Celery/RQ task) OR inline for local dev/demo
    when no worker is running -- see workers/research_worker.py.
    """
    session = db.get(ResearchSession, session_id)
    if session is None:
        logger.error("run_research_pipeline: session %s not found", session_id)
        return

    try:
        # --- Phase: Planning ---
        _update_status(db, session, status="planning", step="creating_research_questions")
        sub_questions = await planner_service.plan_research(session.query, session.depth)

        question_rows: list[ResearchQuestion] = []
        for i, q_text in enumerate(sub_questions):
            q = ResearchQuestion(research_session_id=session.id, question=q_text, order_index=i)
            db.add(q)
            question_rows.append(q)
        db.commit()

        # --- Phase: Search + Evidence + Conflicts (per sub-question) ---
        _update_status(db, session, status="searching", step="searching_sources")

        all_sources: list[Source] = []
        evidence_by_question: dict[str, list[dict]] = {}

        for question in question_rows:
            search_results = await retrieval_service.retrieve_for_question(question.question, session.depth)

            source_rows = []
            for r in search_results:
                src = Source(
                    research_session_id=session.id,
                    title=r.title,
                    url=r.url,
                    publisher=r.publisher,
                    published_at=r.published_at,
                    source_type=r.source_type,
                    content=r.content,
                    content_hash=r.content_hash,
                )
                db.add(src)
                source_rows.append(src)
            db.flush()  # get IDs without committing yet
            all_sources.extend(source_rows)

            _update_status(db, session, status="validating", step="validating_evidence")

            raw_evidence = await evidence_service.extract_evidence(question.question, search_results)

            question_evidence_rows: list[Evidence] = []
            for item in raw_evidence:
                idx = item.get("source_index", 0)
                if not (0 <= idx < len(source_rows)):
                    continue
                ev = Evidence(
                    source_id=source_rows[idx].id,
                    research_question_id=question.id,
                    claim=item.get("claim", ""),
                    supporting_excerpt=item.get("supporting_excerpt", ""),
                    relevance_score=float(item.get("relevance_score", 0.5)),
                    confidence_score=float(item.get("confidence_score", 0.5)),
                )
                db.add(ev)
                question_evidence_rows.append(ev)
            db.flush()

            # Conflict detection needs stable ids, so flush first
            conflict_input = [
                {"id": str(ev.id), "claim": ev.claim} for ev in question_evidence_rows
            ]
            conflict_groups = await evidence_service.detect_conflicts(question.question, conflict_input)

            id_to_row = {str(ev.id): ev for ev in question_evidence_rows}
            for group in conflict_groups:
                for ev_id in group.get("evidence_ids", []):
                    row = id_to_row.get(ev_id)
                    if row:
                        row.is_conflicting = True
                        row.conflict_group = group.get("group_id")

            question.status = "validated"
            evidence_by_question[question.question] = [
                {
                    "claim": ev.claim,
                    "excerpt": ev.supporting_excerpt,
                    "source_id": str(ev.source_id),
                    "conflicting": ev.is_conflicting,
                }
                for ev in question_evidence_rows
            ]
            db.commit()

        # --- Phase: Synthesis ---
        _update_status(db, session, status="synthesizing", step="generating_report")

        sources_index_block, id_to_index = citation_service.build_source_index(all_sources)

        evidence_by_question_block = _render_evidence_block(evidence_by_question, id_to_index)
        conflicts_block = _render_conflicts_block(evidence_by_question)

        synthesis = await synthesis_service.synthesize_report(
            query=session.query,
            evidence_by_question_block=evidence_by_question_block,
            conflicts_block=conflicts_block,
            sources_index_block=sources_index_block,
        )
        report_markdown = synthesis_service.render_report_markdown(session.query, synthesis)

        from app.core.config import get_settings

        report = Report(
            research_session_id=session.id,
            summary=synthesis.get("executive_summary", ""),
            report_content=report_markdown,
            confidence_score=float(synthesis.get("overall_confidence", 0.0)),
            model_name=get_settings().openai_model,
        )
        db.add(report)

        session.status = "completed"
        session.progress_step = "done"
        session.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:  # noqa: BLE001 - top-level pipeline guard
        logger.exception("Research pipeline failed for session %s", session_id)
        session.status = "failed"
        session.error_message = str(exc)
        db.commit()


def _update_status(db: Session, session: ResearchSession, status: str, step: str) -> None:
    session.status = status
    session.progress_step = step
    db.commit()


def _render_evidence_block(evidence_by_question: dict[str, list[dict]], id_to_index: dict[str, int]) -> str:
    blocks = []
    for question, items in evidence_by_question.items():
        blocks.append(f"### {question}")
        if not items:
            blocks.append("(no supporting evidence found)")
        for item in items:
            src_idx = id_to_index.get(item["source_id"], "?")
            flag = " [CONFLICTING]" if item["conflicting"] else ""
            blocks.append(f"- {item['claim']} [Source {src_idx}]{flag}")
        blocks.append("")
    return "\n".join(blocks)


def _render_conflicts_block(evidence_by_question: dict[str, list[dict]]) -> str:
    lines = []
    for question, items in evidence_by_question.items():
        conflicting = [i for i in items if i["conflicting"]]
        if conflicting:
            lines.append(f"For '{question}':")
            for c in conflicting:
                lines.append(f"  - {c['claim']}")
    return "\n".join(lines) if lines else ""
