"""
Core research endpoints. POST /research kicks off the pipeline
asynchronously (Celery in production; FastAPI BackgroundTasks as a
zero-infra fallback for local dev/demo) and returns immediately with a
session id, per the "Asynchronous research" requirement (#15).
"""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.research import ResearchSession
from app.models.user import User
from app.schemas.research import (
    ResearchCreateRequest,
    ResearchCreateResponse,
    ResearchStatusResponse,
    ResearchDetailResponse,
    ResearchListItem,
    QuestionOut,
    ReportOut,
)
from app.services.research_service import run_research_pipeline

router = APIRouter(prefix="/api/research", tags=["research"])


@router.get("", response_model=list[ResearchListItem])
def list_research(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(ResearchSession)
        .filter(ResearchSession.tenant_id == current_user.tenant_id)
        .order_by(ResearchSession.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        ResearchListItem(
            research_id=s.id,
            query=s.query,
            status=s.status,
            created_at=s.created_at,
            confidence_score=s.report.confidence_score if s.report else None,
        )
        for s in sessions
    ]


@router.post("", response_model=ResearchCreateResponse, status_code=202)
def create_research(
    payload: ResearchCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = ResearchSession(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        query=payload.query,
        depth=payload.depth,
        status="pending",
        progress_step="queued",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Production path: dispatch to Celery so the pipeline survives past
    # this request/worker process.
    #   from app.workers.research_worker import run_research_pipeline_task
    #   run_research_pipeline_task.delay(str(session.id))
    #
    # Zero-infra dev/demo path: run in a FastAPI background task using a
    # fresh DB session (background tasks outlive the request's session).
    def _run():
        from app.db.database import SessionLocal

        bg_db = SessionLocal()
        try:
            import asyncio

            asyncio.run(run_research_pipeline(bg_db, session.id))
        finally:
            bg_db.close()

    background_tasks.add_task(_run)

    return ResearchCreateResponse(research_id=session.id, status=session.status)


@router.get("/{research_id}/status", response_model=ResearchStatusResponse)
def get_status(
    research_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(db, research_id, current_user)
    return ResearchStatusResponse(
        research_id=session.id,
        status=session.status,
        progress_step=session.progress_step,
        error_message=session.error_message,
    )


@router.get("/{research_id}", response_model=ResearchDetailResponse)
def get_research(
    research_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(db, research_id, current_user)
    report_out = ReportOut.model_validate(session.report) if session.report else None
    questions_out = [QuestionOut.model_validate(q) for q in sorted(session.questions, key=lambda q: q.order_index)]

    return ResearchDetailResponse(
        research_id=session.id,
        query=session.query,
        status=session.status,
        progress_step=session.progress_step,
        questions=questions_out,
        report=report_out,
    )


@router.get("/{research_id}/report", response_model=ReportOut)
def get_report(
    research_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(db, research_id, current_user)
    if not session.report:
        raise HTTPException(status_code=404, detail="Report not ready yet")
    return ReportOut.model_validate(session.report)


def _get_owned_session(db: Session, research_id: uuid.UUID, current_user: User) -> ResearchSession:
    session = db.get(ResearchSession, research_id)
    if session is None or session.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session
