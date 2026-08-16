import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ResearchCreateRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=2000)
    depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")


class ResearchCreateResponse(BaseModel):
    research_id: uuid.UUID
    status: str


class ResearchStatusResponse(BaseModel):
    research_id: uuid.UUID
    status: str
    progress_step: str
    error_message: str | None = None


class EvidenceOut(BaseModel):
    id: uuid.UUID
    claim: str
    supporting_excerpt: str
    relevance_score: float
    confidence_score: float
    is_conflicting: bool
    source_id: uuid.UUID

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    id: uuid.UUID
    question: str
    order_index: int
    status: str

    class Config:
        from_attributes = True


class ReportOut(BaseModel):
    summary: str
    report_content: str
    confidence_score: float
    model_name: str
    created_at: datetime

    class Config:
        from_attributes = True
        protected_namespaces = ()


class ResearchDetailResponse(BaseModel):
    research_id: uuid.UUID
    query: str
    status: str
    progress_step: str
    questions: list[QuestionOut] = []
    report: ReportOut | None = None


class ResearchListItem(BaseModel):
    research_id: uuid.UUID
    query: str
    status: str
    created_at: datetime
    confidence_score: float | None = None
