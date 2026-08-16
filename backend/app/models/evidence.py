import uuid

from sqlalchemy import ForeignKey, Text, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Evidence(Base):
    """A single extracted, source-grounded claim tied to a research question."""
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"))
    research_question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_questions.id"))
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_excerpt: Mapped[str] = mapped_column(Text)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_conflicting: Mapped[bool] = mapped_column(Boolean, default=False)
    conflict_group: Mapped[str | None] = mapped_column(Text, nullable=True)  # groups opposing claims

    source = relationship("Source", back_populates="evidence_items")
    question = relationship("ResearchQuestion", back_populates="evidence_items")
