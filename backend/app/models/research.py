import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ResearchSession(Base):
    """One end-to-end research request from a user."""
    __tablename__ = "research_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    query: Mapped[str] = mapped_column(Text, nullable=False)
    depth: Mapped[str] = mapped_column(String(20), default="standard")  # quick | standard | deep
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending -> planning -> searching -> validating -> synthesizing -> completed | failed
    progress_step: Mapped[str] = mapped_column(String(50), default="queued")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="research_sessions")
    questions = relationship("ResearchQuestion", back_populates="session", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="session", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="session", uselist=False, cascade="all, delete-orphan")


class ResearchQuestion(Base):
    """A sub-question the planner decomposed the main query into."""
    __tablename__ = "research_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_sessions.id"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending|searched|validated

    session = relationship("ResearchSession", back_populates="questions")
    evidence_items = relationship("Evidence", back_populates="question", cascade="all, delete-orphan")


class Report(Base):
    """The final synthesized research report for a session."""
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id"), unique=True
    )
    summary: Mapped[str] = mapped_column(Text)
    report_content: Mapped[str] = mapped_column(Text)  # full structured markdown/JSON
    confidence_score: Mapped[float] = mapped_column(default=0.0)
    model_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ResearchSession", back_populates="report")
