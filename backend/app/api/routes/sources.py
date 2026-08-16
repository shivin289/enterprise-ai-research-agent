import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.research import ResearchSession
from app.models.source import Source
from app.models.user import User
from app.schemas.source import SourceOut

router = APIRouter(prefix="/api", tags=["sources"])


@router.get("/research/{research_id}/sources", response_model=list[SourceOut])
def list_sources(
    research_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.get(ResearchSession, research_id)
    if session is None or session.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Research session not found")
    return [SourceOut.model_validate(s) for s in session.sources]


@router.get("/sources/{source_id}", response_model=SourceOut)
def get_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    session = db.get(ResearchSession, source.research_session_id)
    if session is None or session.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceOut.model_validate(source)
